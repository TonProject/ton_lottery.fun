FROM ubuntu:18.04
RUN apt-get -y update && \
    apt-get -y upgrade && \
    apt-get -y install git && \
    apt-get -y install python3 && \
    apt-get -y install python3-pip  
FROM python:3.9
RUN pip install --upgrade pip
RUN pip install requests
COPY . /home/
WORKDIR /home
RUN pip3 install -e .
ENTRYPOINT FLASK_APP=app.py flask run --host=0.0.0.0
