import json
import re
import rdflib.plugins.sparql.processor as processor
import ontology.Schema as schema_processor

class QAI:
	def __init__(self):
		self.id = None
		self.description = ""
		self.QPs = []
		self.SP = ""
		self.RP = {'header':"",'body':"",'footer':""}

	def __init__(self,QAIj,QAI_id,propertyIndex):
		self.id = QAI_id
		self.description = QAIj['description']
		self.QPs = QAIj['QPs']
		self.SP = QAIj['SP']
		self.RP = QAIj['RP']
		self.CVs = {}
		self.RVs = {}
		self.IVs = {} #Inner Variables. Vars used only inside the query

		cvs_Set,rvs_Set = self.get_variables_SP(self.SP);

		# print("QAI:{}\n\tin:{}\n\tout:{}".format(self.id,vars_Set,result_Set))

		try:
			self.check_variables(cvs_Set,rvs_Set,self.QPs,self.RP)
		except:
			print("Error on loading QAI {}".format(self.id))
			raise 

		#TODO: computar CVs e RVs
		vars_set = schema_processor.parser_sparql(self.SP,propertyIndex)

		for var in cvs_Set:
			id_var = schema_processor.name_to_id_var(var)
			self.CVs[id_var] = vars_set[id_var]
			self.CVs[id_var]['name'] = var

		for var in rvs_Set:
			id_var = schema_processor.name_to_id_var(var)
			if id_var in vars_set:
				self.RVs[id_var] = vars_set[id_var]
			else:
				self.RVs[id_var] = schema_processor.new_var(var,schema_processor.LITERAL)

		for id_var in vars_set:
			if id_var not in self.CVs and id_var not in self.RVs:
				self.IVs[id_var] = vars_set[id_var]

		#TODO: Armazenar no DB? Melhor treinar modelo logo
		# print(str(self))

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
			


		