
FROM public.ecr.aws/docker/library/python:3.10-bullseye AS builder

ENV POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=1 \
    POETRY_VIRTUALENVS_CREATE=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache

RUN pip install poetry==1.8.0

ARG GITHUB_TOKEN=${GITHUB_TOKEN}
ARG GITHUB_USER=${GITHUB_USER}
ENV GITHUB_TOKEN=${GITHUB_TOKEN}

WORKDIR /app

COPY . /app

RUN git config --global http.https://github.com/.extraheader "AUTHORIZATION: basic $(echo -n x-access-token:${GITHUB_TOKEN} | base64)"
RUN poetry config http-basic.private-repo ${GITHUB_USER} ${GITHUB_TOKEN}


RUN --mount=type=cache,target=$POETRY_CACHE_DIR poetry install --no-root

RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

FROM public.ecr.aws/docker/library/python:3.10-slim AS runtime

ENV VIRTUAL_ENV=/app/.venv
ENV PATH="/app/.venv/bin:$PATH"

COPY --from=builder /app /app
WORKDIR /app

EXPOSE 8501

HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health


ENTRYPOINT ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
