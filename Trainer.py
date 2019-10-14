#CONQUEST Trainer
#Module used for training the chatbot for the interactive question answering task on closed domain knowledge bases.


import plac
from pathlib import Path
import ontology.Schema as sc
import qai.QAI_Manager as q
import pickle
import os


classes_index = None
properties_index = None
QAI_Manager = None
ner_trainer = None

#Parameters
# ontology_path = "input/ontology.ttl"
# QAIs_path = "input/input_QAIs.js"
ontology_path = "input/medibot/ontology.ttl"
QAIs_path = "input/medibot/MediBot.json"
sparql_endpoint = "http://localhost:8890/sparql"
graph_name = "http://localhost:8890/DAV/drugs"
path_train_NER = "persistence/temp/nlp/dataset.sav"
ner_number_iterations = 100
ner_number_samples_train = 1000
ner_number_samples_examples = 10
# End Parameters

@plac.annotations(
    config = ("Configurations file.", "option", "c", Path),
    mode =("Training mode:\nzero - Training the chatbot from starting point (default).\nresume - Resume the training from a saved point.\nupdate - Update models", "option", "m", str),
    point = ("Point to resume training.", "option", "p", str)
)

def main(config=None, mode='zero',point = None):
	#TODO: ler configurações
	if mode.lower() == 'zero':
		make_indexes()
	return

def make_indexes():
	print("Reading ontology schema...")
	schema = sc.getGraph(ontology_path)
	
	print("Creating classes index...")
	classes_index = sc.load_classes_index(schema)
	out_path = os.path.join("persistence/index","class.sav") 
	with open(out_path ,"wb") as file:
		pickle.dump(classes_index,file)
		print("Classes index saved to {}",out_path)

	print("Creating properties index...")
	properties_index = sc.load_properties_index(schema)
	out_path = os.path.join("persistence/index","property.sav") 
	with open(out_path ,"wb") as file:
		pickle.dump(properties_index,file)
		print("Properties index saved to {}",out_path)

	schema.close()
	process_QAIs()

def process_QAIs():
	print("Loading Question Answering Itens (QAIs) from {}...",QAIs_path)
	QAI_Manager = q.QAI_Manager(QAIs_path,properties_index)

	out_path = os.path.join("persistence/qais","qai_manager.sav") 
	with open(out_path ,"wb") as file:
		pickle.dump(QAI_Manager,file)
		print("QAI Manager saved to {}",out_path)

	make_and_train_NER()

def make_and_train_NER():
	print("Starting NLP stage. This could take several minutes...")
	ner_trainer = NER_Trainer(QAI_Manager.QAIs,classes_index,sparql_endpoint,graph_name,number_iterations=ner_number_iterations,number_samples_train=ner_number_samples_train,number_samples_examples=ner_number_samples_examples)
	#TODO: Configurar diretórios para treinamento
	#model = ner_trainer.make_train_dataset(savePath=path_train_NER).train_NER()
	


if __name__ == "__main__":
    plac.call(main)