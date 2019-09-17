import numpy as np
import pandas as pd
from sklearn.naive_bayes import GaussianNB
import os
from pathlib import Path
import pickle as pic
from rdflib import XSD
import hashlib
from nlp.Train_Maker import Train_Maker


MODEL_FILE = "ml_classifier.sav"
MODEL_PATH = "temp/classifier"

class ML_Classifier():
	def __init__(self):
		self.model = GaussianNB()

	@staticmethod
	def pre_process_data(QAIs,labels_NER,nlp_processor):
		#Transform QAIs in train dataset to train the classifier
		#QV: Question Vector; SV: Sentence Vector; CVec: Context Vector
		dataset = []

		#Getting CVec structure
		columns = [XSD.integer,XSD.decimal,XSD.dateTime] + labels_NER
		columns.sort()
		type_CV_to_CVec_idx = {}
		for column in columns:
			type_CV_to_CVec_idx[ML_Classifier.hash(column)] = columns.index(column)

		# print(type_CV_to_CVec_idx)


		#Getting train dataset
		for qai in QAIs:
			for qp in qai.QPs:
				sentence = qp
				CVec = [0] * len(columns)
				#Getting QV = SV+CVec.  
				for cv_id in qai.CVs:
					#Getting CVec: Context Vector
					cv = qai.CVs[cv_id]

					#remove CV from QP
					sentence = sentence.replace(cv['name'],"")

					if XSD.string not in cv['class']:
						#CV is from a primitive type (integer,decimal or datetime)
						classs = list(cv['class'])
						# print(classs[0])
						cvec_idx = type_CV_to_CVec_idx[ML_Classifier.hash(classs)]
						CVec[cvec_idx]+=1
					else:
						#CV is Property@Class
						for owner_id in cv['owners']:
							#Get all possible combinations of Property@Class
							owner = cv['owners'][owner_id]
							propertyy = cv['owners'][owner_id]['uri']
							for classs in cv['owners'][owner_id]['classes']:
								typee = Train_Maker.create_label(classs,propertyy)
								# print(typee)
								cvec_idx = type_CV_to_CVec_idx[ML_Classifier.hash(typee)]
								CVec[cvec_idx] += 1
				#End CVec computing
				SV = nlp_processor.sentence_vector(sentence)
				QV = SV + CVec
				dataset.append(QV)
		columns_header = list(range(0,nlp_processor.vector_size))+columns

		return pd.DataFrame(dataset,columns=columns_header)

	@staticmethod
	def load_model(loadPath=MODEL_PATH,modelFile=MODEL_FILE):
		file_path = os.path.join(loadPath,modelFile)
		with open(file_path,"rb") as pickle_file:
			ml_classifier = ML_Classifier()
			ml_classifier.model = pic.load(pickle_file)
			print("Loaded classifier model from", file_path)
			return ml_classifier



	def fit(self,X,Y):
		self.model.fit(X,Y)


	def predict(self,X):
		return self.model.predict(X)

	def save_model(self,savePath=MODEL_PATH):
		savePath = os.path.join(savePath,MODEL_FILE)
		savePath = Path(savePath)
		if not savePath.exists():
			savePath.mkdir(parents=True)
		with open(savePath,"wb") as pickle_file:
			pic.dump(self.model,pickle_file)
			print("Saved classifier model to", savePath)

	def hash(term):
		return hashlib.md5(str(term).encode('utf-8')).hexdigest()
