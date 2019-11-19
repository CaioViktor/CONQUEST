from pathlib import Path
import ontology.Schema as sc
import qai.QAI_Manager as q
import pickle
import os
from nlp.NLP_Processor import NLP_Processor
from classifier.ML_Classifier import ML_Classifier
from nlp.NER_Trainer import NER_Trainer 
from datetime import datetime
from ontology.Query_Processor import Query_Processor
import pprint
import spacy
import nlp.Solr_Connection as solr_connection
from scipy.spatial.distance import cosine
import re
from rdflib import XSD

#States constants
from dialog.constants import *


#Configuration parameters
from config import *


def load_pickle(filePath):
	with open(filePath,"rb") as file:
		return pickle.load(file)

class Dialog_Manager():
	def __init__(self,users_collection):
		self.index_classes,self.index_properties = self.load_index() #self.index_properties = (rdf:Property,owl:ObjectProperty,owl:DatatypeProperty)
		self.qai_Manager = self.load_QAIs()
		self.nlp_processor = self.load_NLP_Processor()
		self.classifier = ML_Classifier.load_model()
		self.users_collection = users_collection
		self.query_processor = Query_Processor(sparql_endpoint,graph_name)


	def save_user_context(self,user):
		#Clear filds tha mongo don't suport
		context = user['context'].copy()
		context['original_cvec'] = []
		context['original_sv'] = []
		context['qai_id'] = int(context['qai_id'])
		
		self.users_collection.update_one({'id':user['id']},{'$set':{'context':context}})

	def clear_user_context(self,user):
		user['context'] = new_user_context()
		return user

	def close(self):
		self.nlp_processor.close()

	@staticmethod
	def load_index():		
		classes_index = None
		properties_index = None
		out_path = os.path.join("persistence/index","class.sav") 
		with open(out_path ,"rb") as file:
			classes_index = pickle.load(file)
			print("Classes index loaded from {}".format(out_path))

		out_path = os.path.join("persistence/index","property.sav") 
		with open(out_path ,"rb") as file:
			properties_index = pickle.load(file)
			print("Properties index loaded from {}".format(out_path))
		return classes_index,properties_index

	@staticmethod
	def load_QAIs():
		QAI_Manager = None
		out_path = os.path.join("persistence/qais","qai_manager.sav") 
		with open(out_path ,"rb") as file:
			QAI_Manager = pickle.load(file)
			print("QAI Manager loaded from {}".format(out_path))
		return QAI_Manager

	@staticmethod
	def load_NLP_Processor():
		labels_NER = load_pickle("persistence/temp/nlp/labels.sav")
		return NLP_Processor(labels_NER)



	def notify_message(self,text,user_id):
		user = self.users_collection.find_one({'id':user_id})
		if user['context']['state'] == WAITING_TO_START:
			return self.waiting_to_start(user,text)
		elif user['context']['state'] == WAITING_DESAMBIGUATION:
			return self.waiting_desambiguation(user,text)
		elif user['context']['state'] == WAITING_CV_VALUE:
			return self.waiting_CV_value(user,text)

	def waiting_to_start(self,user,text):
		user['context']['question'] = text

		entities, sentence = self.nlp_processor.parser(text)
		user['context']['entities_found'] = entities

		QV,SV_CVec = self.nlp_processor.transform_QV(sentence,entities)
		y = self.classifier.predict_proba(QV)[0]
		max_option = min(len(y),number_desambiguation_options)

		ordered_qais_index = list(y.argsort())
		ordered_qais_index.reverse()
		# print(entities,ordered_qais_index,y[ordered_qais_index[0]],y[ordered_qais_index[1]])
		ordered_qais_index = ordered_qais_index[:max_option]


		if y[ordered_qais_index[0]] >= min_confidance_classification:
			#Classification has a high confidance
			if max_option >= 2:
				diference_confidance = y[ordered_qais_index[0]] - y[ordered_qais_index[1]]
				if diference_confidance < min_diference_confidance:
					#Classification has a high confidance, but in two classes
					# return "estou em dúvida com {} em {}-{} e {}-{}".format(diference_confidance,ordered_qais_index[0],y[ordered_qais_index[0]],ordered_qais_index[1],y[ordered_qais_index[1]])
					return self.make_desambiguation_questions(user,y,ordered_qais_index,SV_CVec)
				else:
					#Classification has a high confidance only in a one class
					user['context']['qai_id'] = ordered_qais_index[0]
					user['context']['original_sv'] = SV_CVec[0]
					user['context']['original_cvec'] = SV_CVec[1]
					# return "Tenho {}% de certeza que essa pergunta é do tipo {}".format((y[ordered_qais_index[0]]*100),ordered_qais_index[0])
					return self.fetch_QAI(user)
			else:
				#There are only one option
				user['context']['qai_id'] = ordered_qais_index[0]
				user['context']['original_sv'] = SV_CVec[0]
				user['context']['original_cvec'] = SV_CVec[1]
				# return "Tenho {}% de certeza que essa pergunta é do tipo {}".format((y[ordered_qais_index[0]]*100),ordered_qais_index[0])
				return self.fetch_QAI(user)
		else: 
			#Classification has a low confidance
			return self.make_desambiguation_questions(user,y,ordered_qais_index,SV_CVec)

	def waiting_desambiguation(self,user,text):
		# print("\n\ndesambi: ",text,"\n",type(text),"\nlen:",len(user['context']['options']) ,"\n\n")
		# print(user)
		text = text.strip()
		if text.isdigit() and int(text) >= 0 and int(text) < len(user['context']['options']):
			#Set correct QAI
			option = int(text)
			user['context']['qai_id'] = user['context']['options'][option]['value']
			qai = self.qai_Manager.QAIs[user['context']['qai_id']] 

			#Process new QP
			QV,SV_CVec = self.nlp_processor.transform_QV(user['context']['question'],user['context']['entities_found'])
			user['context']['original_sv'] = SV_CVec[0]
			user['context']['original_cvec'] = SV_CVec[1]
			nearest_qp_index = self.get_nearest_QP_index(user['context']['original_sv'],qai)
			user = self.fill_CVs(user,qai,nearest_qp_index)
			new_qp = user['context']['question']
			for cv in user['context']['cvs_filled']:
				#replace CVs values with CVs marker in QP
				new_qp = new_qp.replace(str(cv['value']),str(cv['name']))
			#Update QAI
			self.update_QAI(user['context']['qai_id'],new_qp,user['context']['original_sv'])

			# print(user)
			# self.save_user_context(user)
			return self.fetch_QAI(user)
		elif text == "-1":
			#None sugestion is the correct question
			#TODO: guardar questão?
			user = self.clear_user_context(user)
			self.save_user_context(user)
			return {'status':1,'message':messages['unkwon_question']}
		else:
			return {'status':INVALID_OPTION,'message':[messages['invalid_option'],user['context']['question'],user['context']['options']]}

	def waiting_CV_value(self,user,text):
		waiting_cv = user['context']['cvs_to_fill'][0]
		user['context']['cvs_to_fill'].remove(waiting_cv)
		user['context']['cvs_filled'].append({'name':waiting_cv['name'],'value':text})

		if len(user['context']['cvs_to_fill']) == 0:
			#All CVs filled
			
			answer = self.run_query(user)
			user = self.clear_user_context(user)
			self.save_user_context(user)
			return answer
		else:
			#Still has CVs unfilled
			return self.ask_CV(user)

	def get_nearest_QP_index(self,original_sv,qai):
		nearest_qp_index = -1
		nearest_qp_value = 1
		idx = 0

		# print("QPs:\n",qai.QPs,"SVs:\n", len(qai.SVs))

		for sv in qai.SVs:
			if idx >= qai.canonicals_QPs:
				#From here on the QPs are given by the users
				break
			distance = cosine(original_sv , sv)
			if distance < nearest_qp_value:
				nearest_qp_value = distance
				nearest_qp_index = idx
			idx+=1
		# print("near",nearest_qp_index)
		return nearest_qp_index

	def fill_QP(self,user,qai,qp):
		cvs = re.findall("\$\w+",qp)
		entities = {}
		for entity in user['context']['entities_found']:
			#Make lists for CVs divided by types
			entity_type = self.nlp_processor.hash(entity[1])
			if entity_type in entities:
				entities[entity_type].apped(entity[0])
			else:
				entities[entity_type] = [entity[0]]
		for cv in cvs:
			#Filling CVs
			id_var = sc.name_to_id_var(cv)
			if len(qai.CVs[id_var]['owners_types']) > 0:
				#Get only the first type of a CV
				typee = qai.CVs[id_var]['owners_types'][0]
				typee_id = self.nlp_processor.hash(typee)
				if typee_id in entities and len(entities[typee_id]) > 0:
					#Found CV candidate
					cv_value = entities[typee_id][0]
					entities[typee_id].remove(cv_value)
					qp = qp.replace(cv,cv_value,1)
		return qp

	def fetch_QAI(self,user):
		qai = self.qai_Manager.QAIs[user['context']['qai_id']] 
		
		nearest_qp_index = self.get_nearest_QP_index(user['context']['original_sv'],qai)

		if nearest_qp_index > -1:
			user = self.fill_CVs(user,qai,nearest_qp_index)
			if len(user['context']['cvs_to_fill']) == 0:
				#All CVs filled
				return self.run_query(user)
			else:
				#Need to fill CV
				return self.ask_CV(user)

			# return "QP mais próxima é '{}' com distância de {}".format(qai.QPs[nearest_qp_index],nearest_qp_value)
			# return json.dumps(user)
		#TODO
		return {'status':1,'message':"Error in classify QP"}

	def ask_CV(self,user):
		cv_to_ask = user['context']['cvs_to_fill'][0]
		user['context']['state'] = WAITING_CV_VALUE
		self.save_user_context(user)
		if "@" in cv_to_ask['type'] or ('owner' in cv_to_ask and "@" in cv_to_ask['owner']):
			type_splitted = None
			if "@" in cv_to_ask['type']:
				type_splitted = cv_to_ask['type'].split("@")
			else:
				type_splitted = cv_to_ask['owner'].split("@")
			if len(type_splitted) == 2:
				#CV is a value to a know property
				cv_property_uri = type_splitted[0]
				cv_class_uri = type_splitted[1]
				property_index = sc.uri_to_hash(cv_property_uri)
				# print("\nProp:",cv_property_uri,"\nclass:",cv_class_uri,"hash: ",property_index)
				# print("\n\n",self.index_properties,"\n\n")
				cv_property = None
				cv_class = None
				if property_index in self.index_properties[0]:
					#It is a rdf:Property
					cv_property = self.index_properties[0][sc.uri_to_hash(cv_property_uri)]
				elif property_index in self.index_properties[1]:
					#It is a owl:ObjectProperty
					cv_property = self.index_properties[1][sc.uri_to_hash(cv_property_uri)]
				elif property_index in self.index_properties[2]:
					#It is a owl:DatatypeProperty
					cv_property = self.index_properties[2][sc.uri_to_hash(cv_property_uri)]
				if sc.uri_to_hash(cv_class_uri) in self.index_classes:
					cv_class = self.index_classes[sc.uri_to_hash(cv_class_uri)]
				ask_question = messages['ask_cv_question'] 
				if cv_class is not None:
					ask_question = ask_question.replace("$class_comment",self.get_comment(cv_class))
					ask_question = ask_question.replace("$class",self.get_label(cv_class))
				else:
					ask_question = ask_question.replace("$class_comment","")
					ask_question = ask_question.replace("$class",cv_class_uri)
				if cv_property is not None:
					ask_question = ask_question.replace("$property_comment",self.get_comment(cv_property))
					ask_question = ask_question.replace("$property",self.get_label(cv_property))
				else:
					ask_question = ask_question.replace("$property_comment","")
					ask_question = ask_question.replace("$property",cv_property_uri)
				return {'status':WAITING_CV_VALUE,'message':[ask_question]}

			else:
				#TODO
				return {'status':1,'message':["CV \n{}\nDon't have 2 args"]}
		else:
			#TODO
			return {'status':WAITING_CV_VALUE,'message':[messages['ask_cv_question_without_information'].replace("$cv_name",cv_to_ask['type'])]}

	def get_label(self,term):
		if 'labels' in term and len(term['labels']) > 0:
			return str(term['labels'][0].value)
		else:
			return ""

	def get_comment(self,term):
		if 'comments' in term and len(term['comments']) > 0:
			return str(term['comments'][0].value)
		else:
			return ""

	def fill_CVs(self,user,qai,nearest_qp_index):
		nearest_qp = qai.QPs[nearest_qp_index]
		cvs = re.findall("\$\w+",nearest_qp)

		entities = {}
		# print(user['context']['entities_found'])
		for entity in user['context']['entities_found']:
			#Make lists for CVs divided by types
			entity_type = self.nlp_processor.hash(entity[1])
			if entity_type in entities:
				entities[entity_type].apped(entity[0])
			else:
				entities[entity_type] = [entity[0]]

		user['context']['cvs_to_fill'] = []
		user['context']['cvs_filled'] = []
		for cv in cvs:
			#Filling CVs
			id_var = sc.name_to_id_var(cv)
			if len(qai.CVs[id_var]['owners_types']) > 0:
				#Get only the first type of a CV
				typee = qai.CVs[id_var]['owners_types'][0]
				if XSD.string not in qai.CVs[id_var]['class']:
					#CV use a primitive value
					typee = list(qai.CVs[id_var]['class'])[0]
				# print(typee)
				typee_id = self.nlp_processor.hash(typee)
				hash_integer = self.nlp_processor.hash(XSD.integer)
				if typee_id in entities and len(entities[typee_id]) > 0:
					#Found CV candidate
					print("Achou: ",entities[typee_id])
					cv_value = entities[typee_id][0]
					user['context']['cvs_filled'].append({'name':cv,'value':cv_value})
					entities[typee_id].remove(cv_value)
				elif typee == XSD.double and hash_integer in entities and len(entities[hash_integer]) > 0:
						print("Aqui 2:",entities[hash_integer])
						#CV xsd:double not foud, but found a xsd:integer
						cv_value = entities[hash_integer][0]
						user['context']['cvs_filled'].append({'name':cv,'value':cv_value})
						entities[hash_integer].remove(cv_value)
				else:
					#CV candidate not found
					cv_to_fill = {'name':cv,'type':typee}
					if XSD.string not in qai.CVs[id_var]['class']:
						cv_to_fill['owner'] = qai.CVs[id_var]['owners_types'][0]
					user['context']['cvs_to_fill'].append(cv_to_fill)
			else:
				#Not was possible to calculate property@class from CV
				# print("falta preencer: ",qai.CVs[id_var]['name'])
				cv_to_fill = {'name':cv,'type':qai.CVs[id_var]['name']}
				user['context']['cvs_to_fill'].append(cv_to_fill)

		#TODO: preencher CVs sobre as quais não se tinha certeza com os valores que sobraram?
		return user

	def run_query(self,user):
		#Build SPARQL query
		qai = self.qai_Manager.QAIs[user['context']['qai_id']]
		answer = {'status':0,'message':self.query_processor.run(qai,user['context']['cvs_filled'])}
		user = self.clear_user_context(user)
		self.save_user_context(user)
		return answer
		
	def make_desambiguation_questions(self,user,y,ordered_qais_index,SV_CVec):
		user['context']['options'] = []
		for qai_id in ordered_qais_index:
			option = {}
			qai = self.qai_Manager.QAIs[qai_id] 
			option['confidance'] = float(y[qai_id])
			option['value'] = int(qai_id)
			qp = qai.QPs[self.get_nearest_QP_index(SV_CVec[0],qai)]
			option['text'] = self.fill_QP(user,qai,qp)
			user['context']['options'].append(option)
		# print(user)
		user['context']['state'] = WAITING_DESAMBIGUATION
		self.save_user_context(user)
		# return json.dumps(user['context']['options'], ensure_ascii=False)
		return {'status':WAITING_DESAMBIGUATION,'message':[user['context']['options']]}

	def update_QAI(self,qai_index,new_QP,new_SV):
		self.qai_Manager.update_QAI(qai_index,new_QP,new_SV)
		out_path = os.path.join("persistence/qais","qai_manager.sav") 
		with open(out_path ,"wb") as file:
			pickle.dump(self.qai_Manager,file)
			print("QAI Manager updated to {}".format(out_path))

	def list_QAIs(self):
		qais = []
		for qai in self.qai_Manager.QAIs:
			qais.append((qai.id,qai.QPs[0],qai.description))
		return {'status':0,'message':qais}

	def select_QAI(self,user,qai_id):
		#Set correct QAI
		user['context']['qai_id'] = int(qai_id)
		qai = self.qai_Manager.QAIs[user['context']['qai_id']] 
		user['context']['question'] = qai.QPs[0]
		user['context']['entities_found'] = []

		#Process new QP
		QV,SV_CVec = self.nlp_processor.transform_QV(user['context']['question'],user['context']['entities_found'])
		user['context']['original_sv'] = SV_CVec[0]
		user['context']['original_cvec'] = SV_CVec[1]
		nearest_qp_index = 0
		user = self.fill_CVs(user,qai,nearest_qp_index)

		# print(user)
		# self.save_user_context(user)
		return self.fetch_QAI(user)