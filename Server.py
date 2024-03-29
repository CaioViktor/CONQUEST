from flask import Flask,render_template,request, redirect, url_for, jsonify
from dialog.Dialog_Manager import Dialog_Manager
import atexit
import pymongo
import re
import user_interface.Telegram as telegram
import threading
import requests

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
print("Starting Dialog Manager...")
dialog_manager = Dialog_Manager(users_collection)

if use_TELEGRAM:
	print("Starting Telegram Bot...")
	telegram_thread = threading.Thread(target=telegram.main()).start()

@app.route("/search")
def search():
	if 'term' in request.args:
		rdf_browser_url = "http://localhost:{}/".format(rdf_browser_port)
		r = requests.get(rdf_browser_url+"search", params={'term':request.args['term']})
		results = []
		for result in r.json():
			result_aux = result
			result_aux['link'] = rdf_browser_url+"plot?uri="+result['uri']
			results.append(result_aux)
		return jsonify(results)
	return {'status':1,'message':["Missing args!"]}


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

@app.route("/list_qais/")
def list_qais():
	response = dialog_manager.list_QAIs()
	return jsonify(response)

@app.route("/select_qai/")
def select_qai():
	if 'user_id' in request.args and 'qai_id' in request.args:
		user_id = request.args['user_id']
		qai_id = request.args['qai_id']
		if user_id == '-1':
			return {'status':0,'message':["Invalid User ID!"]}
		if users_collection.find_one({'id':user_id}) is None:
			#New user
			user = create_new_user(user_id)
			users_collection.insert_one(user)
		user = users_collection.find_one({'id':user_id})
		response = dialog_manager.select_QAI(user,qai_id)
		return jsonify(response)
	return {'status':1,'message':["Missing args!"]}

@app.route("/")
def index():
	return """Server Running...<br/>
	/list_qais/\t----\t For List suported Questions<br/>
	/select_qai?user_id=VALUE&qai_id=VALUE\t----\t For select a Especific Question<br/>
	/query?user_id=VALUE&text\t----\t For send a Message for the chatbot<br/>
	/search?term=VALUE\t----\t For browser on a specific URI<br/>
	"""


def exit_handler():
	if use_TELEGRAM:
		global telegram_thread
		print('Telegram bot is ending!')
		telegram.shutdown()
	print('Server is ending!')
	dialog_manager.close()


atexit.register(exit_handler)

if __name__ == "__main__":
	app.run(host=host,port = port)

