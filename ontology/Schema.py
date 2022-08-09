from rdflib import Graph
from rdflib.util import guess_format
import hashlib
from rdflib.resource import Resource
from rdflib.plugins.sparql.parserutils import Expr
import re
import rdflib.plugins.sparql.processor as processor
from rdflib import OWL, RDF, RDFS, OWL, XSD,URIRef,BNode,Variable,Literal
from rdflib.namespace import Namespace
from regex import P

DC = Namespace('http://purl.org/dc/elements/1.1/')
DCTERMS = Namespace('http://purl.org/dc/terms/')
SKOS = Namespace('http://www.w3.org/2004/02/skos/core#')
CMO = Namespace('https://github.com/CaioViktor/CONQUEST/tree/master/ontology/ConquestMarkupOntology#')

#Consts definitions
URI = 0
LITERAL = 1
#end consts definitions



#Load Graph
def getGraph(file_path):
	
	g = Graph()
	# print(guess_format(file_path))
	g.parse(file_path,format=guess_format(file_path))
	# g.parse(file_path,format="turtle")
	return g


def get_Resource(graph,uri):
	if type(uri) is str:
		uri = URIRef(uri)
	return Resource(graph,uri)

def normalize_datatype(datatype_xsd):
	if datatype_xsd == XSD.int or datatype_xsd == XSD.decimal:
		return XSD.integer
	if datatype_xsd == XSD.float or datatype_xsd == XSD.double:
		return XSD.double
	if datatype_xsd == XSD.date:
		return XSD.dateTime
	return datatype_xsd

def get_range_domain(schema,types=RDF.Property):
	properties = {}
	for prop in schema.subjects( RDF.type, types):
		domains = []
		ranges = []
		for domain in schema.objects(prop,RDFS.domain):
			domains.append(normalize_datatype(domain))
		if str(prop) not in ['http://www.w3.org/2000/01/rdf-schema#label','http://purl.org/dc/elements/1.1/title','http://www.w3.org/2004/02/skos/core#prefLabel']:
			query = f"""
			SELECT DISTINCT ?c1
			WHERE {{
				?c1 rdfs:subClassOf* ?cn.
				?cn rdf:type owl:Restriction;
					owl:onProperty <{prop}>;
					owl:someValuesFrom|owl:allValuesFrom ?c.
				FILTER(!isBlank(?c1))
			}}"""
			qres = schema.query(query)
			if len(qres) > 0:
				for row in qres:
					uri_ref = URIRef(row[0])
					if not uri_ref in domains:
						domains.append(uri_ref)

		for rangep in schema.objects(prop,RDFS.range):
			ranges.append(normalize_datatype(rangep))
		query = f"""
		SELECT DISTINCT ?c
		WHERE {{
			?c1 rdfs:subClassOf* ?cn.
			?cn rdf:type owl:Restriction;
				owl:onProperty <{prop}>;
				owl:someValuesFrom|owl:allValuesFrom ?c.
			FILTER(!isBlank(?c))
		}}"""
		qres = schema.query(query)
		if len(qres) > 0:
			for row in qres:
				uri_ref = URIRef(row[0])
				if not uri_ref in ranges:
					ranges.append(uri_ref)
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
	p = get_range_domain(schema)

	#print("Get ObjectProperty")
	#Get ObjectProperty
	op = get_range_domain(schema,OWL.ObjectProperty)

	#print("Get DatatypeProperty")
	#Get DatatypeProperty
	dtp = get_range_domain(schema,OWL.DatatypeProperty)
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
	query = f"""
		SELECT DISTINCT ?p
		WHERE {{
			<{classe}> rdfs:subClassOf* ?cn.
			?cn rdf:type owl:Restriction;
				owl:onProperty ?p;
				owl:someValuesFrom|owl:allValuesFrom ?c.
		}}"""
	qres = schema.query(query)
	if len(qres) > 0:
		for row in qres:
			uri_ref = URIRef(row[0])
			if not uri_ref in info['properties'] and str(uri_ref) not in ['http://www.w3.org/2000/01/rdf-schema#label','http://purl.org/dc/elements/1.1/title','http://www.w3.org/2004/02/skos/core#prefLabel']:
				info['properties'].append(uri_ref)


	#get incident properties
	incident_properties = []
	for propertyO in schema.subjects(RDFS.range,classe):
		incident_properties.append(propertyO)
	info['incident_properties'] = incident_properties
	query = f"""
		SELECT DISTINCT ?p
		WHERE {{
			?c rdfs:subClassOf* ?cn.
			?cn rdf:type owl:Restriction;
				owl:onProperty ?p;
				owl:someValuesFrom|owl:allValuesFrom  <{classe}>.
		}}"""
	qres = schema.query(query)
	if len(qres) > 0:
		for row in qres:
			uri_ref = URIRef(row[0])
			if not uri_ref in info['incident_properties'] and str(uri_ref) not in ['http://www.w3.org/2000/01/rdf-schema#label','http://purl.org/dc/elements/1.1/title','http://www.w3.org/2004/02/skos/core#prefLabel']:
				info['incident_properties'].append(uri_ref)

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
	

	#get Instances Identifier
	if (classe,RDF.type,CMO.RecognizableClass) in schema:
		identifiers = set([RDFS.label,SKOS.prefLabel,DC.title])
		for identifier in schema.objects(classe,CMO.entityIdentifier):
			identifiers.add(identifier)
		info['identifiers'] =list(identifiers)


	#get comments and definitions
	comments = []
	for comment in schema.objects(classe,RDFS.comment):
		comments.append(comment)
	info['comments']  = comments


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
# 		'context': Set((subject,predicate,object)), #Where current var is replaced by None
# 	},
# }

def new_var(name,typee,classs=list(),context=None,class_is_explicit=False):
	if context == None:
		context = []
	else:
		context = [context]
	if not isinstance(classs,list):
		classs = [classs]
	return {'name':name,'type':typee,'class':set(classs),'context':context,'class_is_explicit':class_is_explicit}

#parser utilities functions
def parser_algebra(algebra,schema,depth=0,vars_query={}):
	expr = None
	for element in algebra:
		children = algebra[element]
		if re.search("^p\d*",element):
			#print("depth:{}- {}".format(depth,element))
			# print(dir(children))
			parser_algebra(children,schema,depth+1,vars_query)
		elif element == "expr":
			#Postpone expressions evaluation
			expr = children
		elif element == "triples":
			parser_triples(children,schema,vars_query)

	#Evalute expression only after triples evaluation
	if expr != None:		
		#Parse expressions
		parser_expr(expr,vars_query)

	return vars_query



#Parse expression for both, filters and binds
def parser_expr(expr,vars_query,vars_in_expr=list(),depth=0):
	unary_built_in_function = set(['Builtin_ABS','Builtin_BNODE','Builtin_BOUND','Builtin_CEIL','Builtin_DATATYPE','Builtin_DAY','Builtin_HOURS','Builtin_MINUTES','Builtin_MONTH','Builtin_SECONDS','Builtin_YEAR','Builtin_TIMEZONE','Builtin_FLOOR','Builtin_IRI','Builtin_LANG','Builtin_LCASE','Builtin_UCASE','Builtin_ROUND','Builtin_STR','Builtin_STRLEN','Builtin_isIRI','Builtin_isBLANK','Builtin_isLITERAL','Builtin_isNUMERIC'])
	if(isinstance(expr,Expr)):
		id_parent = uri_to_hash(expr)
		
		#Branch node
		if(expr.name == "RelationalExpression"):
			#Binary expression
			
			#left node expression
			left = parser_expr(expr['expr'],vars_query,vars_in_expr,depth+1)
			#Operation,
			op = expr['op']
			#right node expression
			right = parser_expr(expr['other'],vars_query,vars_in_expr,depth+1)

			#infers types 
			if not op == "!=":
				if left in vars_query or right in vars_query:
					if left in vars_query and right in vars_query:
						#Both are variables
						#Update classes
						if not vars_query[left]['class_is_explicit']:
							# print("foi 1 L ",vars_query[left]['name'])
							vars_query[left]['class'].update(vars_query[right]['class'])
						if not vars_query[right]['class_is_explicit']:
							# print("foi 1 R ",vars_query[left]['name'])
							vars_query[right]['class'].update(vars_query[left]['class'])
						#update context
						
						update_context(vars_query[left]['context'],(expr['expr'],expr['op'],expr['other']))
						
						update_context(vars_query[right]['context'],(expr['expr'],expr['op'],expr['other']))
					elif left not in vars_query:
						#Only right is a variable
						if (isinstance(expr['expr'],Literal)):
							#left is literal
							# print("foi 2",vars_query[right]['name'])
							datatype = expr['expr'].datatype
							vars_query[right]['class'].update([datatype])
							vars_query[right]['type'] = LITERAL
					else:
						#Only left is a variable
						if (isinstance(expr['other'],Literal)):
							#right is literal
							# print("foi 3",vars_query[left]['name'])
							datatype = expr['other'].datatype
							vars_query[left]['class'].update([datatype])
							vars_query[left]['type'] = LITERAL

		elif(expr.name == "ConditionalAndExpression"):
			#and: &&

			#first node
			left = parser_expr(expr['expr'],vars_query,vars_in_expr,depth+1)
			
			for node in expr['other']:
				#remainder nodes
				right = parser_expr(node,vars_query,vars_in_expr,depth+1)
				#Do something?

				#Did
				left = right

		elif(expr.name == "ConditionalOrExpression"):
			#or: ||
			
			#first node
			left = parser_expr(expr['expr'],vars_query,vars_in_expr,depth+1)
			
			for node in expr['other']:
				#remainder nodes
				right = parser_expr(node,vars_query,vars_in_expr,depth+1)
				#Do something?

				#Did
				left = right

		elif(expr.name == "UnaryNot"):
			#not: !
			node = parser_expr(expr['expr'],vars_query,vars_in_expr,depth+1)

		#Math operations
		elif(expr.name == "AdditiveExpression" or expr.name == "MultiplicativeExpression"):
			#Operation,#+,-,*,/
			
			#left node expression
			left = parser_expr(expr['expr'],vars_query,vars_in_expr,depth+1)
			
			i = 0
			for node in expr['other']:
				#remainder nodes
				right = parser_expr(node,vars_query,vars_in_expr,depth+1)
				op = expr['op'][i]

				#infers types
				if left != None and left in vars_query:
					# print("foi 4",vars_query[left]['name'])
					vars_query[left]['class'].update([XSD.double])
					vars_query[left]['type'] = LITERAL
					#update context
					
					update_context(vars_query[left]['context'],(left,op,right))


				if right != None and right in vars_query:
					# print("foi 5",vars_query[right]['name'])
					vars_query[right]['class'].update([XSD.double])
					vars_query[right]['type'] = LITERAL
					#update context
					
					update_context(vars_query[left]['context'],(left,op,right))

				left = right
				i+=1			
		elif(expr.name == "Builtin_CONCAT"):
			#CONCAT strings function
			for exp in expr['arg']:
				node = parser_expr(exp,vars_query,vars_in_expr,depth+1)
				

		elif(expr.name == "Builtin_CONTAINS" or expr.name == "Builtin_STRAFTER" or expr.name == "Builtin_STRBEFORE" or expr.name == "Builtin_STRENDS" or expr.name == "Builtin_STRSTARTS"):
			#CONTAINS ,STRAFTER, STRBEFORE strings functions

			#full - string
			string = parser_expr(expr['arg1'],vars_query,vars_in_expr,depth+1)

			#sub-string searched - string
			sub_string = parser_expr(expr['arg2'],vars_query,vars_in_expr,depth+1)

			# infers type
			if string != None and string in vars_query:
				# print("foi 6",vars_query[string]['name'])
				vars_query[string]['class'].update([XSD.string])
				vars_query[string]['type'] = LITERAL
				#update context
				if sub_string in vars_query:
					
					update_context(vars_query[string]['context'],(expr['arg1'],expr.name,expr['arg2']))
				else:
					
					update_context(vars_query[string]['context'],(expr['arg1'],expr.name,sub_string))

			if sub_string != None and sub_string in vars_query:
				# print("foi 7",vars_query[sub_string]['name'])
				vars_query[sub_string]['class'].update([XSD.string])
				vars_query[sub_string]['type'] = LITERAL
				#update context
				if  string in vars_query:
					
					update_context(vars_query[sub_string]['context'],(expr['arg1'],expr.name,expr['arg2']))
				else:
					
					update_context(vars_query[sub_string]['context'],(string,expr.name,expr['arg2']))

		elif(expr.name == "Builtin_LANGMATCHES" or expr.name == "Builtin_STRLANG"):
			#langmatches, STRLANG strings functions

			#string
			string = parser_expr(expr['arg1'],vars_query,vars_in_expr,depth+1)

			#language code
			lang = parser_expr(expr['arg2'],vars_query,vars_in_expr,depth+1)

			# infers type
			if string != None and string in vars_query:
				# print("foi 8",vars_query[string]['name'])
				vars_query[string]['class'].update([XSD.string])
				vars_query[string]['type'] = LITERAL
				#update context
				
				update_context(vars_query[string]['context'],(expr['arg1'],expr.name,expr['arg2']))

		elif(expr.name == "Builtin_REGEX"):
			#regex strings function

			#full-string
			text = parser_expr(expr['text'],vars_query,vars_in_expr,depth+1)

			#regex pattern
			pattern = parser_expr(expr['pattern'],vars_query,vars_in_expr,depth+1)

			#flags mode
			if 'flags' in expr:
				flags = parser_expr(expr['flags'],vars_query,vars_in_expr,depth+1)	

			# infers type
			if text != None and text in vars_query:
				# print("foi 9",vars_query[text]['name'])
				vars_query[text]['class'].update([XSD.string])
				vars_query[text]['type'] = LITERAL
				#update context
				if pattern in vars_query:
					
					update_context(vars_query[text]['context'],(expr['text'],expr.name,expr['pattern']))
				else:
					
					update_context(vars_query[text]['context'],(expr['text'],expr.name,pattern))

			if pattern != None and pattern in vars_query:
				# print("foi 10",vars_query[pattern]['name'])
				vars_query[pattern]['class'].update([XSD.string])
				vars_query[pattern]['type'] = LITERAL
				#update context
				if text in vars_query:
					
					update_context(vars_query[pattern]['context'],(expr['text'],expr.name,expr['pattern']))
				else:
					
					update_context(vars_query[pattern]['context'],(text,expr.name,expr['pattern']))

		elif(expr.name == "Builtin_REPLACE"):
			#replace strings function

			#full-string
			text = parser_expr(expr['arg'],vars_query,vars_in_expr,depth+1)

			#pattern to be replaced
			pattern = parser_expr(expr['pattern'],vars_query,vars_in_expr,depth+1)

			#string to be replace
			replacement = parser_expr(expr['replacement'],vars_query,vars_in_expr,depth+1)

			if 'flags' in expr:
				#flags mode
				flags = parser_expr(expr['flags'],vars_query,vars_in_expr,depth+1)	

			# infers type
			if text != None and text in vars_query:
				# print("foi 11",vars_query[left]['name'])
				vars_query[text]['class'].update([XSD.string])
				vars_query[text]['type'] = LITERAL
				#update context
				if pattern in vars_query:
					
					update_context(vars_query[text]['context'],(expr['arg'],expr.name,expr['pattern']))
				else:
					
					update_context(vars_query[text]['context'],(expr['arg'],expr.name,pattern))

			if pattern != None and pattern in vars_query:
				# print("foi 12",vars_query[pattern]['name'])
				vars_query[pattern]['class'].update([XSD.string])	
				vars_query[pattern]['type'] = LITERAL
				#update context
				if text in vars_query:
					
					update_context(vars_query[pattern]['context'],(expr['arg'],expr.name,expr['pattern']))
				else:
					
					update_context(vars_query[pattern]['context'],(text,expr.name,expr['pattern']))

			if replacement != None and replacement in vars_query:
				# print("foi 13",vars_query[replacement]['name'])
				vars_query[replacement]['class'].update([XSD.string])
				vars_query[replacement]['type'] = LITERAL
				#update context
				
				update_context(vars_query[replacement]['context'],(expr['arg'],expr.name,expr['pattern']))

		elif(expr.name == "Builtin_SUBSTR"):
			#substring strings function

			#full-string
			text = parser_expr(expr['arg'],vars_query,vars_in_expr,depth+1)

			#starting position
			index = parser_expr(expr['start'],vars_query,vars_in_expr,depth+1)

			if 'length' in expr:
				length = parser_expr(expr['length'],vars_query,vars_in_expr,depth+1)

			# infers type
			if text != None and text in vars_query:
				# print("foi 14",vars_query[text]['name'])
				vars_query[text]['class'].update([XSD.string])
				vars_query[text]['type'] = LITERAL
				#update context
				if index in vars_query:
					
					update_context(vars_query[text]['context'],(expr['arg'],expr.name,expr['start']))
				else:
					
					update_context(vars_query[text]['context'],(expr['arg'],expr.name,index))
			if index != None and index in vars_query:
				# print("foi 15",vars_query[index]['name'])
				vars_query[index]['class'].update([XSD.integer])
				vars_query[index]['type'] = LITERAL
				#update context
				if text in vars_query:
					
					update_context(vars_query[index]['context'],(expr['arg'],expr.name,expr['start']))
				else:
					
					update_context(vars_query[index]['context'],(text,expr.name,expr['start']))

		elif(expr.name == "Builtin_LANGMATCHES" or expr.name == "Builtin_STRLANG"):
			#langmatches, STRLANG strings functions
			#string
			term1 = parser_expr(expr['arg1'],vars_query,vars_in_expr,depth+1)

			#language code
			ter2 = parser_expr(expr['arg2'],vars_query,vars_in_expr,depth+1)

			# infers type
			if term1 != None and term1 in vars_query:
				# print("foi 16",vars_query[term1]['name'])
				vars_query[term1]['class'].update([XSD.string])
				vars_query[term1]['type'] = LITERAL
				#update context
				if ter2 in vars_query:
					
					update_context(vars_query[term1]['context'],(expr['arg1'],expr.name,expr['arg2']))
				else:
					
					update_context(vars_query[term1]['context'],(expr['arg1'],expr.name,ter2))

			if ter2 != None and ter2 in vars_query:
				# print("foi 17",vars_query[ter2]['name'])
				vars_query[ter2]['class'].update([XSD.string])
				vars_query[ter2]['type'] = LITERAL
				#update context
				if term1 in vars_query:
					
					update_context(vars_query[ter2]['context'],(expr['arg1'],expr.name,expr['arg2']))
				else:
					
					update_context(vars_query[ter2]['context'],(term1,expr.name,expr['arg2']))

		elif(expr.name == "Builtin_sameTerm"):
			#string
			term1 = parser_expr(expr['arg1'],vars_query,vars_in_expr,depth+1)

			#language code
			ter2 = parser_expr(expr['arg2'],vars_query,vars_in_expr,depth+1)

		#unary functions
		elif(expr.name in unary_built_in_function):
			arg = parser_expr(expr['arg'],vars_query,vars_in_expr,depth+1)
			#infers type
			if arg != None and arg in vars_query:
				if expr.name in ['Builtin_ABS','Builtin_CEIL','Builtin_FLOOR','Builtin_ROUND']:
					#Var is a decimal
					# print("foi 18",vars_query[arg]['name'])
					vars_query[arg]['class'].update([XSD.double])

				elif expr.name in ['Builtin_DAY','Builtin_HOURS','Builtin_MINUTES','Builtin_MONTH','Builtin_SECONDS','Builtin_YEAR','Builtin_TIMEZONE']:
					#Var is a #Var is a decimal
					# print("foi 19",vars_query[arg]['name'])
					vars_query[arg]['class'].update([XSD.dateTime])

				elif expr.name in ['Builtin_LANG','Builtin_LCASE','Builtin_UCASE','Builtin_STRLEN','Builtin_ENCODE_FOR_URI']:
					#Var is a #Var is a string
					# print("foi 20",vars_query[arg]['name'])
					vars_query[arg]['class'].update([XSD.string])

				#set type variable
				vars_query[arg]['type'] = LITERAL
				#update context
				
				update_context(vars_query[arg]['context'],(expr['arg'],expr.name,None))
				
				return expr['arg']
			elif arg != None:
				return arg

	else:
		#Leaf node
		if(isinstance(expr,Variable)):
			# print("Var:{}".format(expr))
			var_id = uri_to_hash(expr)
			if not var_id in vars_query:
				#New Var, probaly a Context Variable
				name = expr.n3().replace("?","")
				typee = URI
				vars_query[var_id] = new_var(name,typee)
			return var_id
		elif(isinstance(expr,URIRef)):
			# print("URI:{}".format(expr))
			#Do something?
			return None
		elif(isinstance(expr,Literal)):
			#Do something?
			return None

def parser_triples(triples,schema,vars_query={}):
	for triple in triples:
		subject,predicate,objectt = triple
		# print("Tripla: ",triple)
		if predicate == RDF.type and isinstance(subject,Variable):
			#is a variable type declaration
			id_var = uri_to_hash(subject)
			if id_var in vars_query:
				#var already parsed
				# print("foi 21",vars_query[id_var]['name'])
				# vars_query[id_var]['class'].update([objectt])
				vars_query[id_var]['class'] = set([objectt])
				vars_query[id_var]['class_is_explicit'] = True
			else:
				#new var found
				name = subject.n3().replace("?","")
				typee = URI
				vars_query[id_var] = new_var(name,typee,objectt,None,True)
				# print("foi 25",vars_query[id_var]['name'])
			# print(vars_query[id_var]['class'])
			#TODO: Obrigar a ficar apenas com o tipo explícito
			# print("declarou {} como um {}".format(subject.n3(),objectt))
		elif isinstance(subject,Variable) or isinstance(objectt,Variable):
			#subject or object are variables, so its types may be infered by property
			# print("******************************",schema,"******************************")
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
					# print(predicate_info['uri'])
					# print(domains)
					if not vars_query[id_hash_subject]['class_is_explicit']:
						# print("foi 22",vars_query[id_hash_subject]['name'])
						vars_query[id_hash_subject]['class'].update(domains) 
					
					update_context(vars_query[id_hash_subject]['context'],triple)
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
					if not vars_query[id_hash_subject]['class_is_explicit'] and not vars_query[id_hash_object]['class_is_explicit']:
						# print("foi 23",vars_query[id_hash_object]['name'])
						# print(ranges)
						vars_query[id_hash_object]['class'].update(ranges) 
					# print(objectt,":\n",triple)
					#TODO: Ver por que está aparecendo tripla estranha, nessa linha de baixo
					update_context(vars_query[id_hash_object]['context'],triple)
					vars_query[id_hash_object]['type'] = LITERAL
				else:
					#new var found
					name = objectt.n3().replace("?","")
					typee = URI
					if predicate_type == 2:
						typee = LITERAL
					vars_query[id_hash_object] = new_var(name,typee,ranges,context=(triple))

	return vars_query


#Utility methods

def uri_to_hash(uri):
	if isinstance(uri,URIRef):
		return hashlib.md5(str(uri).encode('utf-8')).hexdigest()
	elif isinstance(uri,str):
		return hashlib.md5(str(URIRef(uri)).encode('utf-8')).hexdigest()
def name_to_id_var(var):
	return uri_to_hash(Variable(var.replace("$","?")))


def update_context(context,triple):
	if triple not in context:
		context.append(triple)



def main():
	import pprint
	import qai.QAI as QAI
	pp = pprint.PrettyPrinter(indent=4)
	ontology_path = "input/medibot/ontology.ttl"
	schema = getGraph(ontology_path)
	classes_index = load_classes_index(schema)
	properties_index = load_properties_index(schema)

	# query = """
	# 	PREFIX drugs: <http://www.arida.ufc.br/ontology/drugs/>
	# 	PREFIX dc: <http://purl.org/dc/elements/1.1/>
	# 	PREFIX owl: <http://www.w3.org/2002/07/owl#>
	# 	PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>  
	# 	SELECT DISTINCT (str(?qai_7_title) as ?qai_7_title) (str(?qai_7_titleApresentacao) as ?qai_7_titleApresentacao) ?qai_7_precoVal WHERE{
	# 		?qai_7_medicamento a drugs:Medicamento;
	# 			dc:title ?qai_7_title;
	# 			drugs:temApresentacao ?qai_7_apresentacao.
	# 		?qai_7_apresentacao drugs:preco ?qai_7_preco;
	# 			dc:title ?qai_7_titleApresentacao.
	# 		?qai_7_preco a drugs:PrecoAoConsumidorSemImposto;
	# 			drugs:valorPreco ?qai_7_precoVal.
	# 		FILTER(REGEX(str(?qai_7_title),$qai_7_medicamento_in,'i'))
	# 	}
	# """
	query = """
		PREFIX drugs: <http://www.arida.ufc.br/ontology/drugs/>
		PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> 
		PREFIX dc: <http://purl.org/dc/elements/1.1/>
		SELECT  DISTINCT (GROUP_CONCAT(DISTINCT LCASE(?qai_1_auxLabel)) AS ?qai_1_titles) WHERE{
			
				?qai_1_termo a owl:Class.
				{
					?qai_1_termo rdfs:label ?qai_1_auxLabel
				}UNION{
					?qai_1_termo dc:title ?qai_1_auxLabel
				}OPTIONAL{
					?qai_1_termo rdfs:comment ?qai_1_auxComment
				}
				FILTER(REGEX(str(?qai_1_auxLabel),$qai_1_termo_in2 , 'i'))
			}GROUP BY ?qai_1_termo
	"""
	# query = """
	# 	PREFIX drugs: <http://www.arida.ufc.br/ontology/drugs/>
	# 	PREFIX dc: <http://purl.org/dc/elements/1.1/>
	# 	PREFIX owl: <http://www.w3.org/2002/07/owl#>
	# 	PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>  
	# 	SELECT * WHERE{
	# 		?qai_7_medicamento a drugs:Medicamento;
	# 			dc:title ?qai_7_title.
	# 		FILTER(REGEX(str(?qai_7_title),$qai_7_medicamento_in,'i'))
	# 	}
	# """
	query_object = processor.prepareQuery(query)
	pp.pprint(str(query_object.algebra))
	pp.pprint(parser_sparql(query,properties_index)) 
	QAIj = {'description':'','SP':query,'RP':{'header':'','body':'','footer':''},'QPs':['quero saber a definção de $qai_1_termo_in2']}
	qai = QAI.QAI(QAIj,0,properties_index)
	pp.pprint(qai.CVs)


if __name__ == "__main__":
	main()