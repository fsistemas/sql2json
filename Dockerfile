FROM python:3.10-slim

WORKDIR /src
COPY . /src
RUN pip install --no-cache-dir . psycopg2-binary PyMySQL

WORKDIR /workspace

ENTRYPOINT ["python", "-m", "sql2json"]
