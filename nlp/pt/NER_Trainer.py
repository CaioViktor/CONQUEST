from SPARQLWrapper import SPARQLWrapper, JSON
import os
import ontology.Schema as sc

LIMIT = 10000

#Train Named Entity Recognition to recognize class properties values in senteces. It's values will be used in Context Variables
#Class to model in Brazilian portuguese
class NER_Trainer():
	def __init__(self,endpoint,graph,nlp):
		self.endpoint = endpoint
		self.graph = graph
		self.nlp = nlp
		self.labels = self.retrieve_NER_Labels()
		self.retrieve_Property_Labels()


	def add_labels_to_nlp(self):
		ner = None
		if 'ner' not in self.nlp.pipe_names:
			ner = self.nlp.create_pipe('ner')
			self.nlp.add_pipe(ner)
		else:
			ner = self.nlp.get_pipe('ner')

		for label in self.labels:
			if label not in self.nlp.entity.labels
			ner.add_label(label)


	def train_dataset(self,IQAs):
	#Create dataset to train the NLP model
		#make dataset
		self.add_labels_to_nlp()
		i = 1
		for label_class in self.labels:
			print("{}/{}".format(str(i),str(len(self.labels))))
			self.train_to_label(self.labels[label_class])
			i+=1
		#end dataset

		return

	def train_to_label(self,label_class):
		#write examples for a label to dataset
		count_t = self.count_triples(label_class['class'],label_class['property'])
		offset= 0
		print(count_t)
		while offset <= count_t:
			print("\t{}/{}".format(str(offset),str(count_t)))
			train_data = self.query_examples(label_class['class'],label_class['property'],offset)


			#TODO: Train model
			offset+= LIMIT
		


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


##Utility functions
	def count_triples(self,classs,propertyy):
		sparql = SPARQLWrapper(self.endpoint)

		query = """
			PREFIX rdf:<http://www.w3.org/1999/02/22-rdf-syntax-ns#>
			PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
			SELECT DISTINCT count(*) as ?count_t FROM """+self.graph+""" WHERE{
				?s a <"""+classs+""">;
					<"""+propertyy+"""> ?val.
			}
		"""
		# print(query)
		sparql.setQuery(query)
		sparql.setReturnFormat(JSON)
		results = sparql.query().convert()
		count_t = 0
		for result in results["results"]["bindings"]:
			count_t = int(result["count_t"]["value"])
		return count_t

	def query_examples(self,classs,propertyy,offset):
		sparql = SPARQLWrapper(self.endpoint)

		query = """
			PREFIX rdf:<http://www.w3.org/1999/02/22-rdf-syntax-ns#>
			PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
			SELECT ?s ?val
			WHERE{
				{
					SELECT DISTINCT ?s ?val FROM """+self.graph+""" WHERE{
						?s a <"""+classs+""">;
							<"""+propertyy+"""> ?val.
					}ORDER BY ?s ?val
				}
			}
			LIMIT """+str(LIMIT)+"""
			OFFSET """+str(offset)+"""
		"""
		# print(query)
		sparql.setQuery(query)
		sparql.setReturnFormat(JSON)
		results = sparql.query().convert()
		train_data = []
		for result in results["results"]["bindings"]:
			s = result["s"]["value"]
			val = result["val"]["value"]


			#TODO: Examples
			example = ""
			label_data = (0,0,"")
			train_data.append( (example , [label_data]))
			
		return train_data