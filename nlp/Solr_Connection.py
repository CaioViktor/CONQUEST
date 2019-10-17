import os

solr_path = "persistence/nlp/solr/bin/"
def startup(port=8983,memory="1g"):
	print("Starting Sorl from {} in port {} with {} of memory...".format(solr_path,port,memory))
	if os.name == "nt":
		#Running on Windows
		os.system("{}solr start -p {} -m {}".format(solr_path,str(port),memory))
	else:
		#Running on Linux or Mac, or other strange OS
		os.system("./{}solr start -p {} -m {}".format(solr_path,str(port),memory))

def stop():
	print("Stoping all Solr instances...")
	if os.name == "nt":
		#Running on Windows
		os.system("{}solr stop -all".format(solr_path))
	else:
		#Running on Linux or Mac, or other strange OS
		os.system("./{}solr stop -all".format(solr_path))	
