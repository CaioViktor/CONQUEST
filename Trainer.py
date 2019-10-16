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
import pprint
import spacy

pp = pprint.PrettyPrinter(indent=4)



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
path_train_NER_temp = "persistence/temp/nlp"
ner_nlp_model_path = "persistence/nlp/"
ner_number_iterations = 100
ner_number_samples_train = 10000
ner_number_samples_examples = 0
# End Parameters

@plac.annotations(
    mode =("Training mode:\nzero - Training the chatbot from starting point (default).\nresume - Resume the training from a saved point.\nupdate - Update models", "option", "m", str),
    point = ("Point to resume training.\n0 - Starting from start (equal to zero mode).\n1 - Starting from loading QAIs.\n2 - Starting from making NER training dataset.\n3 - Starting from training NLP.\n4 - Starting from making classifier training dataset.\n5 - Starting from training the classifier.\n", "option", "p", int)
)

def main(mode='zero',point = 0):
	point = int(point)
	print("Mode {}\nPoint {}".format(mode,point))

	global satart_time_trainer


	satart_time_trainer = datetime.now()
	if mode.lower() == 'update':
		print("update")
		#TODO: Update model
	elif mode.lower() == 'resume' or point > 0:
		print("Resuming training...\n\n\n")
		if point <= 0:
			make_indexes()

		load_index()	

		if point > 1:
			load_QAIs()
		else:
			return process_QAIs()
		if point > 2:
			load_train_NER()
		else:
			return make_train_NER()
		if point > 3:
			load_NLP()
		else:
			return train_NLP()
		if point > 4:
			load_train_classifier()
		else:
			return make_train_classifier()
		if point == 5:
			train_classifier()
		else:
			return finish()
	elif mode.lower() == 'zero':
		make_indexes()
	else:
		print("unknow option for training mode")
	return

def make_indexes():
	print("\n\nStarting stage",0)


	global classes_index
	global properties_index


	print("Reading ontology schema...")
	schema = sc.getGraph(ontology_path)
	
	print("Creating classes index...")
	classes_index = sc.load_classes_index(schema)

	# pp.pprint(classes_index)
	out_path = os.path.join("persistence/index","class.sav") 
	with open(out_path ,"wb") as file:
		pickle.dump(classes_index,file)
		print("Classes index saved to {}".format(out_path))

	

	print("Creating properties index...")
	properties_index = sc.load_properties_index(schema)

	# pp.pprint(properties_index)
	out_path = os.path.join("persistence/index","property.sav") 
	with open(out_path ,"wb") as file:
		pickle.dump(properties_index,file)
		print("Properties index saved to {}".format(out_path))

	schema.close()
	process_QAIs()

def process_QAIs():
	print("\n\nStarting stage",1)

	global properties_index
	global QAI_Manager


	print("Loading Question Answering Itens (QAIs) from {}...".format(QAIs_path))
	QAI_Manager = q.QAI_Manager(QAIs_path,properties_index)

	out_path = os.path.join("persistence/qais","qai_manager.sav") 
	with open(out_path ,"wb") as file:
		pickle.dump(QAI_Manager,file)
		print("QAI Manager saved to {}".format(out_path))

	make_train_NER()

def make_train_NER():
	print("\n\nStarting stage",2)

	global classes_index
	global QAI_Manager
	global ner_trainer
	

	print("Starting NLP stage.")
	ner_trainer = NER_Trainer(QAI_Manager.QAIs,classes_index,sparql_endpoint,graph_name,number_iterations=ner_number_iterations,number_samples_train=ner_number_samples_train,number_samples_examples=ner_number_samples_examples)
	
	print("Creating NER training dataset. This could take several minutes...")
	ner_trainer.make_train_dataset(savePath=path_train_NER_temp)
	print("NER training dataset saved to {}.\nNumber of examples {}.\n{} labels contained in examples:{}".format(path_train_NER_temp,len(ner_trainer.train_dataset),len(ner_trainer.get_labels()),ner_trainer.get_labels()))
	
	train_NLP()

def train_NLP():
	print("\n\nStarting stage",3)

	global ner_trainer
	global nlp_model


	print("Training NLP model. This could take several minutes...")
	nlp_model = ner_trainer.train_NER(outputPath=ner_nlp_model_path)
	print("NLP model saved to", ner_nlp_model_path)
	make_train_classifier()

def make_train_classifier():
	print("\n\nStarting stage",4)

	global X
	global y
	global classifier


	print("Starting Classifier stage. This could take several minutes...")
	nlp_model_path = os.path.join(ner_nlp_model_path,"nlp_model")
	labels_path = os.path.join(path_train_NER_temp,"labels.sav")

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
	print("\n\nStarting stage",5)

	global X
	global y
	global classifier


	print("Training classifier. This could take several minutes...")
	classifier.fit(X,y)
	classifier.save_model()
	finish()

def finish():


	global satart_time_trainer


	finish_time = datetime.now()
	print("\n\n\nFinished training chatbot process!!!\nElapsed time: {}".format(str(finish_time - satart_time_trainer)))

def load_index():
	print("Loading stage",0)
	
	global classes_index
	global properties_index

	
	out_path = os.path.join("persistence/index","class.sav") 
	with open(out_path ,"rb") as file:
		classes_index = pickle.load(file)
		print("Classes index loaded from {}".format(out_path))

	out_path = os.path.join("persistence/index","property.sav") 
	with open(out_path ,"rb") as file:
		properties_index = pickle.load(file)
		print("Properties index loaded from {}".format(out_path))
	return

def load_QAIs():
	print("Loading stage",1)
	
	global properties_index
	global QAI_Manager

	out_path = os.path.join("persistence/qais","qai_manager.sav") 
	with open(out_path ,"rb") as file:
		QAI_Manager = pickle.load(file)
		print("QAI Manager loaded from {}".format(out_path))
	return

def load_train_NER():
	print("Loading stage",2)
	
	global classes_index
	global QAI_Manager
	global ner_trainer

	ner_trainer = NER_Trainer(QAI_Manager.QAIs,classes_index,sparql_endpoint,graph_name,number_iterations=ner_number_iterations,number_samples_train=ner_number_samples_train,number_samples_examples=ner_number_samples_examples)
	ner_trainer.load_train_dataset(path_train_NER_temp)

	print("NER training dataset loaded from {}".format(path_train_NER_temp))
	return

def load_NLP():
	print("Loading stage",3)
	
	global ner_trainer
	global nlp_model
	 
	out_path = os.path.join(ner_nlp_model_path,"nlp_model")
	nlp_model = spacy.load(out_path)
	print("NLP model loaded from {}".format(out_path))

	return

def load_train_classifier():
	print("Loading stage",4)
	
	global X
	global y
	global classifier


	nlp_model_path = os.path.join(ner_nlp_model_path,"nlp_model")
	labels_path = os.path.join(path_train_NER_temp,"labels.sav")

	nlp_processor = NLP_Processor(nlp_model_path)
	labels_NER = load_labels(labels_path)
	

	output_path = "persistence/temp/classifier/X.sav"
	with open(output_path,"rb") as output:
		X = pickle.load(output)
		print("Features vector X loaded from",output_path)

	output_path = "persistence/temp/classifier/y.sav"
	with open(output_path,"rb") as output:
		y = pickle.load(output)
		print("Classes vector y loaded from",output_path)

	print("Creating classifier.")
	classifier = ML_Classifier(model_path="persistence/classifier",model_file="ml_classifier.sav")

	return


def load_labels(filePath):
	with open(filePath,"rb") as file:
		return pickle.load(file)

if __name__ == "__main__":
    plac.call(main)