FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    mtr \
    iputils-ping \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml poetry.lock* ./
COPY src/ ./src/

RUN pip install --no-cache-dir poetry && \
    poetry config virtualenvs.create false && \
    poetry install --no-dev

ENV PYTHONUNBUFFERED=1
ENV LOG_LEVEL=INFO
ENV METRICS_PORT=8000
ENV API_PORT=5000

EXPOSE 5000 8000

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5000/api/health')"

# 默认启动 API 服务器（前端+后端）
CMD ["python", "-m", "src.gateway", "--host", "0.0.0.0", "--port", "5000"]
