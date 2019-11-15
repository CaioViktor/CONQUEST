import numpy as np
import pandas as pd
from sklearn.naive_bayes import GaussianNB
import os
from pathlib import Path
import pickle as pic
from rdflib import XSD


from nlp.Train_Maker import Train_Maker
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.naive_bayes import GaussianNB
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import  VotingClassifier
from sklearn.model_selection import cross_val_score
from datetime import datetime
from copy import deepcopy


MODEL_FILE = "ml_classifier.sav"
MODEL_PATH = "persistence/classifier/"
MODEL_PATH_TEMP = "persistence/temp/classifier/"


class ML_Classifier():
	def __init__(self,model_path=MODEL_PATH,model_file=MODEL_FILE):
		self.model_path = model_path
		self.model_file = model_file
		#Classifier is always wrong
		gaussian = GaussianNB()
		linear = LogisticRegression(random_state=0, solver='lbfgs',multi_class='multinomial',n_jobs=-1)

		self.model = VotingClassifier(estimators=[('gaus', gaussian), ('line', linear)],voting='soft',n_jobs=-1)

		self.original_model = deepcopy(self.model)
		self.scaler = StandardScaler()
		



	@staticmethod
	def pre_process_data(QAIs,nlp_processor):
		#Transform QAIs in train dataset to train the classifier
		#QV: Question Vector; SV: Sentence Vector; CVec: Context Vector
		dataset = []
		labels_dataset = []

		
		type_CV_to_CVec_idx = nlp_processor.type_CV_to_CVec_idx
		columns = nlp_processor.columns_CVec
		# print(type_CV_to_CVec_idx)

		#Getting train dataset
		for qai in QAIs:
			qp_index = 0
			for qp in qai.QPs:
				#Getting QV = SV+CVec.  

				# labels_dataset.append(qai.id)

				# sentence = qp
				CVec = [0] * len(columns)
				for cv_id in qai.CVs:
					#Getting CVec: Context Vector
					cv = qai.CVs[cv_id]

					#remove CV from QP
					# sentence = sentence.replace(cv['name'],"oovmarker")

					if XSD.string not in cv['class']:
						if len(cv['class']) > 0:
							#CV is from a primitive type (integer,decimal or datetime)
							classs = list(cv['class'])[0]
							# print("class: ",classs,"\nvector\n",type_CV_to_CVec_idx)
							# print(classs[0])
							#TODO: Check error on non strings CVs
							cvec_idx = type_CV_to_CVec_idx[nlp_processor.hash(str(classs))]
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
								cvec_idx = type_CV_to_CVec_idx[nlp_processor.hash(str(typee))]
								CVec[cvec_idx] += 1
				#End CVec computing
				# sentence = sentence.lower()
				# SV = nlp_processor.sentence_vector(sentence)
				SV = qai.SVs[qp_index]
				QV = SV + CVec + [qai.id]
				# print("sentença que vai ser usada:",sentence,"\n",QV,"\n\n")
				# QV =  CVec
				# print("Classe:",qai.id,"QP:",sentence,"\n","CVec",CVec,"\nSV:",SV,"\n\n")
				dataset.append(QV)
				qp_index+=1
		columns_header = list(range(0,nlp_processor.vector_size))+columns+['label']
		# columns_header = columns



		# features_dataframe = pd.DataFrame(dataset,columns=columns_header)
		# label_dataframe = pd.DataFrame(labels_dataset,columns=['label'])
		dataframe = pd.DataFrame(dataset,columns=columns_header).sample(frac=1,random_state=42)
		label_dataframe = dataframe['label']
		features_dataframe = dataframe.drop('label',axis=1)

		# ML_Classifier.save_XY(features_dataframe,label_dataframe)


		return features_dataframe,label_dataframe

	@staticmethod
	def load_model(modelPath= (MODEL_PATH+MODEL_FILE)):
		with open(modelPath,"rb") as pickle_file:
			ml_classifier = pic.load(pickle_file)
			print("Loaded classifier model from", modelPath)
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
		self.scaler.fit(X.astype(np.float64))
		X = self.scaler.transform(X.astype(np.float64))
		#X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=0.2)
		
		
		self.model.fit(X,y)


		finish_time = datetime.now()
		print("Training classifier done! Elapsed time: {}".format(str(finish_time - satart_time)))
		self.eval_model(X,y)

		# self.save_model()



	def eval_model(self,X,y):

		modelP = deepcopy(self.original_model)
		modelR = deepcopy(self.original_model)
		modelF = deepcopy(self.original_model)

		cv = 7
		precision = cross_val_score(modelP, X, y.values.ravel(), cv=cv,scoring='precision_weighted')
		p = precision.mean()

		recall = cross_val_score(modelR, X, y.values.ravel(), cv=cv,scoring='recall_weighted')
		r = recall.mean()

		f1 = cross_val_score(modelF, X, y.values.ravel(), cv=cv,scoring='f1_weighted')
		f = f1.mean()

		print("\n\nScore evaluations using cross validation with cv = {}:\nPrecision = {}\nRecall = {}\nF-1 Score = {}".format(cv,p,r,f))
		return

	def predict(self,X):
		#Normalizer
		X = self.scaler.transform(X.astype(np.float64))

		# print("Classes: ",self.model.classes_)
		print("Probs:",self.model.predict_proba(X))
		# return self.model.predict_proba(X)
		return self.model.predict(X)

	def predict_proba(self,X):
		#Normalizer
		X = self.scaler.transform(X.astype(np.float64))

		# print("Classes: ",self.model.classes_)
		# print("Probs:",self.model.predict_proba(X))
		# return self.model.predict_proba(X)
		return self.model.predict_proba(X)

	def save_model(self,savePath=MODEL_PATH,model_file=MODEL_FILE):
		savePath = Path(savePath)
		
		if not savePath.exists():
			savePath.mkdir(parents=True)
		saveFile = os.path.join(savePath,model_file)
		with open(saveFile,"wb") as pickle_file:
			pic.dump(self,pickle_file)
			print("Saved classifier model to", saveFile)

	
