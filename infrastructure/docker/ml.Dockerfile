FROM python:3.10-slim

WORKDIR /app
COPY ml/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ml/common ./common
EXPOSE 8080
