FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends build-essential libpq-dev \
  && rm -rf /var/lib/apt/lists/*

COPY apps/api/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY apps/api/app ./app
COPY apps/api/docker_entrypoint.sh ./docker_entrypoint.sh
COPY data ./data
COPY scripts ./scripts
RUN chmod +x docker_entrypoint.sh

ENV PYTHONPATH=/app
ENV PORT=8000
EXPOSE 8000

CMD ["./docker_entrypoint.sh"]
