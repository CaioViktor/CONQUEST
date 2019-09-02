from __future__ import unicode_literals, print_function
from SPARQLWrapper import SPARQLWrapper, JSON
import os
import ontology.Schema as sc
import plac
import random
from pathlib import Path
import spacy
from spacy.util import minibatch, compounding




#Train Named Entity Recognition to recognize class properties values in senteces. It's values will be used in Context Variables
#Class to model in Brazilian portuguese
class NER_Trainer():
	def __init__(self,classIndex,endpoint,graph,nlp,fulldata=True,n_iter=100,limit=10000,limit_not_full = 10):
		self.classIndex = classIndex
		self.endpoint = endpoint
		self.graph = graph
		self.nlp = nlp
		self.labels = self.retrieve_NER_Labels()
		self.retrieve_Property_Labels()
		self.fulldata = fulldata
		self.LIMIT = limit
		self.n_iter = n_iter
		if not fulldata:
			self.LIMIT = limit_not_full



	def retrieve_NER_Labels(self):
		#Retrive all datatype properties used in knowledge base that will be used as labels to NER.
		#Train NER only to strings? Maybe Train to numbers and date using external data
		sparql = SPARQLWrapper(self.endpoint)

		sparql.setQuery("""
			PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
		   	PREFIX rdf:<http://www.w3.org/1999/02/22-rdf-syntax-ns#>
			SELECT DISTINCT ?class ?p FROM """+self.graph+""" WHERE{
				?s ?p ?o;
					rdf:type ?class.
				FILTER(isLiteral(?o) && !isNumeric(?o))
			}
		""")
		sparql.setReturnFormat(JSON)
		results = sparql.query().convert()
		labels = {}
		for result in results["results"]["bindings"]:
			if self.filter_label(result["class"]["value"],result["p"]["value"]):
				# print("Formando uri:\n{}".format(result["class"]["value"]+result["p"]["value"]))
				id_property = sc.uri_to_hash(result["class"]["value"]+result["p"]["value"])
				labels[id_property] = {'class':result["class"]["value"],'property':result["p"]["value"],'id':id_property}

		#Filtering properties in sub-classes, when these already apear in its super-classes.
		# print(labels)
		labels_return = {}
		for label in labels:
			is_valid = True
			classs = labels[label]['class']
			propertyy = labels[label]['property']

			id_class = sc.uri_to_hash(classs)
			if id_class in self.classIndex and 'super_classes' in self.classIndex[id_class]:
				for super_class in self.classIndex[id_class]['super_classes']:
					super_class_uri = super_class.n3()[1:-1]#Get URI without "<",">"

					if super_class_uri != classs:
						# print("Pai:\n{}".format(super_class_uri+propertyy))
						super_class_label = sc.uri_to_hash(super_class_uri+propertyy)
						if super_class_label in labels:
							# print("{}:{} \t {}:{}".format(classs.split("/")[-1],propertyy.split("/")[-1],super_class_uri.split("/")[-1],propertyy.split("/")[-1]))
							is_valid = False
							continue
			if is_valid:
				labels_return[label] = labels[label]
		# print("\n\n\n")
		# print(labels_return)
		return labels_return

	
	def retrieve_Property_Labels(self):
		#Retrive all datatype properties labels used in knowledge.
		for labelItem in self.labels:
			propertyy = self.labels[labelItem]['property']
			if propertyy in ["http://www.w3.org/2004/02/skos/core#prefLabel","http://www.w3.org/2000/01/rdf-schema#label","http://purl.org/dc/elements/1.1/title"]:
				#Default labels properties in popular vocabularies
				self.labels[labelItem]['labels'] = ["nome","título","chamado","conhecido"]
			else:
				self.labels[labelItem]['labels'] = self.queryLabels(propertyy)

	def queryLabels(self,propertyy):
		#Retrive all labels that can be represent a given property
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



	def train_NER(self,IQAs):
	#Create dataset to train the NLP model
		#make dataset
		self.add_labels_to_nlp()
		train_data = []
		i = 1
		for label_class in self.labels:
			print("{}/{}".format(str(i),str(len(self.labels))))
			self.get_train_to_label(self.labels[label_class],train_data)
			i+=1
		#end dataset
		#Train model
		print("\n\n\n\n-----------------TRAINING MODEL-----------------")
		print("\ttamanho dataset:{}".format(len(train_data)))
		# print("\tExemplo:{}".format(train_data[0]))
		self.train_model(train_data)
		return

	def get_train_to_label(self,label_class,train_data):
		#write examples for a label to dataset
		count_t = self.count_triples(label_class['class'],label_class['property'])
		print("{}:{}:\t{}".format(label_class['class'].split("/")[-1],label_class['property'].split("/")[-1],count_t))
		offset= 0

		if not self.fulldata:
			self.query_examples(label_class,offset,train_data)
			return
		while offset <= count_t:
			print("\t{}/{}".format(str(offset),str(count_t)))
			#Get train data
			self.query_examples(label_class,offset,train_data)
			
			offset+= self.LIMIT


	def query_examples(self,label_class,offset,train_data):
		
		classs = label_class['class']
		propertyy = label_class['property']
		id_property = label_class['id']
		labels = label_class['labels']

		#Get values from properties in knowledge graph
		sparql = SPARQLWrapper(self.endpoint)

		query = """
			PREFIX rdf:<http://www.w3.org/1999/02/22-rdf-syntax-ns#>
			PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
			SELECT ?val
			WHERE{
				{
					SELECT ?val FROM """+self.graph+""" WHERE{
						{
							_:s a <"""+classs+""">;
								<"""+propertyy+"""> ?val_raw.
								BIND(LCASE(SUBSTR(str(?val_raw),1,1000)) as ?val)
						}UNION{
							_:s rdf:type/rdfs:subClassOf+ <"""+classs+""">;
								<"""+propertyy+"""> ?val_raw.
								BIND(LCASE(SUBSTR(str(?val_raw),1,0000)) as ?val)
						}
					}ORDER BY ?val
				}
			}
			LIMIT """+str(self.LIMIT)+"""
			OFFSET """+str(offset)+"""
		"""
		# print(query)
		sparql.setQuery(query)
		sparql.setReturnFormat(JSON)
		results = sparql.query().convert()

		for result in results["results"]["bindings"]:
			val = result["val"]["value"].strip()

			if val != "":
				for label in labels:
					#TODO: Examples
					string = "{} {}".format(label,val)
					train_data.append( self.create_example(string,str(val),id_property))

				train_data.append( self.create_example(str(val),str(val),id_property))
			




	def add_labels_to_nlp(self):
		ner = None
		if 'ner' not in self.nlp.pipe_names:
			ner = self.nlp.create_pipe('ner')
			self.nlp.add_pipe(ner)
		else:
			ner = self.nlp.get_pipe('ner')

		for label in self.labels:
			if label not in self.nlp.entity.labels:
				ner.add_label(label)

	def train_model(self,TRAIN_DATA):
		#Train model
		optimizer = self.nlp.entity.create_optimizer()
		other_pipes = [pipe for pipe in self.nlp.pipe_names if pipe != 'ner']
		with self.nlp.disable_pipes(*other_pipes):  # only train NER
			for itn in range(self.n_iter):
				print("Train iteration:{}\n".format(itn))
				random.shuffle(TRAIN_DATA)
				losses = {}
				# batch up the examples using spaCy's minibatch
				batches = minibatch(TRAIN_DATA, size=compounding(4., 32., 1.001))
				for batch in batches:
					texts, annotations = zip(*batch) 
					# Updating the weights
					self.nlp.update(texts, annotations, sgd=optimizer, drop=0.35, losses=losses)
				print('Losses', losses)

		#TODO: Test an save model
		 # test the trained model
		# for text, _ in TRAIN_DATA:
		# 	doc = self.nlp(text)
		# 	print("Entities", [(ent.text, ent.label_) for ent in doc.ents])
		# 	print("Tokens", [(t.text, t.ent_type_, t.ent_iob) for t in doc])

##Utility functions
	def count_triples(self,classs,propertyy):
		sparql = SPARQLWrapper(self.endpoint)

		query = """
			PREFIX rdf:<http://www.w3.org/1999/02/22-rdf-syntax-ns#>
			PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
			SELECT count(DISTINCT ?val) as ?count_t FROM """+self.graph+""" WHERE{
				{
					_:s a <"""+classs+""">;
						<"""+propertyy+"""> ?val_raw.
						BIND(LCASE(SUBSTR(str(?val_raw),1,1000)) as ?val)
				}UNION{
					_:s rdf:type/rdfs:subClassOf+ <"""+classs+""">;
						<"""+propertyy+"""> ?val_raw.
						BIND(LCASE(SUBSTR(str(?val_raw),1,1000)) as ?val)
				}
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

	@staticmethod
	def create_example(string,entity,label):
		string = string.strip()
		entity = entity.strip()
		entities_array = []
		if entity in string:
			initial_index = string.index(entity)
			final_index = initial_index + len(entity)
			entities_array.append((initial_index,final_index,label))
		return (string,{'entities':entities_array})