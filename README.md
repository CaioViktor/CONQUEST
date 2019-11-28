# CONQUEST
CONQUEST (Chatbot ONtology QUESTion) is a framework that automates much of the construction process of chatbots for the task of template-based Interactive Question Answering on closed-domain knowledge bases.

<h2>Installation</h2>
<h3>Automatic Installation</h3><br>
Just run the script "install.sh"<br>
<code>$./install.sh</code>

<h3>Manual Installation</h3><br>
<ul>
	<li><code>$pip install -r requirements.txt</code></li>
	<li><code>$python -c "import nltk; nltk.download('punkt')"</code></li>
	<li>Download the file "sorl.tar.xz" from <a href="https://sourceforge.net/projects/conquest-sqai/files/solr.tar.xz/download">https://sourceforge.net/projects/conquest-sqai/files/solr.tar.xz/download</a></li>
	<li>Extract the "sorl.tar.xz" file in "persistence/nlp" keeping the name "sorl"</li>
	<li>Download the file "model.tar.xz" from <a href="https://sourceforge.net/projects/conquest-sqai/files/model_pt-br.tar.xz/download">https://sourceforge.net/projects/conquest-sqai/files/model_pt-br.tar.xz/download</a></li>
	<li>Extract the "model.tar.xz file in "persistence/nlp" keeping the name "model"</li>
	<li>Remove temporary files</li>
</ul>


<h2>Trainer</h2>
<h3>To run the training script:</h3>
	<code>$python Trainer.py</code>
	<br/>
	<pre>
		usage: python Trainer.py [-h] [-m zero] [-p 0]
		optional arguments:
		  -h, --help            show this help message and exit 
		  -m zero, --mode zero  Training mode: 
		  						zero - Training the chatbot from starting point (default).
		  						update - Update models
		                        resume - Resume the training from a saved point.
		  -p 0, --point 0       Point to resume training:
		  							0 - Starting from start (equal to zero mode).
		  							1 - Starting from loading QAIs.
		                        	2 - Starting from making NER training dataset.
		                        	3 - Starting from training NER. 
		                        	4 - Starting from making classifier training dataset. 
		                        	5 - Starting from training the classifier.
	</pre>
<h2>Server</h2>
<h3>To run the server script:</h3>
	<code>$python Server.py</code>