# syntax=docker/dockerfile:1
FROM python:3.9-slim-bullseye AS python

ENV PYTHONUNBUFFERED 1
WORKDIR /marsbots

COPY . .

RUN apt-get update && apt-get install -y git

RUN pip install -r requirements.txt

RUN chmod +x entrypoint.sh
RUN cp entrypoint.sh /tmp/entrypoint.sh

ENTRYPOINT ["/tmp/entrypoint.sh"]
