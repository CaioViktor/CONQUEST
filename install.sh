#!/bin/bash
echo "Installing dependecies..."
pip install -r requirements.txt
python -c "import nltk; nltk.download('punkt')"
cd persistence/nlp/
echo "Downloading Sorl..."
wget -O sorl.tar.xz "https://sourceforge.net/projects/conquest-sqai/files/solr.tar.xz/download"
echo "Extracting Solr..."
tar xf sorl.tar.xz
echo "Downloading NLP model pt-br..."
wget -O model.tar.xz "https://sourceforge.net/projects/conquest-sqai/files/model_pt-br.tar.xz/download"
echo "Extracting model..."
tar xf model.tar.xz
echo "Removing temporary files..."
echo "Removing sorl.tar.xz"
rm -R sorl.tar.xz
echo "Removing model.tar.xz"
rm -R model.tar.xz
echo "Installation completed. Run CONQUEST Trainer with 'python Trainer.py'."