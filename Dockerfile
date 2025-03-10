# Builder stage
FROM public.ecr.aws/docker/library/python:3.10-bullseye AS builder

ENV POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=1 \
    POETRY_VIRTUALENVS_CREATE=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache

RUN pip install poetry==1.8.0

ARG GITHUB_TOKEN
ARG GITHUB_USER
ENV GITHUB_TOKEN=${GITHUB_TOKEN}

ARG BASE_URL
ARG CLINICAL_USERNAME
ARG CLINICAL_PASSWORD
ARG CLINICAL_API_KEY
ARG CONSUMER_USERNAME
ARG CONSUMER_PASSWORD
ARG CONSUMER_API_KEY

ARG SIGMA_REPORT_URL
ARG SIGMA_PROTOCOLS_URL
ARG SIGMA_PROTOCOLS_MINI_URL
ARG SIGMA_REPORT_LOGS_URL

ARG APP_CYBERMED_CLOUD_URL
ARG APP_CYBERMED_CLOUD_PROJECT_PREFIX
ARG APP_CYBERMED_CLOUD_USERNAME
ARG APP_CYBERMED_CLOUD_PASSWORD
ARG APP_MACRO_SERVICE_URL
ARG TARGET_CLINIC_ID
ARG APP_CYBERMED_SCIENTIST_PASSWORD
ARG APP_CYBERMED_SCIENTIST_USERNAME


ARG SIGMA_DODS_KPI_URL
ARG SIGMA_DODS_CLINICS_URL
ARG DODS_PATIENT_DASHBOARD
ARG SIGMA_DODS_AB_DBOARD
ARG APP_NEURALINK_SERVICE_URL
ARG PROTOCOL_FFT_ONLY

ENV BASE_URL=${BASE_URL}
ENV CLINICAL_USERNAME=${CLINICAL_USERNAME}
ENV CLINICAL_PASSWORD=${CLINICAL_PASSWORD}
ENV CLINICAL_API_KEY=${CLINICAL_API_KEY}

ENV CONSUMER_USERNAME=${CONSUMER_USERNAME}
ENV CONSUMER_PASSWORD=${CONSUMER_PASSWORD}
ENV CONSUMER_API_KEY=${CONSUMER_API_KEY}

ENV SIGMA_REPORT_URL=${SIGMA_REPORT_URL}
ENV SIGMA_PROTOCOLS_URL=${SIGMA_PROTOCOLS_URL}
ENV SIGMA_PROTOCOLS_MINI_URL=${SIGMA_PROTOCOLS_MINI_URL}
ENV SIGMA_REPORT_LOGS_URL=${SIGMA_REPORT_LOGS_URL}


ENV APP_CYBERMED_CLOUD_URL=${APP_CYBERMED_CLOUD_URL}
ENV APP_CYBERMED_CLOUD_PROJECT_PREFIX=${APP_CYBERMED_CLOUD_PROJECT_PREFIX}
ENV APP_CYBERMED_CLOUD_USERNAME=${APP_CYBERMED_CLOUD_USERNAME}
ENV APP_CYBERMED_CLOUD_PASSWORD=${APP_CYBERMED_CLOUD_PASSWORD}
ENV APP_MACRO_SERVICE_URL=${APP_MACRO_SERVICE_URL}
ENV TARGET_CLINIC_ID=${TARGET_CLINIC_ID}
ENV APP_CYBERMED_SCIENTIST_PASSWORD=${APP_CYBERMED_SCIENTIST_PASSWORD}
ENV APP_CYBERMED_SCIENTIST_USERNAME=${APP_CYBERMED_SCIENTIST_USERNAME}
ENV SIGMA_DODS_KPI_URL=${SIGMA_DODS_KPI_URL}
ENV SIGMA_DODS_CLINICS_URL=${SIGMA_DODS_CLINICS_URL}
ENV DODS_PATIENT_DASHBOARD=${DODS_PATIENT_DASHBOARD}
ENV SIGMA_DODS_AB_DBOARD=${SIGMA_DODS_AB_DBOARD}
ENV APP_NEURALINK_SERVICE_URL=${APP_NEURALINK_SERVICE_URL}
ENV PROTOCOL_FFT_ONLY = ${https://app.sigmacomputing.com/embed/1-6hsbQEZPyTYKlZ6hGs1oC8}

WORKDIR /app

COPY . /app

RUN git config --global http.https://github.com/.extraheader "AUTHORIZATION: basic $(echo -n x-access-token:${GITHUB_TOKEN} | base64)"
RUN poetry config http-basic.private-repo ${GITHUB_USER} ${GITHUB_TOKEN}

RUN --mount=type=cache,target=$POETRY_CACHE_DIR poetry install --no-root

RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Runtime stage
FROM public.ecr.aws/docker/library/python:3.10-slim AS runtime

ARG BASE_URL
ARG CLINICAL_USERNAME
ARG CLINICAL_PASSWORD
ARG CLINICAL_API_KEY
ARG CONSUMER_USERNAME
ARG CONSUMER_PASSWORD
ARG CONSUMER_API_KEY

ARG SIGMA_REPORT_URL
ARG SIGMA_PROTOCOLS_URL
ARG SIGMA_PROTOCOLS_MINI_URL
ARG SIGMA_REPORT_LOGS_URL

ARG APP_CYBERMED_CLOUD_URL
ARG APP_CYBERMED_CLOUD_PROJECT_PREFIX
ARG APP_CYBERMED_CLOUD_USERNAME
ARG APP_CYBERMED_CLOUD_PASSWORD
ARG APP_MACRO_SERVICE_URL
ARG TARGET_CLINIC_ID
ARG APP_CYBERMED_SCIENTIST_PASSWORD
ARG APP_CYBERMED_SCIENTIST_USERNAME


ARG SIGMA_DODS_KPI_URL
ARG SIGMA_DODS_CLINICS_URL
ARG DODS_PATIENT_DASHBOARD
ARG SIGMA_DODS_AB_DBOARD
ARG APP_NEURALINK_SERVICE_URL
ARG PROTOCOL_FFT_ONLY

ENV VIRTUAL_ENV=/app/.venv
ENV PATH="/app/.venv/bin:$PATH"

ENV BASE_URL=${BASE_URL}
ENV CLINICAL_USERNAME=${CLINICAL_USERNAME}
ENV CLINICAL_PASSWORD=${CLINICAL_PASSWORD}
ENV CLINICAL_API_KEY=${CLINICAL_API_KEY}

ENV CONSUMER_USERNAME=${CONSUMER_USERNAME}
ENV CONSUMER_PASSWORD=${CONSUMER_PASSWORD}
ENV CONSUMER_API_KEY=${CONSUMER_API_KEY}

ENV SIGMA_REPORT_URL=${SIGMA_REPORT_URL}
ENV SIGMA_PROTOCOLS_URL=${SIGMA_PROTOCOLS_URL}
ENV SIGMA_PROTOCOLS_MINI_URL=${SIGMA_PROTOCOLS_MINI_URL}
ENV SIGMA_REPORT_LOGS_URL=${SIGMA_REPORT_LOGS_URL}


ENV APP_CYBERMED_CLOUD_URL=${APP_CYBERMED_CLOUD_URL}
ENV APP_CYBERMED_CLOUD_PROJECT_PREFIX=${APP_CYBERMED_CLOUD_PROJECT_PREFIX}
ENV APP_CYBERMED_CLOUD_USERNAME=${APP_CYBERMED_CLOUD_USERNAME}
ENV APP_CYBERMED_CLOUD_PASSWORD=${APP_CYBERMED_CLOUD_PASSWORD}
ENV APP_MACRO_SERVICE_URL=${APP_MACRO_SERVICE_URL}
ENV TARGET_CLINIC_ID=${TARGET_CLINIC_ID}
ENV APP_CYBERMED_SCIENTIST_PASSWORD=${APP_CYBERMED_SCIENTIST_PASSWORD}
ENV APP_CYBERMED_SCIENTIST_USERNAME=${APP_CYBERMED_SCIENTIST_USERNAME}
ENV SIGMA_DODS_KPI_URL=${SIGMA_DODS_KPI_URL}
ENV SIGMA_DODS_CLINICS_URL=${SIGMA_DODS_CLINICS_URL}
ENV DODS_PATIENT_DASHBOARD=${DODS_PATIENT_DASHBOARD}
ENV SIGMA_DODS_AB_DBOARD=${SIGMA_DODS_AB_DBOARD}
ENV APP_NEURALINK_SERVICE_URL=${APP_NEURALINK_SERVICE_URL}
ENV PROTOCOL_FFT_ONLY = ${https://app.sigmacomputing.com/embed/1-6hsbQEZPyTYKlZ6hGs1oC8}

COPY --from=builder /app /app
WORKDIR /app

EXPOSE 8501

HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health

ENTRYPOINT ["streamlit", "run", "home.py", "--server.port=8501", "--server.address=0.0.0.0"]
