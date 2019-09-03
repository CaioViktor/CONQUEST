from abc import ABC, abstractmethod
from nlp.Train_Maker import Train_Maker

#Template method pattern design

#Train Named Entity Recognition to recognize class properties values in senteces. It's values will be used in Context Variables
class NER_Trainer_Template(ABC):
	def __init__(self,QAIs,class_index,url_endpoint,graph_name="",number_iterations=100,number_samples=0):
		self.class_index = class_index
		self.number_iterations = number_iterations
		self.train_maker = Train_Maker(QAIs,class_index,url_endpoint,graph_name)

		


	

