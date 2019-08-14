import pandas as pd
import ontology.Schema as schema_processor
from rdflib import OWL, RDF, RDFS, OWL, XSD,URIRef,BNode,Variable,Literal

class Factory_ContextVariables():
	def __init__(self,classes):
		self.id_index = {}
		self.id_to_uri = {schema_processor.uri_to_hash(XSD.string):XSD.string.n3(),schema_processor.uri_to_hash(XSD.decimal):XSD.decimal.n3(),schema_processor.uri_to_hash(XSD.integer):XSD.integer.n3(),schema_processor.uri_to_hash(XSD.dateTime):XSD.dateTime.n3(),schema_processor.uri_to_hash(XSD.boolean):XSD.boolean.n3()}
		self.columns = [schema_processor.uri_to_hash(XSD.string),schema_processor.uri_to_hash(XSD.decimal),schema_processor.uri_to_hash(XSD.integer),schema_processor.uri_to_hash(XSD.dateTime),schema_processor.uri_to_hash(XSD.boolean)]
		self.columns_names = list()
		
		for classs in classes:
			self.id_to_uri[classs] = classes[classs]['uri'].n3()
			self.columns.append(classs)

		#Ensure that columns vectors always have the same order
		self.columns.sort()
		i = 0
		for index in self.columns:
			self.id_index[index] = i
			self.columns_names.append(self.id_to_uri[index])
			i+=1


	def build_ContextVariables_vector(self,CVs):
		vector = [0] * len(self.columns)

		for CV in CVs:
			for class_cv in CVs[CV]['class']:
				CV_id = schema_processor.uri_to_hash(class_cv)
				vector[self.id_index[CV_id]] += 1

		return pd.DataFrame([vector],columns=self.columns)

