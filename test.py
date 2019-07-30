import pprint
import qai.QAI_Manager as q
import ontology.Schema as sc


# QAIM = q.QAI_Manager("example_QAIs.js")

pp = pprint.PrettyPrinter(indent=4)

schema = sc.getGraph("ontology.ttl")
# pp.pprint(sc.load_properties_index(schema))
sc.load_classes_index(schema)
# pp.pprint(sc.load_classes_index(schema))

schema.close()