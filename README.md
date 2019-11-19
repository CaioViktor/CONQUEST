# CONQUEST
Chatbot ONtology QUESTion

<h2>Dependencies</h2>

<ul>
	<li>RDFLib:
		<ul>
			<li>easy_install rdflib	</li>
		</ul>
	</li>
	<li>SPARQLWrapper:
		<ul><li>pip install SPARQLWrapper</li></ul>
	</li>
	<li>Pandas:
		<ul>
			<li>pip install numpy</li>
			<li>pip install pandas</li>
		</ul>
	</li>
	<li>SpaCy:
		<ul>
			<li>pip install -U spacy</li>
			<li>python -m spacy download en_core_web_sm</li> (Using small model by default)
			<li>python -m spacy download pt_core_news_sm</li>
		</ul>
	</li>
	<li>SciKit Learn:
		<ul>
			<li>pip install -U scikit-learn</li>
		</ul>
	</li>
	<li>dateparser:
		<ul>
			<li>pip install dateparser</li>
		</ul>
	</li>
	<li>PySolr:
		<ul>
			<li>pip install pysolr</li>
		</ul>
	</li>
	<li>NLTK:
		<ul>
			<li>pip install nltk</li>
			<li>Run: import nltk <br/> nltk.download('punkt')</li>
		</ul>
	</li>
	<li> Flask:
		<ul>
			<li>pip install Flask</li>
		</ul>
	</li>
	<li> Telegram Bot:
		<ul>
			<li>pip install python-telegram-bot</li>
		</ul>
	</li>
</ul>

<h2>Trainer</h2>
<h3>Before running CONQUEST Trainer:</h3>
<p>Download the file "sorl.tar.xz" from <a href="https://drive.google.com/open?id=115uyd5Hqtoq_wirX-7Xtwon3QdVsnaga">https://drive.google.com/open?id=115uyd5Hqtoq_wirX-7Xtwon3QdVsnaga</a></p>
<p>Extract the "sorl.tar.xz" file in "persistence/nlp" keeping the name "sorl"</p>
<h3>To run the training script:</h3>
	<p>python Trainer</p>
	<br/>
	usage: python Trainer.py [-h] [-m zero] [-p 0]
	optional arguments:
	  -h, --help            show this help message and exit
	  -m zero, --mode zero  Training mode: zero - Training the chatbot from
	                        starting point (default). resume - Resume the training
	                        from a saved point. update - Update models
	  -p 0, --point 0       Point to resume training. 0 - Starting from start
	                        (equal to zero mode). 1 - Starting from loading QAIs.
	                        2 - Starting from making NER training dataset. 3 -
	                        Starting from training NER. 4 - Starting from making
	                        classifier training dataset. 5 - Starting from
	                        training the classifier.