from flask import Flask,render_template,request, redirect, url_for
from dialog.Dialog_Manager import Dialog_Manager
import atexit
import pymongo

#States constants
from dialog.constants import *

#Configuration parameters
from config import *



#Database
NAME_DB = "conquest_"+chatbot_name
USERS_COLL = 'users'
mongo = pymongo.MongoClient("mongodb://localhost:27017/")
db = mongo[NAME_DB]
users_collection = db[USERS_COLL]
users_collection.insert_one({'id':'-1'})
users_collection.delete_one({'id':'-1'})

def create_new_user(user_id):
	user = {
		'id':user_id,
		'context': {
			'state': WAITING_TO_START,
			'question': "",#Question in natural language
			'entities_found': [],
			'qai_id':-1, #QAI id classified
			'cvs_to_fill':[{'name':"",	'type':""}] ,#Names of recognized CVs yet to fill
			'cvs_filled':[{'name':""	,	'value:':""}] ,#Names of recognized CVs yet to fill
			'original_cvec':[], #Original CVec parsed from the question
			'original_sv':[], #Original SV parsed from the question
			'options': [{'text':""	,	'value':""}] #options asked to user
		}
	}
	return user



app = Flask(__name__)
dialog_manager = Dialog_Manager(users_collection)

@app.route("/query/")
def query():
	if 'user_id' in request.args and 'text' in request.args:
		user_id = request.args['user_id']
		text = request.args['text']
		if user_id == '-1':
			return {'status':0,'message':"Invalid User ID!"}
		if users_collection.find_one({'id':user_id}) is None:
			#New user
			user = create_new_user(user_id)
			users_collection.insert_one(user)
		response = dialog_manager.notify_message(text,user_id)

		return {'status':1,'message':response}
	return {'status':0,'message':"Missing args!"}

@app.route("/")
def index():
	return "Server Running"


def exit_handler():
	print('Server is ending!')
	dialog_manager.close()


atexit.register(exit_handler)

if __name__ == "__main__":
	#app.run(host='200.19.182.252')
	app.run(host=host,port = port)

