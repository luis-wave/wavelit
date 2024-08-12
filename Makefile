format:
	black *.py
	isort .

local_app:
	python -m streamlit run home.py

app:
	docker run -p 8501:8501 streamlit-epoch


sigma:
	python -m streamlit run protocols.py

reqs:
	poetry export -f requirements.txt --without-hashes -o requirements.txt

