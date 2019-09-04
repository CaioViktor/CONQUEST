from abc import ABC, abstractmethod
from nlp.Train_Maker import Train_Maker
import pickle as pic
import os

#Template method pattern design

#Train Named Entity Recognition to recognize class properties values in senteces. It's values will be used in Context Variables
class NER_Trainer_Template(ABC):
	def __init__(self,QAIs,class_index,url_endpoint,graph_name="",number_iterations=100,number_samples=0):
		self.class_index = class_index
		self.number_iterations = number_iterations
		self.train_maker = Train_Maker(QAIs,class_index,url_endpoint,graph_name,number_samples)
		self.train_dataset = None

	def make_train_dataset(self,savePath=""):
		dataset = self.train_maker.make_train_dataset()
		if savePath != "":
			pathOut = os.path.join(savePath,"train_dataset.pickle")
			with open(pathOut,"wb") as pickle_file:
				pic.dump(dataset,pickle_file)
			pathOut_labels = os.path.join(savePath,"labels.pickle")
			with open(pathOut_labels,"wb") as pickle_file:
				pic.dump(self.get_labels(),pickle_file)
		self.train_dataset = dataset
		return self


	def load_train_dataset(self,loadPath):
		pathOut = os.path.join(loadPath,"train_dataset.pickle")
		with open(pathOut,"rb") as pickle_file:
			self.train_dataset = pic.load(pickle_file)

		pathOut_labels = os.path.join(loadPath,"labels.pickle")
		with open(pathOut_labels,"rb") as pickle_file:
			self.train_maker.labels = pic.load(pickle_file)
		return self


	def train_NER(self,loadPath=""):
		if loadPath != "":
			self.load_train_dataset(loadPath)
		if self.train_dataset == None:
			self.make_train_dataset()
		#TODO: Train model
		return self.train_dataset

	def get_labels(self):
		return self.train_maker.labels

		


	

