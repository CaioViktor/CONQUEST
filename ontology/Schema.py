import os
from rdflib import Graph
from rdflib.util import guess_format
import hashlib
from rdflib import OWL, RDF, RDFS, OWL, XSD
from rdflib.namespace import Namespace
DC = Namespace('http://purl.org/dc/elements/1.1/')
DCTERMS = Namespace('http://purl.org/dc/terms/')

#Load Graph
def getGraph(path):
	g = Graph()
	# print(guess_format(path))
	g.parse(path,format=guess_format(path))
	# g.parse(path,format="turtle")
	return g


def get_range_damain(schema,types=RDF.Property):
	properties = {}
	for prop in schema.subjects( RDF.type, types):
		domains = []
		for domain in schema.objects(prop,RDFS.domain):
			domains.append(domain)

		ranges = []
		for rangep in schema.objects(prop,RDFS.range):
			ranges.append(rangep)

		comments = []
		for comment in schema.objects(prop,RDFS.comment):
			comments.append(comment)

		labels = []
		for label in schema.preferredLabel(prop):
			labels.append(label[1])

		id_hash = hashlib.md5(str(prop).encode('utf-8')).hexdigest()
		properties[id_hash] = {'uri':prop,'domains':domains,'ranges':ranges,'labels':labels,'comments':comments}
		print("{}\n\tDomain:{}\n\tRange:{}\n\tLabels:{}\n\tComments:{}".format(prop,domains,ranges,labels,comments))
	return properties


def load_properties_index(file,path="configurations/"):
	file_path = os.path.join(path,file)
	schema = getGraph(file_path)

	# print("Get properties")
	#Get properties
	p = get_range_damain(schema)

	#print("Get ObjectProperty")
	#Get ObjectProperty
	op = get_range_damain(schema,OWL.ObjectProperty)

	#print("Get DatatypeProperty")
	#Get DatatypeProperty
	dtp = get_range_damain(schema,OWL.DatatypeProperty)
	return p,op,dtp