from SPARQLWrapper import SPARQLWrapper, JSON
import ontology.Schema as sc

#Class to Retrive property's values used in NER from SPARQL endpoint
LIMIT = 10000
class Instances_Retriever():
	def __init__(self,url_endpoint,graph_name=""):
		self.url_endpoint = url_endpoint
		self.graph_name = graph_name
		if self.graph_name != "":
			self.graph_name = " FROM <{}> ".format(self.graph_name)
		self.instances = {} #Save values of instances. Used to prevent query a same property multiple times

	def retriver(self,classs,propertyy):
		#Retrive instances
		instance_id = sc.uri_to_hash(classs+propertyy)
		if instance_id in self.instances:
			#Instances already stored in memory
			# print("HIT {}@{}".format(propertyy,classs))
			return self.instances[instance_id]
		else:
			#Need query SPARQL endpoint to get instances
			self.instances[instance_id] = []
			number_instances = self.count_triples(classs,propertyy)
			# print("Found {}\tFAULT {}@{}".format(number_instances,propertyy,classs))
			if number_instances <= 0:
				self.instances[instance_id]
			offset = 0

			while offset <= number_instances:
				self.instances[instance_id]+= self.query_examples(classs,propertyy,offset)
				offset+= LIMIT
			return self.instances[instance_id]

			




##Utility functions
	def count_triples(self,classs,propertyy):
		sparql = SPARQLWrapper(self.url_endpoint)
		classs = classs.strip()
		propertyy = propertyy.strip()
		query = """
			PREFIX rdf:<http://www.w3.org/1999/02/22-rdf-syntax-ns#>
			PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
			SELECT (count(DISTINCT ?val) as ?count_t) """+self.graph_name+""" WHERE{
				_:s a <"""+classs+""">;
					<"""+propertyy+"""> ?val_raw.
				BIND(LCASE(SUBSTR(str(?val_raw),1,1000)) as ?val)
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
		#Get values from properties in knowledge graph
		sparql = SPARQLWrapper(self.url_endpoint)
		classs = classs.strip()
		propertyy = propertyy.strip()

		limit = LIMIT

		query = """
			PREFIX rdf:<http://www.w3.org/1999/02/22-rdf-syntax-ns#>
			PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
			SELECT ?val
			WHERE{
				{
					SELECT DISTINCT ?val """+self.graph_name+""" WHERE{
						_:s a <"""+classs+""">;
							<"""+propertyy+"""> ?val_raw.
						BIND(LCASE(SUBSTR(str(?val_raw),1,1000)) as ?val)
					}ORDER BY ?val
				}
			}
			LIMIT """+str(limit)+"""
			OFFSET """+str(offset)+"""
		"""
		# print(query)
		sparql.setQuery(query)
		sparql.setReturnFormat(JSON)
		results = sparql.query().convert()

		values = []

		for result in results["results"]["bindings"]:
			values.append(result["val"]["value"].strip())

		return values