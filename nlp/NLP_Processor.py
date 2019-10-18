import spacy
import random
from dateparser.search import search_dates
from rdflib import XSD
import re
from ontology.Schema import normalize_datatype
from nlp.NER import NER

class NLP_Processor():
	def __init__(self,loadPath="pt_core_news_sm"):
		self.model = spacy.load(loadPath)
		self.vector_size = len(self.model("test").vector)
		self.ner = NER()

	def vector(self,sentence):
		return self.model(sentence).vector

	def sentence_vector(self,sentence):
		return list(self.vector(sentence))

	def parser(self,sentence):
		sentenceAux = sentence.lower()
		
		entities = []
		#Search possibles values to strings CVs
		entities, sentenceAux = self.ner.parser(sentence)
			
		#Search possibles values to date CVs
		dates = search_dates(sentenceAux)
		if dates:
			for date in dates:
				entities.append((date[1],XSD.datetime))
				sentenceAux = sentenceAux.replace(date[0],"")
			
			
		#Search possibles values to numeric CVs
		numbers = re.findall("[-+]?\d+[\.]?\d*[eE]?[-+]?\d*", sentenceAux)
		if numbers:
			for number_str in numbers:
				sentenceAux = sentenceAux.replace(number_str,"")
				number = float(number_str)
				if number.is_integer():
					#Number is a integer
					normalize_datatype
					entities.append((number,normalize_datatype(XSD.integer)))
				else:
					#Number is a real
					entities.append((number,normalize_datatype(XSD.float)))
		return entities,sentenceAux

	def close(self):
		self.ner.close()
