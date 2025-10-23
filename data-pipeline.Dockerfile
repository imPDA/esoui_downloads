FROM python:3.13-slim

RUN apt-get update && apt-get install -y xz-utils && rm -rf /var/lib/apt/lists/*

WORKDIR /app

RUN pip install --no-cache-dir fake-useragent pandas prefect requests psycopg2-binary sqlalchemy pyarrow fastparquet

COPY ./data_pipeline/src /app/src
COPY ./common/ /app/src/common

ENTRYPOINT ["python", "src/main.py"]
