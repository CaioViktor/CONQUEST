import json
import re
import rdflib.plugins.sparql.processor as processor
import ontology.Schema as schema_processor
from rdflib import URIRef
from rdflib import XSD
from nlp.Train_Maker import Train_Maker

class QAI:
	def __init__(self):
		self.id = None
		self.description = ""
		self.QPs = []
		self.SP = ""
		self.canonicals_QPs = 0
		self.RP = {'header':"",'body':"",'footer':""}

	def __init__(self,QAIj,QAI_id,propertyIndex):
		self.id = QAI_id
		self.description = QAIj['description']
		self.SP = QAIj['SP']
		self.RP = QAIj['RP']
		self.QPs= QAIj['QPs']

		#Add id of QAI to variables to ensure that it are not used in others qais
		self.SP = self.mark_qaiId_Vars(self.SP)
		self.QPs = [self.mark_qaiId_Vars(qp) for qp in self.QPs]
		self.RP['header']= self.mark_qaiId_Vars(self.RP['header'])
		self.RP['body'] = self.mark_qaiId_Vars(self.RP['body'])
		self.RP['footer'] = self.mark_qaiId_Vars(self.RP['footer'])
		
		self.canonicals_QPs = len(self.QPs) #Number of QP given by the developer (canonicals)
		self.CVs = {} #Context Variables, input variables
		self.RVs = {} #Result Variables
		self.IVs = {} #Inner Variables. Vars used only inside the query
		self.SVs = [] #Sentence Vector of QPs

		cvs_Set,rvs_Set = self.get_variables_SP(self.SP)


		# print("QAI:{}\n\tin:{}\n\tout:{}".format(self.id,vars_Set,result_Set))

		try:
			self.check_variables(cvs_Set,rvs_Set,self.QPs,self.RP)
		except:
			print("Error on loading QAI {}".format(self.id))
			raise 
		vars_set = schema_processor.parser_sparql(self.SP,propertyIndex)
		# print(vars_set)

		for var in cvs_Set:
			#Getting CV's Owners (classes and properties)
			id_var = schema_processor.name_to_id_var(var)
			# print(var)
			# print(id_var)
			self.CVs[id_var] = vars_set[id_var]
			self.CVs[id_var]['name'] = var
			self.CVs[id_var]['owners'] = {}
			self.CVs[id_var]['owners_types'] = set()
			for s,p,o in self.CVs[id_var]['context']:
				id_s = schema_processor.name_to_id_var(s)
				id_o = schema_processor.name_to_id_var(o)
				if self.is_Binary_Comparator(p):
					#CV is used to compare inner variable's value
					other = None
					if id_var == id_o:
						#current var is triple's object
						other = vars_set[id_s]
					elif id_var == id_s:
						#current var is triple's subject
						other = vars_set[id_o]
					if other != None:
						for (class_owner,property_owner,aux) in other['context']:
							self.get_Property_Owner(vars_set,class_owner,property_owner,id_var)
				elif id_s in vars_set :
					#CV is used inside (not as a comparator in filter) triples query
					if id_var == id_o:
						#current var is triple's object
						self.get_Property_Owner(vars_set,s,p,id_var)
			#Record owners_types
			# if XSD.string not in self.CVs[id_var]['class']:
			# 	#CV is from a primitive type (integer,decimal or datetime)
			# 	self.CVs[id_var]['owners_types'] = self.CVs[id_var]['owners_types'].union(set(self.CVs[id_var]['owners_types']))
			# else:
			#CV is Property@Class
			for owner_id in self.CVs[id_var]['owners']:
				#TODO: Check why in some cases owners_types has a path
				owner = self.CVs[id_var]['owners'][owner_id]
				propertyy = self.CVs[id_var]['owners'][owner_id]['uri']
				for classs in self.CVs[id_var]['owners'][owner_id]['classes']:
					typee = Train_Maker.create_label(classs,propertyy)
					self.CVs[id_var]['owners_types'].add(typee)
			self.CVs[id_var]['owners_types'] = list(self.CVs[id_var]['owners_types'])
			# print("Var {} types:\n{}".format(var,self.CVs[id_var]['owners_types']))
		for var in rvs_Set:
			id_var = schema_processor.name_to_id_var(var)
			if id_var in vars_set:
				self.RVs[id_var] = vars_set[id_var]
				if self.RVs[id_var]['name'][0] != "?":
					self.RVs[id_var]['name'] = "?"+self.RVs[id_var]['name']
			else:
				self.RVs[id_var] = schema_processor.new_var(var,schema_processor.LITERAL)
				if self.RVs[id_var]['name'][0] != "?":
					self.RVs[id_var]['name'] = "?"+self.RVs[id_var]['name']
		for id_var in vars_set:
			if id_var not in self.CVs and id_var not in self.RVs:
				self.IVs[id_var] = vars_set[id_var]

	@staticmethod
	def is_Binary_Comparator(op):
		return op in ['=','<','>','>=','<=','!=','Builtin_CONTAINS','Builtin_STRAFTER','Builtin_STRBEFORE','Builtin_STRENDS','Builtin_STRSTARTS','Builtin_REGEX','Builtin_sameTerm']

	def mark_qaiId_Vars(self,text):
		cvs = re.findall("\$\w+",text)
		for cv in cvs:
			cv_name = cv.replace("$","")
			text = text.replace(cv,"$qai_"+str(self.id)+"_"+cv_name)
		
		varss = re.findall("\?\w+",text)
		for var in varss:
			var_name = var.replace("?","")
			text = text.replace(var,"?qai_"+str(self.id)+"_"+var_name)
		return text

	def get_Property_Owner(self,vars_set,class_owner,property_owner,id_var):
		if isinstance(property_owner,URIRef):
			id_class_owner = schema_processor.name_to_id_var(class_owner)
			classes = set()
			for classs in vars_set[id_class_owner]['class']:
				if isinstance(classs,URIRef):
					classes.add(classs)
			id_property = schema_processor.uri_to_hash(property_owner)
			if id_property not in self.CVs[id_var]['owners']:
				#First time seeing CV's owner
				self.CVs[id_var]['owners'][id_property]	={'uri':property_owner,'classes':classes}	
			else:
				#Adding a new CV's owner
				self.CVs[id_var]['owners'][id_property]['classes'].update(classes) 
			# print(var," é de ",classes,property_owner)

	#Load QAI already computed
	@classmethod
	def load_from_persistence(cls,QAIj):
		return None

	def __str__(self):
		return str(self.to_Json())
		

	def to_Json(self):
		return json.dumps({"id":self.id,"description": self.description,"QPs":self.QPs,"SP":self.SP,"RP":self.RP},indent=4,ensure_ascii=False)

	#Compute Context Variables from SPARQL query Pattern
	@staticmethod
	def compute_CVs_SP(SP):
		CVs = {}


		return CVs

	@staticmethod
	def get_variables_SP(SP):
		#Get CVs
		vars_Set = set()
		vars_Set.update(re.findall("\$\w+",SP))

		#Get RVs
		result_Set = set()
		query_object = processor.prepareQuery(SP)
		for var in query_object.algebra['PV']:
			result_Set.add(var.n3())

		

		return vars_Set,result_Set


	@staticmethod
	def check_variables(vars_Set,result_Set,QPs,RP):
		#check errors in Questions Templates
		for QP in QPs:
			vars_Set_QP = set()
			vars_Set_QP.update(re.findall("\$\w+",QP))
			if not vars_Set_QP.issubset(vars_Set):
				print('Error in QP: "{}". Variables: {} not in SP set: {}'.format(QP,str(vars_Set_QP.difference(vars_Set)),str(vars_Set)))
				raise

		#check errors in Response Template
		#header CVs
		vars_Set_RP_H = set()
		vars_Set_RP_H.update(re.findall("\$\w+",RP['header']))
		if not vars_Set_RP_H.issubset(vars_Set):
			print('Error in RP header: "{}". Variables: {} not in SP set: {}'.format(RP['header'],str(vars_Set_RP_H.difference(vars_Set)),str(vars_Set)))
			raise

		#body CVs
		vars_Set_RP_B = set()
		vars_Set_RP_B.update(re.findall("\$\w+",RP['body']))
		if not vars_Set_RP_B.issubset(vars_Set):
			print('Error in RP body: "{}". Variables: {} not in SP set: {}'.format(RP['body'],str(vars_Set_RP_B.difference(vars_Set)),str(vars_Set)))
			raise

		#body RVs
		vars_Set_RP_B = set()
		vars_Set_RP_B.update(re.findall("\?\w+",RP['body']))
		if not vars_Set_RP_B.issubset(result_Set):
			print('Error in RP body: "{}". Response Variables: {} not in SP set: {}'.format(RP['body'],str(vars_Set_RP_B.difference(result_Set)),str(result_Set)))
			raise


		#footer CVs
		vars_Set_RP_F = set()
		vars_Set_RP_F.update(re.findall("\$\w+",RP['footer']))
		if not vars_Set_RP_F.issubset(vars_Set):
			print('Error in RP footer: "{}". Variables: {} not in SP set: {}'.format(RP['footer'],str(vars_Set_RP_F.difference(vars_Set)),str(vars_Set)))
			raise
	def compute_SVs(self,nlp_processor):
		self.SVs = []
		for qp in self.QPs:	
			sentence = qp
			for cv_id in self.CVs:
				cv = self.CVs[cv_id]
				sentence = sentence.replace(cv['name'],"oovmarker")
			sentence = sentence.lower()
			SV = nlp_processor.sentence_vector(sentence)
			self.SVs.append(SV)	