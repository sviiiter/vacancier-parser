FROM python:3.12-slim

WORKDIR /app

# Install supercronic — a container-friendly cron daemon (no root daemon, respects env vars)
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl ca-certificates \
    && curl -fsSL "https://github.com/aptible/supercronic/releases/download/v0.2.29/supercronic-linux-amd64" \
       -o /usr/local/bin/supercronic \
    && chmod +x /usr/local/bin/supercronic \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENTRYPOINT ["supercronic", "/app/crontab"]
