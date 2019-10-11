import numpy as np
import pandas as pd
from sklearn.naive_bayes import GaussianNB
import os
from pathlib import Path
import pickle as pic
from rdflib import XSD
import hashlib
from nlp.Train_Maker import Train_Maker
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split


MODEL_FILE = "ml_classifier.sav"
MODEL_PATH = "persistence/temp/classifier"

class ML_Classifier():
	def __init__(self):
		self.model = GaussianNB()
		#TODO: Usar melhor modelo

	@staticmethod
	def pre_process_data(QAIs,labels_NER,nlp_processor):
		#Transform QAIs in train dataset to train the classifier
		#QV: Question Vector; SV: Sentence Vector; CVec: Context Vector
		dataset = []
		labels_dataset = []

		#Getting CVec structure
		columns = [XSD.integer.n3(),XSD.decimal.n3(),XSD.dateTime.n3()] + labels_NER
		columns.sort()
		type_CV_to_CVec_idx = {}
		for column in columns:
			type_CV_to_CVec_idx[ML_Classifier.hash(column)] = columns.index(column)

		# print(type_CV_to_CVec_idx)


		#Getting train dataset
		for qai in QAIs:
			for qp in qai.QPs:
				#Getting QV = SV+CVec.  

				labels_dataset.append(qai.id)

				sentence = qp
				CVec = [0] * len(columns)
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


		features_dataframe = pd.DataFrame(dataset,columns=columns_header)
		label_dataframe = pd.DataFrame(labels_dataset,columns=['label'])

		


		return features_dataframe,label_dataframe

	@staticmethod
	def load_model(loadPath=MODEL_PATH,modelFile=MODEL_FILE):
		file_path = os.path.join(loadPath,modelFile)
		with open(file_path,"rb") as pickle_file:
			ml_classifier = ML_Classifier()
			ml_classifier.model = pic.load(pickle_file)
			print("Loaded classifier model from", file_path)
			return ml_classifier



	def fit(self,X,y):
		#Normalizer
		scaler = StandardScaler()
		X = scaler.fit_transform(X.astype(np.float64))
		X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=0.2)
		#TODO: Train model
		
		self.model.fit(X,y)


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
