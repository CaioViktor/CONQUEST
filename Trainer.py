#CONQUEST Trainer
#Module used for chat chat training for the interactive question answering task on closed domain knowledge bases.


import plac
from pathlib import Path

@plac.annotations(
    model=("Model name. Defaults to blank 'en' model.", "option", "m", str),
    output_dir=("Optional output directory", "option", "o", Path),
    n_iter=("Number of training iterations", "option", "n", int),
)

def main(model=None, output_dir=None, n_iter=100):
	return




if __name__ == "__main__":
    plac.call(main)