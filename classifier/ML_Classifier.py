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

def new_model():
	gaussian = GaussianNB()
	linear = LogisticRegression(random_state=0, solver='lbfgs',multi_class='multinomial',n_jobs=-1)
	return VotingClassifier(estimators=[('gaus', gaussian), ('line', linear)],voting='soft',n_jobs=-1)
	# return GaussianNB()

class ML_Classifier():
	def __init__(self,model_path=MODEL_PATH,model_file=MODEL_FILE, model = None):
		self.model_path = model_path
		self.model_file = model_file
		
		if model == None:
			#Set Default model

			self.model = new_model()
			# self.model = GaussianNB()
		else:
			#Set customized model
			print("Using customized model")
			self.model = model

		self.original_model = deepcopy(self.model)
		self.scaler = StandardScaler()
		self.X = None
		self.y = None
		



	@staticmethod
	def pre_process_data(QAIs,nlp_processor,use_semantic_features = True,number_qp_samples = 0):
		#Transform QAIs in train dataset to train the classifier
		#QV: Question Vector; SV: Sentence Vector; CVec: Context Vector
		print("Using semantic features {}. QPs limited {}".format(use_semantic_features,number_qp_samples != 0))
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
				QV = []
				if use_semantic_features:
					QV = SV + CVec + [qai.id]
				else:
					QV = SV + [qai.id]
				# print("sentença que vai ser usada:",sentence,"\n",QV,"\n\n")
				# QV =  CVec
				# print("Classe:",qai.id,"QP:",sentence,"\n","CVec",CVec,"\nSV:",SV,"\n\n")
				dataset.append(QV)
				qp_index+=1
				if number_qp_samples != 0 and qp_index >=  number_qp_samples:
					#Reached of number of QPs limited
					print("Reached QPs limited ",number_qp_samples)
					break
		if use_semantic_features:
			columns_header = list(range(0,nlp_processor.vector_size))+columns+['label']
		else:
			columns_header = list(range(0,nlp_processor.vector_size))+['label']
		# columns_header = columns


		# features_dataframe = pd.DataFrame(dataset,columns=columns_header)
		# label_dataframe = pd.DataFrame(labels_dataset,columns=['label'])
		dataframe = pd.DataFrame(dataset,columns=columns_header).sample(frac=1,random_state=42)
		label_dataframe = dataframe['label']
		features_dataframe = dataframe.drop('label',axis=1)

		# ML_Classifier.save_XY(features_dataframe,label_dataframe)
		# print(features_dataframe.head(1))
		
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


	def update_XY(self,new_QV,new_label):
		self.X = self.X.append(new_QV)
		self.y = self.y.append(pd.Series([new_label]))

		path_X = os.path.join(MODEL_PATH_TEMP,"X.sav")
		path_Y = os.path.join(MODEL_PATH_TEMP,"y.sav")

		with open(path_X,"wb") as file:
			pic.dump(self.X,file)
			# print("Saved X")

		with open(path_Y,"wb") as file:
			pic.dump(self.y,file)
			# print("Saved Y")

	# 	print("Features vector saved to {}\nClasses vector saved to {}",path_X,path_Y)


	def load_XY(self):
		path_X = os.path.join(MODEL_PATH_TEMP,"X.sav")
		path_Y = os.path.join(MODEL_PATH_TEMP,"y.sav")
		with open( path_X,"rb") as file:
			X = pic.load(file)
		with open( path_Y,"rb") as file:
			y = pic.load(file)


		print("Load X and y from Persistence:\nX from {}\nY from {}".format(path_X,path_Y))
		self.X,self.y = X,y
		return X,y

	def fit(self,X,y):
		self.X,self.y = X,y
		satart_time = datetime.now()
		#Normalizer
		# scaler = StandardScaler()
		self.scaler.fit(X.astype(np.float64))
		X = self.scaler.transform(X.astype(np.float64))
		#X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=0.2)
		
		
		self.model.fit(X,y)


		finish_time = datetime.now()
		print("Training classifier done! Elapsed time: {}".format(str(finish_time - satart_time)))
		return finish_time - satart_time
		# self.eval_model(X,y)

		# self.save_model()

	def update(self):
		X,y = self.X,self.y
		# scaler = StandardScaler()
		self.scaler.fit(X.astype(np.float64))
		X = self.scaler.transform(X.astype(np.float64))
		self.model = new_model()
		self.model.fit(X,y)
		self.save_model()

	def eval_model(self,X,y,cv=5):

		modelP = deepcopy(self.original_model)
		modelR = deepcopy(self.original_model)
		modelF = deepcopy(self.original_model)


		precision = cross_val_score(modelP, X, y.values.ravel(), cv=cv,scoring='precision_weighted')
		p = precision.mean()

		recall = cross_val_score(modelR, X, y.values.ravel(), cv=cv,scoring='recall_weighted')
		r = recall.mean()

		f1 = cross_val_score(modelF, X, y.values.ravel(), cv=cv,scoring='f1_weighted')
		f = f1.mean()

		print("\n\nScore evaluations using cross validation with cv = {}:\nPrecision = {}\nRecall = {}\nF-1 Score = {}".format(cv,p,r,f))
		return p,r,f

	def predict(self,X):
		#Normalizer
		X = self.scaler.transform(X.astype(np.float64))

		# print("Classes: ",self.model.classes_)
		# print("Probs:",self.model.predict_proba(X))
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

	
