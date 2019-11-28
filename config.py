#Parameters
# ontology_path = "input/ontology.ttl"
# QAIs_path = "input/input_QAIs.js"
ontology_path = "input/medibot/ontology.ttl"
QAIs_path = "input/medibot/MediBot.json"
sparql_endpoint = "http://localhost:8890/sparql"
graph_name = "http://localhost:8890/DAV/drugs"
path_train_NER_temp = "persistence/temp/nlp"
ner_nlp_model_path = "persistence/nlp/"
ner_number_iterations = 100
ner_number_samples_train = 10000
ner_number_samples_examples = 0
solr_host =" http://localhost"
solr_port = "8983"
solr_core = "conquest_exact_match"
solr_memory = "1g"
nlp_model_load = "persistence/nlp/model/pt_br"
# End Parameters

chatbot_name = "medibot" #Set ChatBot name

#Server Parameters
host = '0.0.0.0'
port = 5000

min_confidance_classification = 0.8
min_diference_confidance = 0.05
number_desambiguation_options = 3




#APIs Messenger
TELEGRAM_TOKEN = "651002368:AAGbk_d0sMIO92rpU_GSVgKAodukcMNDjUI"
