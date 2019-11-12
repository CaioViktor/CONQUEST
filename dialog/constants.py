WAITING_TO_START = "waiting to start"
WAITING_DESAMBIGUATION = "waiting desambiguation"
INVALID_OPTION = "invalid_option"



def new_user_context():
	context = {
		'state': WAITING_TO_START,
		'question': "",#Question in natural language
		'entities_found': [],
		'qai_id':-1, #QAI id classified
		'cvs_to_fill':[{'name':"",	'type':""}] ,#Names of recognized CVs yet to fill
		'cvs_filled':[{'name':""	,	'value:':""}] ,#Names of recognized CVs yet to fill
		'original_cvec':[], #Original CVec parsed from the question
		'original_sv':[], #Original SV parsed from the question
		'options': [{'text':""	,	'value':""	,	'confidance':""}] #options asked to user
	}
	return context