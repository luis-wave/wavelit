format:
	black *.py
	isort .

app:
	python -m streamlit run home2.py

sigma:
	python -m streamlit run protocols.py

reqs:
	poetry export -f requirements.txt --without-hashes -o requirements.txt

