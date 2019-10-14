from abc import ABC, abstractmethod
from nlp.Train_Maker import Train_Maker
import pickle as pic
import os
import spacy
from spacy.util import minibatch, compounding
from pathlib import Path
import random
from datetime import datetime

#os.environ["OMP_NUM_THREADS"] = "1"

#Template method pattern design

#Train Named Entity Recognition to recognize class properties values in senteces. It's values will be used in Context Variables
class NER_Trainer_Template(ABC):
	def __init__(self,QAIs,class_index,url_endpoint,graph_name="",number_iterations=100,number_samples_train=0,number_samples_examples=0):
		self.class_index = class_index
		self.number_iterations = number_iterations
		self.number_samples = number_samples_train
		self.train_maker = Train_Maker(QAIs,class_index,url_endpoint,graph_name,number_samples_examples)
		#self.model NLP: Model instantiated in children class
		#self.name_model: name NER Model instantiated in children class
		self.train_dataset = None

	def make_train_dataset(self,savePath=""):
		dataset = self.train_maker.make_train_dataset()
		if savePath != "":
			saveDir = Path(savePath)
			if not saveDir.exists():
				saveDir.mkdir(parents=True)
			pathOut = os.path.join(savePath,"train_dataset.sav")
			with open(pathOut,"wb") as pickle_file:
				pic.dump(dataset,pickle_file)
			pathOut_labels = os.path.join(savePath,"labels.sav")
			with open(pathOut_labels,"wb") as pickle_file:
				pic.dump(self.get_labels(),pickle_file)
		self.train_dataset = dataset
		return self


	def load_train_dataset(self,loadPath):
		pathOut = os.path.join(loadPath,"train_dataset.sav")
		with open(pathOut,"rb") as pickle_file:
			self.train_dataset = pic.load(pickle_file)

		pathOut_labels = os.path.join(loadPath,"labels.sav")
		with open(pathOut_labels,"rb") as pickle_file:
			self.train_maker.labels = pic.load(pickle_file)
		print("Dataset loaded from {}".format(loadPath))
		return self


	def train_NER(self,loadPath="",outputPath=""):
		print("Starting training...")
		satart_time = datetime.now()
		random.seed(0)
		if loadPath != "":
			self.load_train_dataset(loadPath)
			print("Loaded dataset from ",loadPath)
		if self.train_dataset == None:
			self.make_train_dataset()
		

		# Add entity recognizer to model if it's not in the pipeline
		# nlp.create_pipe works for built-ins that are registered with spaCy
		if "ner" not in self.model.pipe_names:
			ner = self.model.create_pipe("ner")
			self.model.add_pipe(ner)
		# otherwise, get it, so we can add labels to it
		else:
			ner = self.model.get_pipe("ner")

		#Add labels to NER
		labels = self.get_labels()
		self.add_labels_to_nlp(labels)


		#Init trainer optimizer
		if loadPath == "":
			#New model
			optimizer = self.model.begin_training()
		else:
			#Loading model
			optimizer = self.model.resume_training()

		move_names = list(ner.move_names)
		# get names of other pipes to disable them during training
		other_pipes = [pipe for pipe in self.model.pipe_names if pipe != "ner"]
		with self.model.disable_pipes(*other_pipes):  # only train NER
			sizes = compounding(1.0, 4.0, 1.001)
			# batch up the examples using spaCy's minibatch
			for itn in range(self.number_iterations):
				DATASET = self.train_dataset
				if self.number_samples > 0 and self.number_samples < len(self.train_dataset):
					DATASET = random.sample(self.train_dataset,self.number_samples)
				else:
					random.shuffle(DATASET)
				batches = minibatch(DATASET, size=sizes)
				losses = {}
				for batch in batches:
					texts, annotations = zip(*batch)
					self.model.update(texts, annotations, sgd=optimizer, drop=0.35, losses=losses)

				print("Training in {}%({}/{})".format(str((itn/self.number_iterations)*100),itn,self.number_iterations))
				print("Losses", losses)

		if outputPath == "":
			self.save_NER()
		else:
			self.save_NER(outputPath)
		finish_time = datetime.now()
		print("Training NLP done! Elapsed time: {}".format(str(finish_time - satart_time)))
		return self.model


	def get_labels(self):
		return self.train_maker.labels


	def add_labels_to_nlp(self,labels):
		#Add labels in NER
		ner = None
		if 'ner' not in self.model.pipe_names:
			ner = self.model.create_pipe('ner')
			self.model.add_pipe(ner)
		else:
			ner = self.model.get_pipe('ner')

		for label in labels:
			if label not in self.model.entity.labels:
				ner.add_label(label)

	def save_NER(self,outputPath="persistence/temp/nlp/model"):
		outputPath = os.path.join(outputPath,"nlp_model")
		outputPath = Path(outputPath)
		if not outputPath.exists():
			outputPath.mkdir(parents=True)
		# self.model.meta["name"] = self.name_model  # rename model
		self.model.meta["name"] = "nlp_model"  # rename model
		self.model.to_disk(outputPath)
		# print("NLP model saved to", outputPath)

