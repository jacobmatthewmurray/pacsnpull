FROM python:3.7

MAINTAINER jacobmatthewmurray "jacobmatthewmurray@gmail.com"

COPY ./requirements.txt /pacsnpull/requirements.txt

WORKDIR /pacsnpull

RUN apt-get update -y && apt-get install -y dcmtk && apt-get install -y vim
RUN pip install -r requirements.txt
RUN export FLASK_APP=app
RUN export FLASK_ENV=production

COPY ./app /pacsnpull/app

