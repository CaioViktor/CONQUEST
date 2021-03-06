import os
import json
import datetime
import qai.QAI as QAI


class QAI_Manager():
	def __init__(self):
		self.description = ""
		self.update_data = ""
		self.author = ""
		self.created_date = ""
		self.QAIs = []

	def __init__(self,file_path,propertyIndex):
		
		with open(file_path,"r", encoding="utf-8") as json_file:
			qais = json.load(json_file)
			self.description = qais['description']
			self.author = qais['author']

			if((not 'update_data' in qais) or (qais['update_data'] == "")):
				self.update_data = str(datetime.datetime.now())
			else:
				self.update_data = qais['update_data']

			if((not 'created_date' in qais) or (qais['created_date'] == "")):
				self.created_date = str(datetime.datetime.now())
			else:
				self.created_date = qais['created_date']

			self.QAIs = []

			count_id = 0
			for qaiD in qais['QAIs']:
				try:
					qai = QAI.QAI(qaiD,count_id,propertyIndex)
					self.QAIs.append(qai)
				except:
					print('Error on loading QAI Manager on file: "{}"'.format(file_path))
					raise
				count_id+=1

			# print(str(self))

	def compute_SVs(self,nlp_processor):
		for qai in self.QAIs:
			qai.compute_SVs(nlp_processor)

	def __str__(self):
		return str(self.to_Json())
		

	def to_Json(self):
		return json.dumps({"description": self.description,"update_data": self.update_data,"author": self.author,"created_date": self.created_date,"QAIs": [QAI.__dict__ for QAI in self.QAIs]},indent=4,ensure_ascii=False)

	def update_QAI(self,qai_index,new_QP,new_SV):
		# print("QPs:\n",self.QAIs[qai_index].QPs,"SVs:\n",self.QAIs[qai_index].SVs)
		if qai_index >=0 and qai_index < len(self.QAIs):
			self.QAIs[qai_index].QPs.append(new_QP)
			self.QAIs[qai_index].SVs.append(new_SV)
			# print("QPs:\n",self.QAIs[qai_index].QPs,"SVs:\n",self.QAIs[qai_index].SVs)
