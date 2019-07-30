import pprint
import qai.QAI_Manager as q
import ontology.Schema as sc
import ontology.SPARQL_Parser.sqparser3 as parser


# QAIM = q.QAI_Manager("example_QAIs.js")
#sc.load_properties_index("ontology.ttl")

text = '''PREFIX foaf:<http://xmlns.com/foaf/0.1/> 
		SELECT ?name ?idade WHERE{ 
			?a a foaf:Person; 
				foaf:name ?name; 
				foaf:age ?age. 
			FILTER(REGEX(STR(?name), $nome ,'i'))
		}'''

text = '''PREFIX qpr: <http://istresearch.com/qpr> 
 			SELECT ?number_of_individuals (count(?ad) AS ?count)(group_concat(?ad;separator=',') AS ?ads) WHERE { 
 				?ad a qpr:Ad ; 
 				qpr:location 'Eugene, OR' ; 
 				qpr:number_of_individuals ?number_of_individuals .  
 			} GROUP BY ?number_of_individuals 
 			ORDER BY DESC(?count) 
 			LIMIT 1'''

pp = pprint.PrettyPrinter(indent=4)
pp.pprint(parser.SQParser.parse_string(text))