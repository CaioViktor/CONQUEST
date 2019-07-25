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

	def __init__(self,file,path = "configurations/"):
		file_path = os.path.join(path,file)
		
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

			count_id = 1
			for qaiD in qais['QAIs']:
				qai = QAI.QAI(qaiD,count_id)
				self.QAIs.append(qai)
				count_id+=1

			print(str(self))


	def __str__(self):
		return str(self.to_Json())
		

	def to_Json(self):
		return json.dumps({"description": self.description,"update_data": self.update_data,"author": self.author,"created_date": self.created_date,"QAIs": [QAI.__dict__ for QAI in self.QAIs]},indent=4,ensure_ascii=False)


	@classmethod
	def load_from_persistence(cls,name):
		return cls()