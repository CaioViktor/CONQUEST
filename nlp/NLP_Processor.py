import spacy
import random
from dateparser.search import search_dates
from rdflib import XSD
import re
from ontology.Schema import normalize_datatype

class NLP_Processor():
	def __init__(self,loadPath):
		self.model = spacy.load(loadPath)
		self.vector_size = len(self.model("test").vector)

	def vector(self,sentence):
		return self.model(sentence).vector

	def sentence_vector(self,sentence):
		return list(self.vector(sentence))

	def parse_sentece(self,sentence):
		sentenceAux = sentence
		
		entities = []
		#Search possibles values to strings CVs
		doc = self.model(sentence)
		for entity in doc.ents:
			entityStr = str(entity)
			sentenceAux = sentenceAux.replace(entityStr,"")
			entities.append((entityStr,entity.label_))
			
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
