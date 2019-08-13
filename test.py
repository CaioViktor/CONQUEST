import pprint
import qai.QAI_Manager as q
import ontology.Schema as sc
import rdflib.plugins.sparql.processor as processor
from rdflib.plugins.sparql.parser import parseQuery



pp = pprint.PrettyPrinter(indent=4)

schema = sc.getGraph("ontology.ttl")
# pp.pprint(sc.load_properties_index(schema))
# sc.load_classes_index(schema)
#pp.pprint(sc.load_classes_index(schema))



s = sc.load_properties_index(schema)
QAIM = q.QAI_Manager("MediBot.json")

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

# query_object = processor.prepareQuery(q)
# query_object = parseQuery(q)
# print(query_object.algebra)

# varss = sc.parser_sparql(q,s)
# pp.pprint(varss)

schema.close()