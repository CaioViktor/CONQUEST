#CONQUEST Trainer
#Module used for training the chatbot for the interactive question answering task on closed domain knowledge bases.


import plac
from pathlib import Path
import ontology.Schema as sc
import qai.QAI_Manager as q
import pickle
import os
from nlp.NLP_Processor import NLP_Processor
from classifier.ML_Classifier import ML_Classifier
from nlp.pt.NER_Trainer_PT import NER_Trainer #Change package to change language
from datetime import datetime



satart_time_trainer = None

classes_index = None
properties_index = None
QAI_Manager = None
ner_trainer = None
nlp_model = None
X = None
y = None
classifier = None

#Parameters
# ontology_path = "input/ontology.ttl"
# QAIs_path = "input/input_QAIs.js"
ontology_path = "input/medibot/ontology.ttl"
QAIs_path = "input/medibot/MediBot.json"
sparql_endpoint = "http://localhost:8890/sparql"
graph_name = "http://localhost:8890/DAV/drugs"
path_train_NER = "persistence/temp/nlp/dataset.sav"
ner_nlp_model_path = "persistence/temp/nlp/model/nlp_model"
ner_number_iterations = 100
ner_number_samples_train = 1000
ner_number_samples_examples = 0
# End Parameters

@plac.annotations(
    mode =("Training mode:\nzero - Training the chatbot from starting point (default).\nresume - Resume the training from a saved point.\nupdate - Update models", "option", "m", str),
    point = ("Point to resume training.", "option", "p", str)
)

def main(mode='zero',point = None):
	if mode.lower() == 'zero':
		satart_time_trainer = datetime.now()
		make_indexes()
	elif mode.lower() == 'resume':
		print("resume")
	elif mode.lower() == 'update':
		print("update")
	else:
		print("unknow option for training mode")
	return

def make_indexes():
	print("Reading ontology schema...")
	schema = sc.getGraph(ontology_path)
	
	print("Creating classes index...")
	classes_index = sc.load_classes_index(schema)
	out_path = os.path.join("persistence/index","class.sav") 
	with open(out_path ,"wb") as file:
		pickle.dump(classes_index,file)
		print("Classes index saved to {}"format(out_path))

	print("Creating properties index...")
	properties_index = sc.load_properties_index(schema)
	out_path = os.path.join("persistence/index","property.sav") 
	with open(out_path ,"wb") as file:
		pickle.dump(properties_index,file)
		print("Properties index saved to {}".format(out_path))

	schema.close()
	process_QAIs()

def process_QAIs():
	print("Loading Question Answering Itens (QAIs) from {}...".format(QAIs_path))
	QAI_Manager = q.QAI_Manager(QAIs_path,properties_index)

	out_path = os.path.join("persistence/qais","qai_manager.sav") 
	with open(out_path ,"wb") as file:
		pickle.dump(QAI_Manager,file)
		print("QAI Manager saved to {}".format(out_path))

	make_and_train_NER()

def make_train_NER():
	print("Starting NLP stage. This could take several minutes...")
	ner_trainer = NER_Trainer(QAI_Manager.QAIs,classes_index,sparql_endpoint,graph_name,number_iterations=ner_number_iterations,number_samples_train=ner_number_samples_train,number_samples_examples=ner_number_samples_examples)
	print("Creating NER training dataset. This could take several minutes...")
	
	ner_trainer.make_train_dataset(savePath=path_train_NER)
	print("NER training dataset saved to {}.\nNumber of examples {}.\n{} labels contained in examples:{}".format(path_train_NER,len(ner_trainer.train_dataset),len(ner_trainer.get_labels),ner_trainer.get_labels))
	
	train_NLP()

def train_NLP():
	print("Training NLP model. This could take several minutes...")
	nlp_model = ner_trainer.train_NER(outputPath=ner_nlp_model_path)
	print("NLP model saved to", ner_nlp_model_path)
	make_train_classifier()

def make_train_classifier():
	print("Starting Classifier stage. This could take several minutes...")
	nlp_model_path = os.path.join(ner_nlp_model_path,"nlp_model")
	labels_path = os.path.join(path_train_NER,"labels.sav")

	nlp_processor = NLP_Processor(nlp_model_path)
	labels_NER = load_labels(labels_path)
	print("Creating classifier training dataset. This could take several minutes...")
	X,y = ML_Classifier.pre_process_data(QAI_Manager.QAIs,labels_NER,nlp_processor)
	

	output_path = "persistence/temp/classifier/X.sav"
	with open(output_path,"wb") as output:
		pickle.dump(X,output)
		print("Features vector X saved to",output_path)


	output_path = "persistence/temp/classifier/y.sav"
	with open(output_path,"wb") as output:
		pickle.dump(y,output)
		print("Classes vector y saved to",output_path)

	print("Creating classifier.")
	classifier = ML_Classifier(model_path="persistence/classifier",model_file="ml_classifier.sav")

	train_classifier()

def train_classifier():
	print("Training classifier. This could take several minutes...")
	classifier.fit(X,y)
	classifier.save_model()
	finish()

def finish():
	finish_time = datetime.now()
	print("\n\n\nFinished training chatbot process!!!\nElapsed time: {}".format(str(finish_time - satart_time_trainer)))

if __name__ == "__main__":
    plac.call(main)