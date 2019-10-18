import nlp.Solr_Connection as solr_connection
# import Solr_Connection as solr_connection
import pysolr
from functools import reduce
from nltk.tokenize import sent_tokenize, word_tokenize 

class NER():
	def __init__(self,solr_host="http://localhost",solr_port="8983",solr_core="conquest_exact_match",solr_memory = "1g"):
		self.solr_url = "{}:{}/solr/{}/".format(solr_host,solr_port,solr_core)
		self.solr_port = solr_port
		self.solr_core = solr_core
		self.solr_host = solr_host
		solr_connection.startup(self.solr_port,solr_memory)
		self.solr = pysolr.Solr(self.solr_url, timeout=10)


	def parser(self,text):
		#Search named entities in the whole text.
		#TODO: Manter a ordem dos matchs encontrados no texto? Ignorar acentos?  otimizar
		matchs = []
		sentences = sent_tokenize(text)
		text_final = ""
		for sentence in sentences:
			text_final += self.parser_sentence(sentence,matchs)

		return matchs,text_final

	def parser_sentence(self,sentence,matchs):
		#Search named entities in the sentence.
		sentence_splitted = self.tokenize_sentence(sentence)

		window_size = len(sentence_splitted)

		while window_size > 0 and window_size <= len(sentence_splitted):
			#Uses a sliding window to match segments from sentence to index. Window's size begin as full sentence's lenght and going decreasing by one until 0 or all sentence's fragments already have match.
			window_start = 0
			window_end = window_start + window_size
			remove_elements = []
			while window_end <= len(sentence_splitted):
				term_search = reduce(lambda x,y:"{} {}".format(x,y),sentence_splitted[window_start:window_end])
				label = self.search(term_search)
				if label != None:
					# print("achou",term_search," em ",sentence_splitted[window_start:window_end])
					#Term is present in index
					matchs.append((term_search,label))
					remove_elements.append(term_search)
				window_start+=1
				window_end = window_start + window_size
			sentence = self.remove_matchs(sentence,remove_elements)
			sentence_splitted = self.tokenize_sentence(sentence)
			window_size-=1
			sentence_final = reduce(lambda x,y:"{} {}".format(x,y),sentence_splitted)
		return sentence_final

		

	def close(self):
		solr_connection.stop()

#Utility functions
	def search(self,term):
		# print("buscando",term)
		results = self.solr.search('values:"{}"'.format(term))
		if results.hits > 0:
			# print("achou")
			#Term is in index
			label = results.docs[0]['id']
			#By now, only the first result is been considerating
			return label
		return None

	@staticmethod
	def remove_matchs(sentence,remove_elements):
		for term in remove_elements:
			# print("removendo '{}' da sentença '{}'".format(term,sentence))
			sentence = sentence.replace(term,"")
		return sentence

	@staticmethod
	def tokenize_sentence(sentence):
		tokens = word_tokenize(sentence)
		return tokens

# def test(sentence):
# 	print(sentence)
# 	print(ner.parser(sentence))
# 	print("--------------------------------")


# #Tests 
# ner = NER()
# test("teste com uma frase qualquer que não deve retornar")
# test("Um exemplo com válidos reopro e buscopan, mas buscopam está errado e outro que não deveria composto e buscopan composto, mas não buscopan compost. além de abacavir e são paulo que é sp e ceará que é ce")

# ner.close()


