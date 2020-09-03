#WARNING: Change only the file "input/configurations.json"


import json
with open("input/configurations.json","r", encoding="utf-8") as json_file:
	configurations = json.load(json_file)

	ontology_path = configurations["ontology_path"]
	QAIs_path = configurations["QAIs_path"]
	sparql_endpoint = configurations["sparql_endpoint"]
	graph_name = configurations["graph_name"]
	path_train_NER_temp = configurations["path_train_NER_temp"]
	ner_nlp_model_path = configurations["ner_nlp_model_path"]
	language = configurations["language"]
	
	solr_host = configurations["solr_host"]
	solr_port = configurations["solr_port"]
	solr_core = configurations["solr_core"]
	solr_memory = configurations["solr_memory"]
	nlp_model_load = configurations["nlp_model_load"]
	# End Parameters

	chatbot_name = configurations["chatbot_name"] #Set ChatBot name

	#Server Parameters
	host = configurations["host"]
	port = configurations["port"]

	min_confidance_classification = configurations["min_confidance_classification"]
	min_diference_confidance = configurations["min_diference_confidance"]
	number_desambiguation_options = configurations["number_desambiguation_options"]
	steps_to_update = configurations["steps_to_update"]

	#APIs Messenger
	TELEGRAM_TOKEN = configurations["TELEGRAM_TOKEN"]
