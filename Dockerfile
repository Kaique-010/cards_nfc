# syntax=docker/dockerfile:1
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    POETRY_VIRTUALENVS_CREATE=false \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# System deps
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       build-essential \
       libjpeg62-turbo-dev \
       zlib1g-dev \
       libpng-dev \
       curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python deps
COPY requirements.txt ./
RUN pip install --upgrade pip \
    && pip install -r requirements.txt \
    && pip install gunicorn

# Copy project
COPY . .

# Collect static (safe even if none)
RUN python manage.py collectstatic --noinput || true

EXPOSE 8000

CMD ["gunicorn", "card_nfc_project.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3"]


