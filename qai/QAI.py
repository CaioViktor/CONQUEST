class QAI:
	def __init__(self,QPs,SP,RP):
		self.QPs = QPs
		self.SP = SP
		self.RP = RP


	#Get Context Variables from SPARQL query Pattern
	def get_CVs_SP(self):
		