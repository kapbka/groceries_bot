# set base image (host OS)
FROM python:3.9

# set the working directory in the container
WORKDIR /code

RUN apt-get install -yqq unzip
RUN wget -O /tmp/chromedriver.zip http://chromedriver.storage.googleapis.com/`curl -sS chromedriver.storage.googleapis.com/LATEST_RELEASE`/chromedriver_linux64.zip
RUN unzip /tmp/chromedriver.zip chromedriver -d /usr/local/bin/

# copy the dependencies file to the working directory
COPY requirements.txt .

# install dependencies
RUN pip install -r requirements.txt

# copy the content of the local src directory to the working directory
COPY app/ app

ENV PYTHONPATH=/code
ENV INSIDE_DOCKER_CONTAINER=1

# command to run on container start
CMD [ "python", "./app/bot/telegram/main.py"]