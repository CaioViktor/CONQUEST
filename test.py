import pprint
import qai.QAI_Manager as q
import ontology.Schema as sc


# QAIM = q.QAI_Manager("example_QAIs.js")

pp = pprint.PrettyPrinter(indent=4)

schema = sc.getGraph("ontology.ttl")
# pp.pprint(sc.load_properties_index(schema))
# sc.load_classes_index(schema)
#pp.pprint(sc.load_classes_index(schema))



s = sc.load_properties_index(schema)

# pp.pprint(s)
q = '''
	PREFIX dc:<http://purl.org/dc/elements/1.1/>
	PREFIX drugs:<http://www.linkedmed.com.br/ontology/drugs/>
	SELECT distinct ?nomeMedicamento
      WHERE {
      	?s a drugs:Medicamento,drugs:MedicamentoAlopatico.
        ?s dc:title ?nomeMedicamento .
        ?s drugs:substancia ?substancia .
        ?substancia dc:title ?tituloSubstanciaPt .
        FILTER(regex(str(?tituloSubstanciaPt), $principioAtivo, "i"))
        FILTER (lang(?tituloSubstanciaPt) = 'pt')
      }
'''
varss = sc.parser_sparql(q,s)
pp.pprint(varss)

schema.close()