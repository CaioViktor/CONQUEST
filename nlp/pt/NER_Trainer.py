from SPARQLWrapper import SPARQLWrapper, JSON
import os
import ontology.Schema as sc

#Train Named Entity Recognition to recognize class properties values in senteces. It's values will be used in Context Variables
#Class to model in Brazilian portuguese
class NER_Trainer():
	def __init__(self,endpoint,graph):
		self.endpoint = endpoint
		self.graph = graph
		self.labels = self.retrieve_NER_Labels()
		self.retrieve_Property_Labels()


	#Create dataset to train the NLP model
	def make_train_dataset(self,IQAs):
		#TODO: Fazer
		path_temp = os.paht.join("temp","dataset_tain_NER.json")
		return


	def retrieve_Property_Labels(self):
		#Retrive all labels that can be represent a given property
		for labelItem in self.labels:
			propertyy = self.labels[labelItem]['property']
			if propertyy in ["http://www.w3.org/2004/02/skos/core#prefLabel","http://www.w3.org/2000/01/rdf-schema#label","http://purl.org/dc/elements/1.1/title"]:
				#Default labels properties in popular vocabularies
				self.labels[labelItem]['labels'] = ["nome","título","chamado","conhecido"]
			else:
				self.labels[labelItem]['labels'] = self.queryLabels(propertyy)


	def retrieve_NER_Labels(self):
		#Retrive all datatype properties used in knowledge base that will be used as labels to NER.
		sparql = SPARQLWrapper(self.endpoint)

		sparql.setQuery("""
		   PREFIX rdf:<http://www.w3.org/1999/02/22-rdf-syntax-ns#>
			SELECT DISTINCT ?class ?p FROM """+self.graph+""" WHERE{
				?s ?p ?o;
					rdf:type ?class.
				FILTER(isLiteral(?o) )
			}
		""")
		sparql.setReturnFormat(JSON)
		results = sparql.query().convert()
		labels = {}
		for result in results["results"]["bindings"]:
			if self.filter_label(result["class"]["value"],result["p"]["value"]):
				id_property = sc.uri_to_hash(result["class"]["value"]+result["p"]["value"])
				labels[id_property] = {'class':result["class"]["value"],'property':result["p"]["value"]}
		return labels

	@staticmethod
	def filter_label(classs,propertyy):
		discarted_prefix = ['http://www.w3.org/','http://www4.wiwiss.fu-berlin.de/']
		for prefix in discarted_prefix:
			if prefix in classs:
				return False

		discarted_property = ['http://www.w3.org/2000/01/rdf-schema#comment']
		for prefix in discarted_property:
			if prefix in propertyy:
				return False
		return True

	def queryLabels(self,propertyy):
		#Retrive all datatype properties used in knowledge base that will be used as labes to NER.
		sparql = SPARQLWrapper(self.endpoint)

		query = """
			PREFIX rdf:<http://www.w3.org/1999/02/22-rdf-syntax-ns#>
			PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
			SELECT DISTINCT ?label FROM """+self.graph+""" WHERE{
				<"""+propertyy+"""> rdfs:label ?label.
				FILTER( langMatches( lang(?label),"pt"))
			}
		"""
		# print(query)
		sparql.setQuery(query)
		sparql.setReturnFormat(JSON)
		results = sparql.query().convert()
		labels = []
		for result in results["results"]["bindings"]:
			label = result["label"]["value"]
			labels.append(label)
		return labels