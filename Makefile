all:
	python3 src/scripts/step_chunk.py
	python3 src/scripts/step2_ner.py
	python3 src/scripts/step_disambiguate.py
	python3 src/scripts/step3_re.py