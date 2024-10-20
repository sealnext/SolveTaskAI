FROM python:3.12.6-alpine3.20

WORKDIR /app

RUN apk add --no-cache gcc musl-dev libffi-dev openssl-dev postgresql-dev curl cargo && \
    curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y && \
    source $HOME/.cargo/env && \
    export PATH="$HOME/.cargo/bin:$PATH"


COPY ./requirements.txt .

RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY . .
