import spacy
import random
from dateparser.search import search_dates
from rdflib import XSD
import re
from ontology.Schema import normalize_datatype
from nlp.NER import NER
# from nltk.stem import RSLPStemmer


class NLP_Processor():
	def __init__(self,loadPath="persistence/nlp/model/pt_br"):
		self.model = spacy.load(loadPath)
		# self.stop_words = spacy.lang.pt.stop_words.STOP_WORDS
		self.vector_size = len(self.model("test").vector)
		self.ner = NER()
		# self.stemmer = RSLPStemmer()
		

	def vector(self,sentence):
		#Stemming and stopwords removal degraded the classification performance

		# print(sentence)
		# sentenceAux = ""
		# tokens = NER.tokenize_sentence(sentence.lower())

		# # for token in tokens:
		# # 	# if token not in self.stop_words:
		# # 	sentenceAux+=(self.stemmer.stem(token))+" "

		# print(sentenceAux)
		# print("-----------------------")

		return self.model(sentence.lower()).vector

	def sentence_vector(self,sentence):
		return list(self.vector(sentence))

	def parser(self,sentence):
		sentenceAux = sentence.lower()
		
		entities = []
		#Search possibles values to strings CVs
		entities, sentenceAux = self.ner.parser(sentenceAux)
			
		#Search possibles values to date CVs
		dates = search_dates(sentenceAux,languages=['pt'])
		if dates:
			for date in dates:
				entities.append([(date[1],XSD.datetime),sentenceAux.index(date[0])])
				sentenceAux = sentenceAux.replace(date[0]," "*len(date[0]))
			
			
		#Search possibles values to numeric CVs
		numbers = re.findall("[-+]?\d+[\.]?\d*[eE]?[-+]?\d*", sentenceAux)
		if numbers:
			for number_str in numbers:
				number_index = sentenceAux.index(number_str)
				sentenceAux = sentenceAux.replace(number_str," "*len(number_str))
				number = float(number_str)
				if number.is_integer():
					#Number is a integer
					normalize_datatype
					entities.append([(number,normalize_datatype(XSD.integer)),number_index])
				else:
					#Number is a real
					entities.append([(number,normalize_datatype(XSD.float)),number_index])

		#sort variables in apperition order
		unorded_matchs = entities.copy()
		entities = []
		unorded_matchs.sort(key = lambda x:x[1])
		for match in unorded_matchs:
			entities.append(match[0])
		return entities,sentenceAux

	def close(self):
		self.ner.close()
