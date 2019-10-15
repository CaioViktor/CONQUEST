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
from sklearn.naive_bayes import GaussianNB
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import  VotingClassifier
from sklearn.model_selection import cross_val_score
from datetime import datetime


MODEL_FILE = "ml_classifier.sav"
MODEL_PATH = "persistence/classifier/"
MODEL_PATH_TEMP = "persistence/temp/classifier/"


class ML_Classifier():
	def __init__(self,model_path=MODEL_PATH,model_file=MODEL_FILE):
		self.model_path = model_path
		self.model_file = model_file
		gaussian = GaussianNB()
		linear = LogisticRegression(random_state=0, solver='lbfgs',multi_class='multinomial',n_jobs=-1)

		self.model = VotingClassifier(estimators=[('gaus', gaussian), ('line', linear)],voting='hard',n_jobs=-1)

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

		ML_Classifier.save_XY(features_dataframe,label_dataframe)


		return features_dataframe,label_dataframe

	@staticmethod
	def load_model(loadPath=MODEL_PATH,modelFile=MODEL_FILE):
		file_path = os.path.join(loadPath,modelFile)
		with open(file_path,"rb") as pickle_file:
			ml_classifier = ML_Classifier()
			ml_classifier.model = pic.load(pickle_file)
			print("Loaded classifier model from", file_path)
			return ml_classifier

	@staticmethod
	def save_XY(X,y):
		path_X = os.path.join(MODEL_PATH_TEMP,"X.sav")
		path_Y = os.path.join(MODEL_PATH_TEMP,"y.sav")

		with open(path_X,"wb") as file:
			pic.dump(X,file)
			print("Saved X")

		with open(path_Y,"wb") as file:
			pic.dump(y,file)
			print("Saved Y")

	# 	print("Features vector saved to {}\nClasses vector saved to {}",path_X,path_Y)


	def load_XY(self):
		path_X = os.path.join(MODEL_PATH_TEMP,"X.sav")
		path_Y = os.path.join(MODEL_PATH_TEMP,"y.sav")
		with open( path_X,"rb") as file:
			X = pic.load(file)
		with open( path_Y,"rb") as file:
			y = pic.load(file)


		print("Load X and y from Persistence:\nX from {}\nY from {}".format(path_X,path_Y))
		return X,y

	def fit(self,X,y):
		satart_time = datetime.now()
		#Normalizer
		scaler = StandardScaler()
		X = scaler.fit_transform(X.astype(np.float64))
		#X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=0.2)
		
		self.model.fit(X,y)

		self.eval_model(X,y)

		finish_time = datetime.now()
		print("Training classifier done! Elapsed time: {}".format(str(finish_time - satart_time)))

		# self.save_model()


	def update(self,x,y):
		# TODO: Update model
		return


	def eval_model(self,X,y):
		cv = 7
		precision = cross_val_score(self.model, X, y.values.ravel(), cv=cv,scoring='precision_weighted')
		p = precision.mean()

		recall = cross_val_score(self.model, X, y.values.ravel(), cv=cv,scoring='recall_weighted')
		r = recall.mean()

		f1 = cross_val_score(self.model, X, y.values.ravel(), cv=cv,scoring='f1_weighted')
		f = f1.mean()

		print("\n\nScore evaluations using cross validation with cv = {}:\nPrecision = {}\nRecall = {}\nF-1 Score = {}".format(cv,p,r,f))
		return

	def predict(self,X):
		return self.model.predict(X)

	def save_model(self,savePath=MODEL_PATH,model_file=MODEL_FILE):
		savePath = Path(savePath)
		
		if not savePath.exists():
			savePath.mkdir(parents=True)


		saveFile = os.path.join(savePath,model_file)
		with open(saveFile,"wb") as pickle_file:
			pic.dump(self.model,pickle_file)
			print("Saved classifier model to", saveFile)

	def hash(term):
		return hashlib.md5(str(term).encode('utf-8')).hexdigest()
