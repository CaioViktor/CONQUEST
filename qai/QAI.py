import json

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

		print(str(self))

	#Load QAI already computed
	@classmethod
	def load_from_persistence(cls,QAIj):
		return None

	def __str__(self):
		return str(self.to_Json())
		

	def to_Json(self):
		return json.dumps({"id":self.id,"description": self.description,"QPs":self.QPs,"SP":self.SP,"RP":self.RP},indent=4,ensure_ascii=False)

	#Get Context Variables from SPARQL query Pattern
	def get_CVs_SP(self):
		return None
		