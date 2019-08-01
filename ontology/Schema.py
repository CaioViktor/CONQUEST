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

#Consts definitions
URI = 0
LITERAL = 1
#end consts definitions


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
def parser_sparql(query_string,schema):
	query_object = processor.prepareQuery(query_string)
	# print(query_object.algebra)
	# print("\n\n")
	return parser_algebra(query_object.algebra,schema)


# #vars_query's struct
# {
# 	'hash_id':{
# 		'name': '?var_name',
# 		'type' : (URI|LITERAL),
# 		'class': Set(URIRef(Class)),
# 		'context': [(subject,predicate,object)], #Where current var is replaced by None
# 		'filter': ?
# 		'only_optional': True|False
# 	},
# }

def new_var(name,typee,classs,context=None,filterr=None,only_optional=False):
	if context == None:
		context = []
	else:
		context = [context]
	if not isinstance(classs,list):
		classs = [classs]
	return {'name':name,'type':typee,'class':set(classs),'context':context,'filter':filterr,'only_optional':only_optional}

#parser utilities functions
def parser_algebra(algebra,schema,depth=0,vars_query={}):
	for element in algebra:
		children = algebra[element]
		if re.search("^p\d*",element):
			#print("depth:{}- {}".format(depth,element))
			parser_algebra(children,schema,depth+1,vars_query)
		elif element == "expr":
			parser_expr(children,vars_query)
		elif element == "triples":
			parser_triples(children,schema,vars_query)
	return vars_query


def parser_expr(expr,depth=0,vars_query={}):
	print("Expressão de pofundidade {}:\n{}".format(depth,expr))
	#expr.name tem o tipo da expressão
	#TODO: interpretar expressões
	return vars_query

def parser_triples(triples,schema,vars_query={}):
	for triple in triples:
		subject,predicate,objectt = triple
		if predicate == RDF.type and isinstance(subject,Variable):
			#is a variable type declaration
			id_var = uri_to_hash(subject)
			if id_var in vars_query:
				#var already parsed
				vars_query[id_var]['class'].update([objectt])
			else:
				#new var found
				name = subject.n3().replace("?","")
				typee = URI
				vars_query[id_var] = new_var(name,typee,objectt)
			#print("declarou {} como um {}".format(subject.n3(),objectt))
		elif isinstance(subject,Variable) or isinstance(objectt,Variable):
			#subject or object are variables, so its types may be infered by property
			id_hash_property = uri_to_hash(predicate)

			#get iformation about the predicate if it is known
			predicate_info = None		
			predicate_type = None
			if id_hash_property in schema[0]:
				#Predicate is a rdf:Property
				predicate_info = schema[0][id_hash_property]
				predicate_type = 0
			elif id_hash_property in schema[1]:
				#Predicate is a owl:ObjectProperty
				predicate_info = schema[1][id_hash_property]
				predicate_type = 1
			elif id_hash_property in schema[2]:
				#Predicate is a owl:DatatypeProperty
				predicate_info = schema[2][id_hash_property]
				predicate_type = 2



			domains = []
			ranges = []
			if not predicate_info == None:
				#Known Predicate
				domains = predicate_info['domains']
				ranges = predicate_info['ranges']
				# print("Propriedade {} do tipo: {} já conhecida.\nDomains:{}\nRanges:{}".format(predicate,predicate_type,domains,ranges))
			

			if isinstance(subject,Variable):
				#Triple's subject is a variable
				#all subject must be a URI, not a LITERAL
				id_hash_subject = uri_to_hash(subject)
				if id_hash_subject in vars_query:
					#var already parsed
					vars_query[id_hash_subject]['class'].update(domains) 
					vars_query[id_hash_subject]['context'].append(triple)
				else:
					#new var found
					name = subject.n3().replace("?","")
					typee = URI
					vars_query[id_hash_subject] = new_var(name,typee,domains,context=(triple))


			if isinstance(objectt,Variable):
				#Triple's object is a variable
				id_hash_object = uri_to_hash(objectt)
				if id_hash_object in vars_query:
					#var already parsed
					vars_query[id_hash_object]['class'].update(ranges) 
					vars_query[id_hash_object]['context'].append(triple)
					vars_query[id_hash_object]['type'] = LITERAL
				else:
					#new var found
					name = objectt.n3().replace("?","")
					typee = URI
					if predicate_type == 2:
						typee = LITERAL
					vars_query[id_hash_object] = new_var(name,typee,domains,context=(triple))

	return vars_query