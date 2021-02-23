FROM python:3.8-buster

ENV DEBIAN_FRONTEND noninteractive

RUN mkdir /app
WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

ARG MAPIT_KEY
ARG MAPIT_GENERATION=41
ARG ACCESS_KEY

ENV SERVER_PRODUCTION=TRUE MAPIT_KEY=$MAPIT_KEY ACCESS_KEY=$ACCESS_KEY  MAPIT_GENERATION=$MAPIT_GENERATION

COPY . .

RUN python fetch_resources.py

CMD ["python", "main.py"]