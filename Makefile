format:
	black *.py
	isort .

app:
	python -m streamlit run home.py

reqs:
	poetry export -f requirements.txt --without-hashes -o requirements.txt
