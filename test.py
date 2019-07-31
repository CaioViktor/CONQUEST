import pprint
import qai.QAI_Manager as q
import ontology.Schema as sc


# QAIM = q.QAI_Manager("example_QAIs.js")

pp = pprint.PrettyPrinter(indent=4)

schema = sc.getGraph("ontology.ttl")
# pp.pprint(sc.load_properties_index(schema))
# sc.load_classes_index(schema)
#pp.pprint(sc.load_classes_index(schema))

q = "PREFIX foaf:<http://xmlns.com/foaf/0.1/> SELECT ?name ?idade WHERE{ {?a a foaf:Person; foaf:name ?name; foaf:age ?age. ?cara foaf:novo <http://uri>} UNION {?a a foaf:Male} {SELECT ?a ?tipo WHERE{ ?a foaf:teste ?tipo}} FILTER(REGEX(STR(?name),$nomeCV,'i') && ?age <= $limite)} ORDER BY ?name LIMIT 100  "
sc.parser_sparql(q)

schema.close()