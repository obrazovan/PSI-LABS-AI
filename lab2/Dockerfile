# syntax=docker/dockerfile:1
FROM python:3.12-slim AS base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PORT=8000 \
    HOST=0.0.0.0

WORKDIR /app

# Системные зависимости
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Зависимости Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Исходный код приложения
COPY pyproject.toml .
COPY README.md .
COPY run_web.py .
COPY run.py .
COPY src/ ./src/
COPY sample_data/ ./sample_data/
COPY students.xlsx .
COPY tickets.docx .
COPY results.xlsx .

# Установка пакета в редактируемом режиме
RUN pip install --no-deps -e .

EXPOSE 8000

HEALTHCHECK --interval=15s --timeout=3s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/api/init || exit 1

CMD ["python", "run_web.py", "--host", "0.0.0.0", "--port", "8000"]
