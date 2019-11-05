import spacy
import random
from dateparser.search import search_dates
from rdflib import XSD
import re
from ontology.Schema import normalize_datatype
from nlp.NER import NER
import hashlib
import numpy as np
import pandas as pd
from nltk.stem import RSLPStemmer


class NLP_Processor():
	def __init__(self,labels_NER,loadPath="persistence/nlp/model/pt_br"):
		self.model = spacy.load(loadPath)
		self.stop_words = spacy.lang.pt.stop_words.STOP_WORDS
		self.vector_size = len(self.model("test").vector)
		self.ner = NER()
		self.stemmer = RSLPStemmer()

		self.labels_NER = labels_NER

		#Getting CVec structure
		self.columns_CVec = [str(XSD.integer),str(XSD.decimal),str(XSD.dateTime)] + labels_NER
		self.columns_CVec.sort()
		self.type_CV_to_CVec_idx = {}
		for column in self.columns_CVec:
			self.type_CV_to_CVec_idx[self.hash(column)] = self.columns_CVec.index(column)
		

	def vector(self,sentence):
		#Get SV: Sentence Vector as numpay array
		#Stemming and stopwords removal degraded the classification performance

		# print(sentence)
		# sentenceAux = ""
		# tokens = NER.tokenize_sentence(sentence.lower())

		# for token in tokens:
			# if token not in self.stop_words:
				# sentenceAux+=(self.stemmer.stem(token))+" "

		# print(sentenceAux)
		# print("-----------------------")
		# return self.model(sentenceAux).vector
		return self.model(sentence.lower()).vector

	def sentence_vector(self,sentence):
		#Get SV: Sentence Vector as list
		return list(self.vector(sentence))

	def parser(self,sentence):
		sentenceAux = sentence.lower()
		
		entities = []
		#Search possibles values to strings CVs
		entities, sentenceAux,sentence_oov = self.ner.parser(sentenceAux)
			
		#Search possibles values to date CVs
		dates = search_dates(sentenceAux,languages=['pt'])
		if dates:
			for date in dates:
				entities.append([(date[1],str(XSD.dateTime)),sentenceAux.index(date[0])])
				sentenceAux = sentenceAux.replace(date[0]," "*len(date[0]),1)
				sentence_oov = sentence_oov.replace(date[0],"oovmarker",1)
			
			
		#Search possibles values to numeric CVs
		numbers = re.findall("[-+]?\d+[\.]?\d*[eE]?[-+]?\d*", sentenceAux)
		if numbers:
			for number_str in numbers:			
				number_index = sentenceAux.index(number_str)
				sentenceAux = sentenceAux.replace(number_str," "*len(number_str),1)
				sentence_oov = sentence_oov.replace(number_str,"oovmarker",1)
				number = float(number_str)
				if number.is_integer():
					#Number is a integer
					entities.append([(number,str(normalize_datatype(XSD.integer))),number_index])
				else:
					#Number is a real
					entities.append([(number,str(normalize_datatype(XSD.float))),number_index])

		#sort variables in apperition order
		unorded_matchs = entities.copy()
		entities = []
		unorded_matchs.sort(key = lambda x:x[1])
		for match in unorded_matchs:
			entities.append(match[0])
		return entities,sentence_oov

	def transform_CVec(self,CVs):
		#Transform CVs list in Contex Vector(CVec)
		CVec = [0] * len(self.columns_CVec)
		for cv in CVs:
			cvec_idx = self.type_CV_to_CVec_idx[self.hash(cv[1])]
			CVec[cvec_idx]+=1
		return CVec

	def transform_QV(self,sentence,CVs):
		CVec = self.transform_CVec(CVs)

		columns_header = list(range(0,self.vector_size))+self.columns_CVec
		# columns_header = self.columns_CVec

		SV = self.sentence_vector(sentence) 

		QV_list = SV + CVec
		# QV_list = CVec
		dataset = [QV_list]

		QV = pd.DataFrame(dataset,columns=columns_header)
		return QV,(SV,CVec)

	def close(self):
		self.ner.close()

	@staticmethod
	def hash(term):
		return hashlib.md5(str(term).encode('utf-8')).hexdigest()
