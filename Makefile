format:
	black *.py
	isort .

app:
	python -m streamlit run app.py