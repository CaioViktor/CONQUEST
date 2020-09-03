from flask import Flask,render_template,request, redirect, url_for
from SPARQLWrapper import SPARQLWrapper, JSON
import hashlib
import json


import json
rdf_browser_port = None
rdf_browser_graph = None
sparql_endpoint = None

with open("../input/configurations.json","r", encoding="utf-8") as json_file:
	configurations = json.load(json_file)
	rdf_browser_port = configurations["rdf_browser_port"]
	rdf_browser_graph = configurations["rdf_browser_graph"]
	sparql_endpoint = configurations["sparql_endpoint"]

endpoint = sparql_endpoint
graph = rdf_browser_graph

sparql = SPARQLWrapper(endpoint)

visited = set()
edges = set()
nodes = {}

app = Flask(__name__)



# 	return redirect(url_for("menu"))
def getDatatypeProperties(uri):
	query = """
	    SELECT DISTINCT ?p ?o """+graph+""" WHERE{
			{
				"""+uri+""" ?p ?o.
				FILTER(isLiteral(?o))
			}UNION{
				"""+uri+""" ?p ?o.
				FILTER(str(?p) = "http://www.w3.org/1999/02/22-rdf-syntax-ns#type")
			}
		}
	"""
	sparql.setQuery(query)
	# print(query)
	sparql.setReturnFormat(JSON)
	results = sparql.query().convert()
	properties = {}
	for result in results["results"]["bindings"]:
		id_property = uri_to_hash(result["p"]["value"])

		if not id_property in properties:
			properties[id_property] = {'uri':result["p"]["value"],'values':[]}
		properties[id_property]['values'].append(result["o"]["value"])
	return properties

def getObjectProperties(uri):
	query = """
	    SELECT DISTINCT ?p ?o """+graph+""" WHERE{
			"""+uri+""" ?p ?o.
			FILTER(isIRI(?o) && regex(str(?p), "^(?!http://www.w3.org/1999/02/22-rdf-syntax-ns#type)",'i') && regex(str(?p), "^(?!http://www.w3.org/2002/07/owl#).+") && regex(str(?o), "^(?!http://www.w3.org/2002/07/owl#).+"))
		}
	"""
	sparql.setQuery(query)
	# print(query)
	sparql.setReturnFormat(JSON)
	results = sparql.query().convert()
	neighbors = []
	for result in results["results"]["bindings"]:
		edges.add((uri_to_hash(uri),result["p"]["value"],uri_to_hash("<"+result["o"]["value"]+">"),result["p"]["value"].split("/")[-1].split("#")[-1].replace(">","")))
		neighbors.append("<"+result["o"]["value"]+">")
	return neighbors


def searchTem(term):
	sparql.setQuery("""
		PREFIX rdfs:<http://www.w3.org/2000/01/rdf-schema#>
		PREFIX dc:<http://purl.org/dc/elements/1.1/>
		PREFIX skos:<http://www.w3.org/2004/02/skos/core#>
	    SELECT DISTINCT ?s ?p ?term """+graph+""" WHERE{
			 {
			 	?s rdfs:label ?term
			 	BIND("rdfs:label" as ?p)
			 } UNION
			 {
			 	?s dc:title ?term
			 	BIND("dc:title" as ?p)
		 	} UNION
			{
				?s skos:prefLabel ?term
				BIND("skos:prefLabel" as ?p)
			} 
			FILTER(REGEX(str(?term),'"""+term+"""','i'))
		}ORDER BY strlen(str(?term))
	""")
	sparql.setReturnFormat(JSON)
	results = sparql.query().convert()
	resultss = []
	for result in results["results"]["bindings"]:
		resultss.append((result['s']['value'],result['p']['value'],result['term']['value']))
	return resultss

def visit_node(uri,depth):
	if depth <= 0 or uri in visited:
		return
	visited.add(uri)
	id_uri = uri_to_hash(uri)
	nodes[id_uri] = {'uri':uri.replace(">","").replace("<",""),'label':uri.split("/")[-1].replace(">",""),'properties':getDatatypeProperties(uri)}
	for neighbor in getObjectProperties(uri):
		visit_node(neighbor,depth-1)



def explore(uri):
	depth = 5
	visited.clear()
	edges.clear()
	nodes.clear()
	visit_node(uri,depth)

@app.route("/plot",methods=['POST','GET'])
def plot():
	if request.method == 'GET':
		uri = "<"+request.full_path.replace("/plot?uri=","")+">"
	else:
		uri = "<"+request.form['uri']+">"
	# print(request.values)
	explore(uri)
	return render_template('plot.html',nodes=nodes,edges=edges,uri=uri)

@app.route("/search/<term>")
def search(term):
	results = {}
	if term != " ":
		results = searchTem(term)

	return render_template("index.html",results=results)

@app.route("/search")
def search_get():
	term = request.values['term']
	result_dict = []
	if term != " ":
		results = searchTem(term)
		for result in results:
			result_dict.append({'uri':result[0],'property':result[1],'value':result[2]})

	return json.dumps(result_dict)

@app.route("/select")
def select():
	term = request.values['term']
	option = int(request.values['option'])
	results = searchTem(term)
	uri = "<"+results[option][0]+">"
	explore(uri)
	return render_template('plot.html',nodes=nodes,edges=edges,uri=uri)

@app.route("/")
def index():
	return redirect(url_for("search",term=" "))

def uri_to_hash(uri):
	return hashlib.md5(str(uri).encode('utf-8')).hexdigest()

if __name__ == "__main__":
	#app.run(host='200.19.182.252')
	if graph != "":
		graph = " FROM <"+graph+"> "
	app.run(host='0.0.0.0',port=rdf_browser_port)