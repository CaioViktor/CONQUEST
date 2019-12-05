import nlp.Solr_Connection as solr_connection
# import Solr_Connection as solr_connection
import pysolr
from functools import reduce
from nltk.tokenize import sent_tokenize, word_tokenize 
import re

class NER():
	def __init__(self,solr_host="http://localhost",solr_port="8983",solr_core="conquest_exact_match",solr_memory = "1g",startup_solr=True):
		self.solr_url = "{}:{}/solr/{}/".format(solr_host,solr_port,solr_core)
		self.solr_port = solr_port
		self.solr_core = solr_core
		self.solr_host = solr_host
		if startup_solr:
			solr_connection.startup(self.solr_port,solr_memory)
			self.solr = pysolr.Solr(self.solr_url, timeout=10)


	def parser(self,text):
		#Search named entities in the whole text.
		#TODO: otimizar
		#This method can be optimizaded searching if individual words are containd in the index (partial match). if not, replace them with "."
		matchs = []
		sentences = sent_tokenize(text)
		text_final = ""
		sentence_oov= ""
		for sentence in sentences:
			sentence_parsed,sentence_oov_parsed = self.parser_sentence(sentence,matchs,text)
			text_final += sentence_parsed + " "
			sentence_oov+=sentence_oov_parsed+" "


		return matchs,text_final,sentence_oov

	def parser_sentence(self,sentence,matchs,text):
		#Search named entities in the sentence.
		sentence_splitted = self.tokenize_sentence(sentence)
		sentence_final = sentence
		
		text_marked = text

		sentence_oov = sentence
		# unorded_matchs = []

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
					#Term is present in index
					# matchs.append((term_search,label))
					
					#Get term's order in sentence
					term_index_order = text_marked.index(term_search)
					text_marked = text_marked.replace(term_search,(" " * len(term_search)),1)
					sentence_oov =sentence_oov.replace(term_search,"oovmarker",1)

					# unorded_matchs.append( [(term_search,label),term_index_order] )
					matchs.append( [(term_search,label),term_index_order] )

					# print("achou",term_search," em ",sentence_splitted[window_start:window_end],len(unorded_matchs),"\n\n\n")

					#Remove term in searched sentence
					sentence_final = sentence_final.replace(term_search,(" " * len(term_search)),1)
					remove_elements.append(term_search)
				window_start+=1
				window_end = window_start + window_size
			sentence = self.remove_matchs(sentence,remove_elements)
			sentence_splitted = self.tokenize_sentence(sentence)
			window_size-=1

		# sentence_final = reduce(lambda x,y:"{} {}".format(x,y),sentence_splitted)
		#sort variables in apperition order
		# unorded_matchs.sort(key = lambda x:x[1])
		# for match in unorded_matchs:
			# matchs.append(match[0])

		return sentence_final,sentence_oov
		# return text_marked

		

	def close(self):
		solr_connection.stop()

#Utility functions
	def search(self,term):
		# print("buscando",term)
		term =  re.sub("[^a-zA-Z0-9]",".",term)
		results = self.solr.search('values:/{}/'.format(term))
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
			sentence = sentence.replace(term,"",1)
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


