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
				"Quem é $nome ?",
				"Fale sobre o $nome",
				"Busque pela pessoa com o nome $nome"
			],
			"SP": "PREFIX foaf:<http://xmlns.com/foaf/0.1/> SELECT ?nome ?idade WHERE{ ?a a foaf:Person; foaf:name ?name; foaf:age ?age. FILTER(REGEX(STR(?name),$nome,'i'))}",
			"RP": {
				"header": "Eu encontrei as seguintes pessoas:",
				"body": "?nome ?idade",
				"footer":"Você desaja mais alguma coisa?"
			}
		}
	]
}