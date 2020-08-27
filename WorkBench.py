import os
from flask import Flask,render_template,request, redirect, url_for
import json

app = Flask(__name__)


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
	return render_template('templates.html')

@app.route("/")
def index():
	with open("input/medibot/configurations.json","r") as config_file:
		configurations = json.load(config_file)
	if "message" in request.values:
		message = request.values['message']
	else:
		message = ""
	return render_template('index.html',configurations=configurations,configurations_json = json.dumps(configurations,indent=4,ensure_ascii=False).encode('utf8').decode(),message=message)


if __name__ == "__main__":
	#app.run(host='200.19.182.252')
	app.run(host='0.0.0.0',port="5050")
