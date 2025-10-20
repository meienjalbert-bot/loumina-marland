FROM python:3.11-slim

WORKDIR /app
COPY apps/server/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY apps/server /app/apps/server
COPY agents /app/agents

ENV PYTHONUNBUFFERED=1
EXPOSE 8080
CMD ["python", "-m", "apps.server.main"]
