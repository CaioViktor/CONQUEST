import pprint
import qai.QAI_Manager as q
import ontology.Schema as sc
import rdflib.plugins.sparql.processor as processor
from rdflib.plugins.sparql.parser import parseQuery
import context.Factory_ContextVariables as fCV



pp = pprint.PrettyPrinter(indent=4)

schema = sc.getGraph("ontology.ttl")
# pp.pprint(sc.load_properties_index(schema))
# sc.load_classes_index(schema)
#pp.pprint(sc.load_classes_index(schema))



sp = sc.load_properties_index(schema)
scl = sc.load_classes_index(schema)
# QAIM = q.QAI_Manager("MediBot.json",sp)
QAIM = q.QAI_Manager("example_QAIs.js",sp)
f = fCV.Factory_ContextVariables(scl)

for qai in QAIM.QAIs:
	print(qai.CVs)
	print("QAI {}:\n".format(qai.id))
	CV = f.build_ContextVariables_vector(qai.CVs)
	print(CV.max())


# pp.pprint(s)
# q = '''
# 	PREFIX dc:<http://purl.org/dc/elements/1.1/>
# 	PREFIX drugs:<http://www.linkedmed.com.br/ontology/drugs/>
# 	SELECT distinct ?nomeMedicamento
#       WHERE {
#       	?s a drugs:Medicamento,drugs:MedicamentoAlopatico.
#         ?s dc:title ?nomeMedicamento .
#         ?s drugs:substancia ?substancia .
#         ?substancia dc:title ?tituloSubstanciaPt .
#         FILTER(regex(str(?tituloSubstanciaPt), $principioAtivo, "i"))
#         FILTER (lang(?tituloSubstanciaPt) = 'pt')
#       }
# '''

# FILTER(regex(str(?nomeMedicamento), $nome, "i"))



# q = '''
# 	SELECT ?a
#       WHERE {
#       	FILTER(REGEX(?a,$b,"i"))
#     }
# '''
# q = "PREFIX drugs: <http://www.linkedmed.com.br/ontology/drugs/>\n PREFIX dc: <http://purl.org/dc/elements/1.1/>\nSELECT  DISTINCT (GROUP_CONCAT(DISTINCT LCASE(?auxLabel);separator='\\nOU\\n') AS ?titles) (GROUP_CONCAT( DISTINCT LCASE(?auxTipo);separator=' ; ') as ?types) (GROUP_CONCAT(DISTINCT LCASE(?auxComment);separator=' . ') as ?comments) WHERE{\n        {?termo rdfs:label ?auxLabel}UNION\n        {?termo dc:title ?auxLabel}\n        OPTIONAL{\n          ?termo rdfs:comment ?auxComment\n       }\n        OPTIONAL{\n         ?termo a _:tipo.\n         _:tipo rdfs:label ?auxTipo.\n        }\n        FILTER(REGEX(str(?auxLabel),$termo_in , 'i'))\n      }GROUP BY ?termo"

# query_object = processor.prepareQuery(q)
# query_object = parseQuery(q)
# print(query_object.algebra['PV'])

# varss = sc.parser_sparql(q,s)
# pp.pprint(varss)

schema.close()