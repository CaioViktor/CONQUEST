import spacy
class NLP_Processor():
	def __init__(self,loadPath):
		self.model = spacy.load(loadPath)
		self.vector_size = len(self.model("test").vector)

	def vector(self,sentence):
		return self.model(sentence).vector

	def sentence_vector(self,sentence):
		return list(self.vector(sentence))