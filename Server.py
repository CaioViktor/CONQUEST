from flask import Flask,render_template,request, redirect, url_for, jsonify
from dialog.Dialog_Manager import Dialog_Manager
import atexit
import pymongo
import re

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
		'context': new_user_context() #From dialog.constants
	}
	return user



app = Flask(__name__)
dialog_manager = Dialog_Manager(users_collection)

@app.route("/query/")
def query():
	if 'user_id' in request.args and 'text' in request.args:
		user_id = request.args['user_id']
		text = request.args['text']
		if text is None or text.strip() == "":
			return {'status':1,'message':["Missing args!"]}
		text = text.strip()
		text = re.sub(r'^\"','',text)
		text = re.sub(r'\"$','',text)
		if user_id == '-1':
			return {'status':0,'message':["Invalid User ID!"]}
		if users_collection.find_one({'id':user_id}) is None:
			#New user
			user = create_new_user(user_id)
			users_collection.insert_one(user)
		response = dialog_manager.notify_message(text,user_id)
		# print(response)
		# return jsonify({'status':1,'message':response})
		return jsonify(response)
	return {'status':1,'message':["Missing args!"]}

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

