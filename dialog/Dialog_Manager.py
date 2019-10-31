from pathlib import Path
import ontology.Schema as sc
import qai.QAI_Manager as q
import pickle
import os
from nlp.NLP_Processor import NLP_Processor
from classifier.ML_Classifier import ML_Classifier
from nlp.NER_Trainer import NER_Trainer 
from datetime import datetime
import pprint
import spacy
import nlp.Solr_Connection as solr_connection

#States constants
from dialog.constants import *

#Configuration parameters
from config import *


def load_pickle(filePath):
	with open(filePath,"rb") as file:
		return pickle.load(file)

class Dialog_Manager():
	def __init__(self,users_collection):
		self.index_classes,index_properties = self.load_index()
		self.qai_Manager = self.load_QAIs()
		self.nlp_processor = self.load_NLP_Processor()
		self.classifier = ML_Classifier.load_model()
		self.users_collection = users_collection



	def close(self):
		self.nlp_processor.close()

	@staticmethod
	def load_index():		
		classes_index = None
		properties_index = None
		out_path = os.path.join("persistence/index","class.sav") 
		with open(out_path ,"rb") as file:
			classes_index = pickle.load(file)
			print("Classes index loaded from {}".format(out_path))

		out_path = os.path.join("persistence/index","property.sav") 
		with open(out_path ,"rb") as file:
			properties_index = pickle.load(file)
			print("Properties index loaded from {}".format(out_path))
		return classes_index,properties_index

	@staticmethod
	def load_QAIs():
		QAI_Manager = None
		out_path = os.path.join("persistence/qais","qai_manager.sav") 
		with open(out_path ,"rb") as file:
			QAI_Manager = pickle.load(file)
			print("QAI Manager loaded from {}".format(out_path))
		return QAI_Manager

	@staticmethod
	def load_NLP_Processor():
		labels_NER = load_pickle("persistence/temp/nlp/labels.sav")
		return NLP_Processor(labels_NER)



	def notify_message(self,text,user_id):
		user = self.users_collection.find_one({'id':user_id})
		if user['context']['state'] == WAITING_TO_START:
			return self.waiting_to_start(user,text)
		elif ser['context']['state'] == WAITING_TO_START:
			return

	def waiting_to_start(self,user,text):
		entities, sentence = self.nlp_processor.parser(text)
		QV = self.nlp_processor.transform_QV(sentence,entities)
		y = self.classifier.predict_proba(QV)[0]
		max_option = min(len(y),3)

		ordered_qais_index = list(y.argsort())
		ordered_qais_index.reverse()
		ordered_qais_index = ordered_qais_index[:max_option]



		if y[ordered_qais_index[0]] >= min_confidance_classification:
			#Classification has a high confidance
			if max_option >= 2:
				diference_confidance = y[ordered_qais_index[0]] - y[ordered_qais_index[1]]
				if diference_confidance < min_diference_confidance:
					#Classification has a high confidance, but in two classes
					return "estou em dúvida com {} em {}-{} e {}-{}".format(diference_confidance,ordered_qais_index[0],y[ordered_qais_index[0]],ordered_qais_index[1],y[ordered_qais_index[1]])
				else:
					#Classification has a high confidance only in a one class
					return "Tenho {}% de certeza que essa pergunta é do tipo {}".format((y[ordered_qais_index[0]]*100),ordered_qais_index[0])
			else:
				#There are only one option
				return "Só tenho uma opção"
		else: 
			#Classification has a low confidance
			return "não tenho certeza"
		return list(y)
