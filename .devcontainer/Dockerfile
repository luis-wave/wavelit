FROM mcr.microsoft.com/devcontainers/python:3.10-bullseye

# Set environment variables for Poetry
ENV POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=1 \
    POETRY_VIRTUALENVS_CREATE=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Switch to non-root user for development
USER vscode
WORKDIR /workspaces/mywaveanalytics

# Add vscode user's .local/bin to PATH
ENV PATH="/home/vscode/.local/bin:$PATH"

# Install Poetry for the vscode user
RUN pip install poetry==1.8.0

# Configure Poetry to create virtual environments in-project
RUN poetry config virtualenvs.in-project true
