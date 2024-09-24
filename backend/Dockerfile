FROM python:3.12.6-alpine3.20

WORKDIR /app

COPY ./requirements.txt .

RUN apk add --no-cache gcc musl-dev libffi-dev openssl-dev postgresql-dev && \
    pip install --no-cache-dir -r requirements.txt

COPY . .
