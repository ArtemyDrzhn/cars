FROM python:3.10-slim

WORKDIR /app/backend

COPY ./requirements.txt ./requirements.txt
RUN apt-get update \
&& apt-get install gcc -y \
&& apt-get clean
RUN pip install --upgrade pip
RUN pip install -r ./requirements.txt
