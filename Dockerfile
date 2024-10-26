FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive \
    TELEGRAM_BOT_TOKEN=your-code

WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc \
    git \
    && rm -rf /var/lib/apt/lists/*

RUN git clone https://github.com/Batyan45/worldle-ru-telegram-bot.git .

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p /app/data

RUN useradd -m botuser && \
    chown -R botuser:botuser /app
USER botuser

VOLUME ["/app/data"]

CMD ["python", "main.py"]
