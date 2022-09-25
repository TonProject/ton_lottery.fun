FROM ubuntu:18.04
RUN apt-get -y update && \
    apt-get -y upgrade && \
    apt-get -y install git && \
    apt-get -y install cmake && \
    apt-get -y install libssl-dev && \
    apt-get -y install g++ && \
    apt-get -y install zlib1g-dev && \
    apt-get -y install wget && \
    apt-get -y install python3 && \
    apt-get -y install python3-pip  
FROM python:3.9
COPY . /home/
WORKDIR /home
RUN pip3 install -e .
ENTRYPOINT FLASK_APP=app.py flask run --host=0.0.0.0
