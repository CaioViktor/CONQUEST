from SPARQLWrapper import SPARQLWrapper, JSON
import ontology.Schema as sc

#Class to Retrive property's values used in NER from SPARQL endpoint
LIMIT = 10000
class Instances_Retriever():
	def __init__(self,url_endpoint,graph_name="",number_samples=0):
		self.url_endpoint = url_endpoint
		self.graph_name = graph_name
		self.number_samples = number_samples #Maximum number of samples retrieved from RDF graph
		if self.graph_name != "":
			self.graph_name = " FROM <{}> ".format(self.graph_name)
		self.instances = {} #Save values of instances. Used to prevent query a same property multiple times

	def retriver(self,classs,propertyy):
		#Retrive instances
		instance_id = sc.uri_to_hash(classs+propertyy)
		if instance_id in self.instances:
			#Instances already stored in memory
			return self.instances[instance_id]
		else:
			#Need query SPARQL endpoint to get instances