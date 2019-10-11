{
	"description": "Exemplo de QAI",
	"update_data": "",
	"author": "Caio Viktor",
	"created_date": "",
	"QAIs": [
		{
			"id": 1,
			"description": "Consulta pessoas pelo nome",
			"QPs": [
				"Quem é $principioAtivo com idade maior que $ida",
				"Fale sobre o $principioAtivo com idade maior que $ida",
				"Busque pela pessoa com o nome $principioAtivo com idade maior que $ida"
			],
			"SP": "PREFIX dc:<http://purl.org/dc/elements/1.1/>\n PREFIX drugs:<http://www.linkedmed.com.br/ontology/drugs/>\n SELECT distinct ?nomeMedicamento \n WHERE { \n   ?s a drugs:Medicamento,drugs:MedicamentoAlopatico;\n dc:title ?nomeMedicamento;\n drugs:temApresentacao ?ap.\n ?s drugs:substancia ?substancia .\n ?substancia dc:title ?tituloSubstanciaPt .\n ?ap drugs:ean ?ean.\n FILTER(regex(str(?tituloSubstanciaPt), $principioAtivo, 'i') && ?ean > $ida)\n }",
			"RP": {
				"header": "Eu encontrei as seguintes pessoas:",
				"body": "?nomeMedicamento",
				"footer":"Você desaja mais alguma coisa?"
			}
		}
	]
}