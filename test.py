import pprint
import qai.QAI_Manager as q
import ontology.Schema as sc
import rdflib.plugins.sparql.processor as processor
from rdflib.plugins.sparql.parser import parseQuery
import context.Factory_ContextVariables as fCV
import spacy
from spacy.lang.pt.examples import sentences 

from nlp.pt.NER_Trainer_PT import NER_Trainer #Change package to change language



pp = pprint.PrettyPrinter(indent=4)

schema = sc.getGraph("ontology.ttl")
# pp.pprint(sc.load_properties_index(schema))
classIndex = sc.load_classes_index(schema)
# pp.pprint(classIndex)
#pp.pprint(sc.load_classes_index(schema))



sp = sc.load_properties_index(schema)
scl = sc.load_classes_index(schema)
QAIM = q.QAI_Manager("MediBot.json",sp)
# QAIM = q.QAI_Manager("example_QAIs.js",sp)
f = fCV.Factory_ContextVariables(scl)

ner_trainer = NER_Trainer(QAIM.QAIs,classIndex,"http://localhost:8890/sparql","http://localhost:8890/DAV/drugs",number_iterations=200,number_samples_train=1000)
# model = ner_trainer.make_train_dataset(savePath="temp/dataset").train_NER()
# model = ner_trainer.make_train_dataset(savePath="temp/dataset_full")
model = ner_trainer.train_NER(loadPath="temp/dataset_full")



# print("labels:\n{}\n-------------------------\n".format(ner_trainer.get_labels()))
# pp.pprint(dataset)

# for qai in QAIM.QAIs:
# 	print("QPs:")
# 	for qp in qai.QPs:
# 		print(qp)
# 	print("-------------------------------------------------")
# 	print("cvs")
# 	for cv_id in qai.CVs:
# 		cv = qai.CVs[cv_id]
# 		pp.pprint(cv)
# 	print("*************************************************")
# 	print(qai.CVs)
# 	print("QAI {}:\n".format(qai.id))
# 	CV = f.build_ContextVariables_vector(qai.CVs)
# 	print(CV.max())


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
# for classs in scl:
# 	if 'identifiers' in scl[classs]:
# 		print("{}:\n{}\n\n".format(scl[classs]['uri'],scl[classs]['identifiers']))
# schema.close()



# nlp = spacy.load('pt_core_news_sm')

# ner_trainer = nt.NER_Trainer(classIndex,"http://localhost:8890/sparql","<http://localhost:8890/DAV/drugs>",nlp,fulldata=False)
# ner_trainer.add_labels_to_nlp()
# print(nlp.entity.labels)
# ner_trainer.train_NER(None)