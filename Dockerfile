FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential git curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt requirements_dashboard.txt ./
RUN python -m pip install --upgrade pip \
    && python -m pip install -r requirements.txt -r requirements_dashboard.txt \
    && python -m pip install jupyterlab papermill ipykernel

COPY . .
RUN mkdir -p data/raw data/processed outputs/figures outputs/interactive outputs/tables outputs/networks outputs/report_assets outputs/run_logs outputs/executed_notebooks

EXPOSE 8000 8888

CMD ["bash", "docker/start_jupyter.sh"]
