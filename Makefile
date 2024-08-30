format:
	ruff format
	isort .

lint:
	ruff check .

local_app:
	python -m streamlit run home.py

app:
	docker run -p 8501:8501 streamlit-epoch-dev


sigma:
	python -m streamlit run protocols.py

reqs:
	poetry export -f requirements.txt --without-hashes -o requirements.txt

