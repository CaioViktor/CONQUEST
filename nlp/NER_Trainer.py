import pysolr
import json 
import nlp.Solr_Connection as solr_connection
from nlp.Train_Maker import Train_Maker
from pathlib import Path
import os
import pickle as pic
from datetime import datetime



class NER_Trainer():
	def __init__(self,QAIs,class_index,url_endpoint,graph_name="",solr_host="http://localhost",solr_port="8983",solr_core="conquest"):
		self.class_index = class_index
		self.train_maker = Train_Maker(QAIs,class_index,url_endpoint,graph_name)
		#self.model NLP: Model instantiated in children class
		#self.name_model: name NER Model instantiated in children class
		self.train_dataset = None
		self.solr_url = "{}:{}/solr/{}/".format(solr_host,solr_port,solr_core)
		self.solr_port = solr_port
		self.solr_core = solr_core
		self.solr_host = solr_host




	def make_train_dataset(self,savePath=""):
		dataset = self.train_maker.make_train_dataset()
		if savePath != "":
			saveDir = Path(savePath)
			if not saveDir.exists():
				saveDir.mkdir(parents=True)
			
			pathOut = os.path.join(savePath,"train_dataset.json")
			with open(pathOut,"w") as dump_file:
				json.dump(dataset,dump_file,ensure_ascii=False)
				

			pathOut_labels = os.path.join(savePath,"labels.sav")
			with open(pathOut_labels,"wb") as pickle_file:
				pic.dump(self.get_labels(),pickle_file)
		self.train_dataset = dataset
		return self

	def load_train_dataset(self,loadPath):
		pathOut = os.path.join(loadPath,"train_dataset.json")
		with open(pathOut,"r") as dump_file:
			self.train_dataset = json.load(dump_file)

		pathOut_labels = os.path.join(loadPath,"labels.sav")
		with open(pathOut_labels,"rb") as pickle_file:
			self.train_maker.labels = pic.load(pickle_file)

		print("Dataset loaded from {}".format(loadPath))
		return self

	def train_NER(self,loadPath="",outputPath="",solr_memory="1g"):
		#Load index of labels (CV types, P@C) and instances (values of properties)
		
		print("Starting training...")
		satart_time = datetime.now()

		if loadPath != "":
			self.load_train_dataset(loadPath)
			print("Loaded dataset from ",loadPath)
		if self.train_dataset == None:
			self.make_train_dataset()


		solr_connection.startup(self.solr_port,solr_memory)

		solr = pysolr.Solr(self.solr_url, timeout=10)
		print("Creating index NER...")
		#Removing old index 
		solr.delete(q="*:*",commit=True)
		#creating new index
		solr.add(self.train_dataset,commit=True)
		solr_connection.stop()

		finish_time = datetime.now()
		print("Training NER done! Elapsed time: {}".format(str(finish_time - satart_time)))
		

	def get_labels(self):
		return self.train_maker.labels
