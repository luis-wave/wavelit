format:
	black *.py
	isort .

app:
	python -m streamlit run app.py

reqs:
	poetry export -f requirements.txt --without-hashes -o requirements.txt
