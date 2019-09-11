from nlp.NER_Trainer import NER_Trainer_Template
import spacy
from spacy.util import minibatch, compounding
from datetime import datetime
#Train Named Entity Recognition to recognize class properties values in senteces. It's values will be used in Context Variables
#Class to model in Brazilian portuguese
class NER_Trainer(NER_Trainer_Template):
	def __init__(self,QAIs,class_index,url_endpoint,graph_name="",number_iterations=100,number_samples=0):
		self.model = spacy.load('pt_core_news_sm')
		self.name_model = "NER_PT_{}".format(str(datetime.now()).replace(" ","_"))
		super().__init__(QAIs=QAIs,class_index=class_index,url_endpoint=url_endpoint,graph_name=graph_name,number_iterations=number_iterations,number_samples=number_samples)

	def load_train_dataset(self,loadPath):
		self.name_model = "NER_PT_{}".format(str(datetime.now()).replace(" ","_"))
		super().load_train_dataset(loadPath)