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

#States constants
from dialog.constants import *


#Configuration parameters
from config import *


def load_pickle(filePath):
	with open(filePath,"rb") as file:
		return pickle.load(file)

class Dialog_Manager():
	def __init__(self,users_collection):
		self.index_classes,index_properties = self.load_index()
		self.qai_Manager = self.load_QAIs()
		self.nlp_processor = self.load_NLP_Processor()
		self.classifier = ML_Classifier.load_model()
		self.users_collection = users_collection
		self.query_processor = Query_Processor(sparql_endpoint,graph_name)


	def save_user_context(self,user):
		self.users_collection.update_one({'id':user['id']},{'$set':{'context':user['context']}})

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
				return {'status':1,'message':"Só tenho uma opção"}
		else: 
			#Classification has a low confidance
			return self.make_desambiguation_questions(user,y,ordered_qais_index,SV_CVec)

	def waiting_desambiguation(self,user,text):
		text = text.strip()
		if text.isdigit() and int(text) >= 0 and int(text) < len(user['context']['options']):
			option = int(text)
			#TODO: Aprender questão e continuar o fluxo
			return {'status':0,'message':"Você selecionou a opção {}".format(user['context']['options'][option]['text'])}
		elif text == "-1":
			#None sugestion is the correct question
			#TODO: guardar questão?
			return {'status':0,'message':messages['unkwon_question']}
		else:
			return {'status':INVALID_OPTION,'message':messages['invalid_option']}


	def get_nearest_QP_index(self,original_sv,qai):
		nearest_qp_index = -1
		nearest_qp_value = 1
		idx = 0

		for sv in qai.SVs:
			distance = cosine(original_sv , sv)
			if distance < nearest_qp_value:
				nearest_qp_value = distance
				nearest_qp_index = idx
			idx+=1
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
				if len(entities[typee_id]) > 0:
					#Found CV candidate
					cv_value = entities[typee_id][0]
					entities[typee_id].remove(cv_value)
					qp = qp.replace(cv,cv_value,1)
			return qp

	def fetch_QAI(self,user):
		qai = self.qai_Manager.QAIs[user['context']['qai_id']] 
		
		nearest_qp_index = self.get_nearest_QP_index(user['context']['original_sv'],qai)

		if nearest_qp_index > -1:
			nearest_qp = qai.QPs[nearest_qp_index]
			cvs = re.findall("\$\w+",nearest_qp)

			entities = {}
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
					typee_id = self.nlp_processor.hash(typee)
					if typee_id not in entities:
						#CV candidate not found
						user['context']['cvs_to_fill'].append({'name':cv,'type':typee})
					elif len(entities[typee_id]) > 0:
						#Found CV candidate
						cv_value = entities[typee_id][0]
						user['context']['cvs_filled'].append({'name':cv,'value':cv_value})
						entities[typee_id].remove(cv_value)
			# print(user)
			if len(user['context']['cvs_to_fill']) == 0:
				#All CVs filled
				return self.run_query(user)
			else:
				#Need to fill CV
				return {'status':1,'message':"Faltou as CVs:\n{}".format(user['context']['cvs_filled'])}

			# return "QP mais próxima é '{}' com distância de {}".format(qai.QPs[nearest_qp_index],nearest_qp_value)
			# return json.dumps(user)
		return {'status':1,'message':"Error in classify QP"}

	def run_query(self,user):
		#Build SPARQL query
		qai = self.qai_Manager.QAIs[user['context']['qai_id']]
		return {'status':0,'message':self.query_processor.run(qai,user['context']['cvs_filled'])}
		
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
		return {'status':WAITING_DESAMBIGUATION,'message':user['context']['options']}

