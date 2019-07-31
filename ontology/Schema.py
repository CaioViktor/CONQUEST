import os
from rdflib import Graph
from rdflib.util import guess_format
import hashlib
from rdflib.resource import Resource
import re
import rdflib.plugins.sparql.processor as processor
from rdflib import OWL, RDF, RDFS, OWL, XSD,URIRef,BNode,Variable
from rdflib.namespace import Namespace

DC = Namespace('http://purl.org/dc/elements/1.1/')
DCTERMS = Namespace('http://purl.org/dc/terms/')



#Load Graph
def getGraph(file,path="configurations/"):
	file_path = os.path.join(path,file)
	
	g = Graph()
	# print(guess_format(file_path))
	g.parse(file_path,format=guess_format(file_path))
	# g.parse(file_path,format="turtle")
	return g


def get_Resource(graph,uri):
	if type(uri) is str:
		uri = URIRef(uri)
	return Resource(graph,uri)


def uri_to_hash(uri):
	return hashlib.md5(str(uri).encode('utf-8')).hexdigest()

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


		id_hash = uri_to_hash(prop)
		properties[id_hash] = {'uri':prop,'domains':domains,'ranges':ranges,'labels':labels,'comments':comments}
		#print("{}\n\tDomain:{}\n\tRange:{}\n\tLabels:{}\n\tComments:{}".format(prop,domains,ranges,labels,comments))
	return properties


def load_properties_index(schema):

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



#Get all information for make the index of a class
def get_info_class(classe,schema):
	info = {'uri':classe}


	#get labels
	labels = []
	for label in schema.preferredLabel(classe):
		labels.append(label[1])
	info['labels'] = labels


	#get own properties
	properties = []
	for propertyO in schema.subjects(RDFS.domain,classe):
		properties.append(propertyO)
	info['properties'] = properties


	#get incident properties
	incident_properties = []
	for propertyO in schema.subjects(RDFS.range,classe):
		incident_properties.append(propertyO)
	info['incident_properties'] = incident_properties


	#get super-classes
	super_classes_list = get_Resource(schema,classe).transitive_objects(RDFS.subClassOf)
	super_classes = []
	for super_class in super_classes_list:
		if not isinstance(super_class.identifier,BNode) :
			super_classes.append(super_class.identifier)
	info['super_classes'] = super_classes



	#get sub-classes
	sub_classes_list = get_Resource(schema,classe).transitive_subjects(RDFS.subClassOf)
	sub_classes = []
	for sub_class in sub_classes_list:
		if not isinstance(sub_class.identifier,BNode) :
			sub_classes.append(sub_class.identifier)
	info['sub_classes'] = sub_classes
	


	return info

def load_classes_index(schema):
	classes = {}
	#Get OWL:Classes
	for classe in schema.subjects(RDF.type,OWL.Class):
		uri = uri_to_hash(classe)
		classes[uri] = get_info_class(classe,schema)

	#Get RDFS:Classes
	for classe in schema.subjects(RDF.type,RDFS.Class):
		uri = uri_to_hash(classe)
		classes[uri] = get_info_class(classe,schema)


	return classes

#parser sparql query to interpretate context variables meaning
def parser_sparql(query_string):
	query_object = processor.prepareQuery(query_string)
	# print(query_object.algebra)
	# print("\n\n")
	parser_algebra(query_object.algebra)

#parser utilities functions
def parser_algebra(algebra,depth=0):
	for element in algebra:
		children = algebra[element]
		if re.search("^p\d*",element):
			print("depth:{}- {}".format(depth,element))
			parser_algebra(children,depth+1)
		elif element == "expr":
			parser_expr(children)
		elif element == "triples":
			parser_triples(children)


def parser_expr(expr,depth=0):
	print("Expressão de pofundidade {}:\n{}".format(depth,expr))
	#expr.name tem o tipo da expressão
	#TODO: interpretar expressões

def parser_triples(triples):
	for triple in triples:
		subject,predicate,objectt = triple
		if predicate == RDF.type and isinstance(subject,Variable):
			#is a variable type declaration

			print("declarou {} como um {}".format(subject.n3(),objectt))
		elif isinstance(subject,Variable) or isinstance(objectt,Variable):
			#subject or object are variables, so its types may be infered by property
			print("S:{},\tP:{},\tO:{}".format(subject,predicate,objectt))
			print("\n")
			if isinstance(subject,Variable):
				#TODO: consultar o indice
				return 0
			if isinstance(objectt,Variable):
				#TODO: consultar o indice
				return 0
		#TODO: Verificar casos de CVs