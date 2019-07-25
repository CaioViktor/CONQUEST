import json
import re

class QAI:
	def __init__(self):
		self.id = None
		self.description = ""
		self.QPs = []
		self.SP = ""
		self.RP = {'header':"",'body':"",'footer':""}

	def __init__(self,QAIj,QAI_id):
		self.id = QAI_id
		self.description = QAIj['description']
		self.QPs = QAIj['QPs']
		self.SP = QAIj['SP']
		self.RP = QAIj['RP']

		vars_Set,result_Set = self.get_variables_SP(self.SP);

		try:
			self.check_variables(vars_Set,result_Set,self.QPs,self.RP)
		except:
			print("Error on loading QAI {}".format(self.id))
			raise 

		# print("{}\n{}".format(vars_Set,result_Set))

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
		vars_Set = set()
		vars_Set.update(re.findall("\$\w+",SP))

		result_Set = set()
		result_list = (re.search("select .+ WHERE",SP,re.IGNORECASE)).group()
		result_Set.update(re.findall("\?\w+",result_list))
		

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
			


		