from rdflib import XSD
from SPARQLWrapper import SPARQLWrapper, JSON
import ontology.Schema as sc
from config import messages
class Query_Processor():
	def __init__(self,url_endpoint,graph_name=""):
		self.url_endpoint = url_endpoint
		self.graph_name = graph_name
		if self.graph_name != "":
			self.graph_name = " FROM <{}> ".format(self.graph_name)

	def run(self,qai,cvs):
		query = self.build_query(qai,cvs)
		# print(query)
		results = self.run_sparql(query)
		# print(results)
		return self.build_answer(qai,results)

	def build_query(self,qai,cvs):
		#TODO: Tratar tipos de dados
		query = qai.SP
		if self.graph_name != "":
			#Set FROM clause in query
			q = query.lower()
			if "from" not in q:
				where_index = q.index("where")
				where_end_index = where_index + len("where")
				where_query = query[where_index:where_end_index]
				query = query.replace(where_query,self.graph_name+"WHERE")
		for cv in cvs:
			id_var = sc.name_to_id_var(cv['name'])
			cv_value = cv['value']
			#TODO: Ver se vai dar erro por causa dos tipos das variáveis terem sido simplificados
			if XSD.string in qai.CVs[id_var]['class']:
				cv_value = '"'+str(cv_value)+'"^^xsd:string'
			elif XSD.dateTime in qai.CVs[id_var]['class']:
				cv_value = '"'+str(cv_value)+'"^^xsd:dateTime'
			elif XSD.date in qai.CVs[id_var]['class']:
				cv_value = '"'+str(cv_value)+'"^^xsd:date'
			elif XSD.integer in qai.CVs[id_var]['class']:
				cv_value = '"'+str(cv_value)+'"^^xsd:integer'
			elif XSD.float in qai.CVs[id_var]['class']:
				cv_value = '"'+str(cv_value)+'"^^xsd:float'
			elif XSD.double in qai.CVs[id_var]['class']:
				cv_value = '"'+str(cv_value)+'"^^xsd:double'
			elif XSD.decimal in qai.CVs[id_var]['class']:
				cv_value = '"'+str(cv_value)+'"^^xsd:decimal'
			elif XSD.real in qai.CVs[id_var]['class']:
				cv_value = '"'+str(cv_value)+'"^^xsd:real'
			query = query.replace(cv['name'],cv_value)
		return query

	def run_sparql(self,query):
		sparql = SPARQLWrapper(self.url_endpoint)
		sparql.setQuery(query)
		sparql.setReturnFormat(JSON)
		results = sparql.query().convert()
		result_set = []
		for result in results["results"]["bindings"]:
			result_item = {}
			for var in result:
				result_item["?"+var] = result[var]["value"]
			result_set.append(result_item)
		return result_set

	def build_answer(self,qai,results):
		if len(results) == 0:
			return messages['empty_rensponse']
		answer = qai.RP['header']
		# print("RV",qai.RVs)
		for result in results:
			body_line = "\n{}".format(qai.RP['body'])
			for rv_id in qai.RVs:
				rv = qai.RVs[rv_id]['name']
				rv_value = ""
				if rv in result:
					rv_value = result[rv]
				body_line = body_line.replace(rv,rv_value)
			answer+=body_line
		answer += "\n"+qai.RP['footer']
		return answer