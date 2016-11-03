FROM ubuntu:16.04


RUN apt-get update && apt-get install -y python
#RUN pip install git+https://github.com/dpallot/simple-websocket-server.git
RUN apt-get install -y python-pip python-dev build-essential 
RUN pip install tornado

ADD ./app /app
