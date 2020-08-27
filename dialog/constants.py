WAITING_TO_START = "waiting to start"
WAITING_DESAMBIGUATION = "waiting desambiguation"
INVALID_OPTION = "invalid_option"
WAITING_CV_VALUE = "waiting CV value"
SELECT_QAI = "select qai"


import json
with open("input/medibot/configurations.json","r", encoding="utf-8") as json_file:
	configurations = json.load(json_file)
	messages = configurations["messages"]



def new_user_context():
	context = {
		'state': WAITING_TO_START,
		'question': "",#Question in natural language
		'entities_found': [],
		'qai_id':-1, #QAI id classified
		'cvs_to_fill':[{'name':"",	'type':""}] ,#Names of recognized CVs yet to fill
		'cvs_filled':[{'name':""	,	'value:':""}] ,#Names of recognized CVs
		'original_cvec':[], #Original CVec parsed from the question
		'original_sv':[], #Original SV parsed from the question
		'options': [{'text':""	,	'value':""	,	'confidance':""}] #options asked to user
	}
	return context