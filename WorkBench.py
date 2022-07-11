import os
from flask import Flask,render_template,request, redirect, url_for
import json
from datetime import date

app = Flask(__name__)


@app.route("/save_qai",methods=['POST'])
def save_qai():
	QAIs = json.loads(request.data)
	with open("input/configurations.json","r") as config_file:
		configurations = json.load(config_file)
	with open(configurations['QAIs_path'],"w") as QAIs_file:
		QAIs_string = json.dumps(QAIs,indent=4,ensure_ascii=False).encode('utf8').decode()
		QAIs_file.write(QAIs_string)
	return json.dumps({'success':True}), 200, {'ContentType':'application/json'}

@app.route("/update_configurations",methods=['POST'])
def update_configurations():
	configurations = {'messages': {}}
	for field in request.form:
		if field not in ["welcome","empty_rensponse","low_confidance","invalid_option","unkwon_question","ask_cv_question","ask_cv_question_without_information","Internal_error","desambiguation_header","cancel_desambiugation","help"]:
			if field in ["min_confidance_classification","min_diference_confidance"]:
				configurations[field] = float(request.form[field])
			elif field in ["number_desambiguation_options","steps_to_update"]:
				configurations[field] = int(request.form[field])
			else:
				configurations[field] = request.form[field]
		else:
			configurations['messages'][field] = request.form[field]
	with open("input/configurations.json","w") as configurations_file:
		configurations_json = json.dumps(configurations,indent=4,ensure_ascii=False).encode('utf8').decode()
		configurations_file.write(configurations_json)
	return redirect(url_for("index",message="Configurations Updated!"))



@app.route("/developing_tester")
def developing_tester():
	return render_template('developing_tester.html')

@app.route("/templates")
def templates():
	today = date.today().strftime("%Y-%m-%d")
	with open("input/configurations.json","r") as config_file:
		configurations = json.load(config_file)	
	with open(configurations['QAIs_path'],"r") as templates_file:
		templates = json.load(templates_file)
	if "message" in request.values:
		message = request.values['message']
	else:
		message = ""
	return render_template('templates.html',templates=templates,today=today,message=message)

@app.route("/")
def index():
	with open("input/configurations.json","r") as config_file:
		configurations = json.load(config_file)
	if "message" in request.values:
		message = request.values['message']
	else:
		message = ""
	return render_template('index.html',configurations=configurations,configurations_json = json.dumps(configurations,indent=4,ensure_ascii=False).encode('utf8').decode(),message=message)


if __name__ == "__main__":
	#app.run(host='200.19.182.252')
	app.run(host='0.0.0.0',port="5050")
