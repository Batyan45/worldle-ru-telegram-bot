FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive \
    DATA_DIR=/app/data \
    USER_DATA_FILE=/app/data/user_data.json \
    LOGS_DIR=/app/data/logs \
    GAME_LOGS_FILE=/app/data/logs/game_logs.log

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
        tini \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

COPY . .

ARG UID=1000
ARG GID=1000
RUN groupadd -g ${GID} botuser \
    && useradd -m -u ${UID} -g ${GID} botuser \
    && mkdir -p /app/data/logs \
    && chown -R botuser:botuser /app

VOLUME ["/app/data"]

USER botuser

ENTRYPOINT ["/usr/bin/tini", "--"]
CMD ["python", "-m", "src.main"]
