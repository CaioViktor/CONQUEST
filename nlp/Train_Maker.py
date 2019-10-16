from nlp.Instances_Retriever import Instances_Retriever
from rdflib import XSD
from rdflib.namespace import Namespace
#This class is resposable to make the NER's train dataset
class Train_Maker():
	def __init__(self,QAIs,class_index,url_endpoint,graph_name="",number_samples=0):
		self.QAIs = QAIs
		self.labels = []
		self.instance_retriever = Instances_Retriever(url_endpoint,graph_name,number_samples)

	def make_train_dataset(self):
		print("Creating train dataset")
	#create whole train dataset
		train_dataset = []
		for qai in self.QAIs:
			qai_training_examples = self.make_qai_training_examples(qai)
			train_dataset+=qai_training_examples
		print("Created train dataset")
		return self.filter_dataset(train_dataset)

	def make_qai_training_examples(self,qai):
		#Create train examples for a given QAI
		train_data = []
		for qp in qai.QPs:
			#For each QP, create examples using values for each one CV at a time
			for cv_id in qai.CVs:
				cv = qai.CVs[cv_id]
				if XSD.string in cv['class']:
					#Train NER only for strings
					for cv_owner_id in cv['owners']:
						cv_owner = cv['owners'][cv_owner_id]
						if 'classes' in cv_owner and len(cv_owner['classes']) > 0:
							#If was possible define class e property owners from CV
							for classs in cv_owner['classes']:
								instances = self.instance_retriever.retriver(classs,cv_owner['uri'])
								examples = []
								for instance in instances:
									example = qp.replace(cv['name'],instance)
									label = self.create_label(classs,cv_owner['uri'])
									if label not in self.labels:
										self.labels.append(label)
									annotation = self.create_annotation(example,instance,label)
									train_data.append(annotation)


		return train_data

	def filter_dataset(self,train_dataset):
		return train_dataset


##Utility functions
	@staticmethod
	def create_label(classs,propertyy):
		return propertyy.strip()+"@"+classs.strip()
	@staticmethod
	def create_annotation(string,entity,label):
		#Create Spacy annotation structure
		#Fow now this function is annotating just one entity to example
		string = string.strip()
		entity = entity.strip()
		entities_array = []
		if entity in string:
			initial_index = string.index(entity)
			final_index = initial_index + len(entity)
			entities_array.append((initial_index,final_index,label))
		return (string,{'entities':entities_array})

