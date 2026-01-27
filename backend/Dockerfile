FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN pip install --no-cache-dir --upgrade pip

COPY pyproject.toml /app/pyproject.toml
COPY README.md /app/README.md
COPY app /app/app
RUN pip install --no-cache-dir .

EXPOSE 8000
