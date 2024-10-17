format:
	ruff format
	isort .

lint:
	ruff check .

local_app:
	python -m streamlit run home.py

simulation:
	python -m streamlit run simulation.py

app:
	docker run -p 8501:8501 streamlit-epoch

dev:
	docker run -p 8501:8501 streamlit-epoch-dev

mert:
	python -m streamlit run streamlit_apps/reports.py

sigma:
	python -m streamlit run protocols.py

reqs:
	poetry export -f requirements.txt --without-hashes -o requirements.txt

