from nlp.NER_Trainer import NER_Trainer_Template
import spacy
from spacy.util import minibatch, compounding
#Train Named Entity Recognition to recognize class properties values in senteces. It's values will be used in Context Variables
#Class to model in Brazilian portuguese
class NER_Trainer(NER_Trainer_Template):
	def __init__(self,class_index,url_endpoint,graph_name="",number_iterations=100,number_samples=0):
		self.model = spacy.load('pt_core_news_sm')
		super().__init__(class_index,url_endpoint,graph_name,number_iterations,number_samples)

	def test(self):
		super().test()
		print("Sou PT-BR")