WAITING_TO_START = "waiting to start"
WAITING_DESAMBIGUATION = "waiting desambiguation"
INVALID_OPTION = "invalid_option"
WAITING_CV_VALUE = "waiting CV value"
SELECT_QAI = "select qai"



messages = {
	'welcome': "Olá,\n Eu sou o $chatbot_name e estou aqui para lhe tirar dúvidas sobre medicamentos.",
	'empty_rensponse': "Desculpe, não encontrei nada sobre sua pergunta",
	"low_confidance" : "Desculpe, não entendi sua pergunta.",
	"invalid_option" : "A opção que você escolheu é inválida. Por favor, escolha uma opção válida:",
	"unkwon_question" : "Desculpe-me por não conseguir responder sua questão. Tentarei melhorar no futuro.",
	"ask_cv_question" : "Qual é o valor para $property para $class.\n Só lembrando um $property significa $property_comment.\n E $class significa $class_comment.",
	"ask_cv_question_without_information" : "Informe o valor para a $cv_name:",
	"Internal_error" : "Desculpe ocorreu um erro interno",
	"desambiguation_header" : "O que exatamente você quer saber:",
	"cancel_desambiugation" : "Nenhuma",
	"help" : "Consigo responder os seguintes tipos de questões:"
}

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