from nlp.Instances_Retriever import Instances_Retriever
from rdflib import XSD
from rdflib.namespace import Namespace
from functools import reduce
#This class is resposable to make the NER's train dataset
class Train_Maker():
	def __init__(self,QAIs,class_index,url_endpoint,graph_name=""):
		self.QAIs = QAIs
		self.labels = []
		self.instance_retriever = Instances_Retriever(url_endpoint,graph_name)

	def make_train_dataset(self):
		print("Creating train dataset")
		#create whole train dataset
		train_dataset = []
		for qai in self.QAIs:
			qai_training_examples = self.make_qai_training_examples(qai)
			train_dataset+=qai_training_examples
		print("Created train dataset")
		return train_dataset

	def make_qai_training_examples(self,qai):
		#Create train examples for a given QAI
		train_data = []
		
		for cv_id in qai.CVs:
			cv = qai.CVs[cv_id]
			if XSD.string in cv['class']:
				#Train NER only for strings
				for cv_owner_id in cv['owners']:
					cv_owner = cv['owners'][cv_owner_id]
					if 'classes' in cv_owner and len(cv_owner['classes']) > 0:
						#If was possible define class e property owners from CV
						for classs in cv_owner['classes']:
							#Get label P@C. Where P = Property and C = Class.
							label = self.create_label(classs,cv_owner['uri'])
							if label not in self.labels:
								#New label found
								self.labels.append(label)

							#Get instances to property
							instances = self.instance_retriever.retriver(classs,cv_owner['uri'])
							document = {"id":label,"values":instances}
							train_data.append(document)
		return train_data


##Utility functions
	@staticmethod
	def create_label(classs,propertyy):
		return propertyy.strip()+"@"+classs.strip()