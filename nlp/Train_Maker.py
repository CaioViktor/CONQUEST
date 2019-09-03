from nlp.Instances_Retriever import Instances_Retriever
#This class is resposable to make the NER's train dataset
class Train_Maker():
	def __init__(QAIs,class_index,url_endpoint,graph_name=""):
		self.QAIs = QAIs
		self.instance_retriever = Instances_Retriever(url_endpoint,graph_name,number_samples)

	def make_train_dataset(self):
	#create whole train dataset
		train_dataset = []
		for qai in self.QAIs:
			qai_training_examples = self.make_qai_training_examples()
			train_dataset.append(qai_training_examples)
		return train_dataset

	def make_qai_training_examples(self,qai):
		#Create train examples for a given QAI
		for qp in qai.QPs:
			#For each QP, create examples using values for each one CV at a time
			for cv_id in qai.CVs:
				cv = qai.CVs[cv_id]
				for cv_owner_id in cv['owners']:
					cv_owner = cv['owners'][cv_owner_id]
					if 'classes' in cv_owner and len(cv_owner['classes']) > 0:
						#If was possible define class e property owners from CV
						for classs in cv_owner['classes']:
							#TODO: construct examples with instances
							self.instance_retriever.retriver(classs,cv_owner['uri'])

