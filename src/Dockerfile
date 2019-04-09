FROM amsterdam/python
MAINTAINER datapunt@amsterdam.nl

ENV PYTHONUNBUFFERED 1
ENV CONSUL_HOST=${CONSUL_HOST:-notset}
ENV CONSUL_PORT=${CONSUL_PORT:-8500}
ENV DATAPUNT_API_URL=${DATAPUNT_API_URL:-https://api.data.amsterdam.nl/}
ARG BOUWDOSSIERS_OBJECTSTORE_PASSWORD
ENV BOUWDOSSIERS_OBJECTSTORE_PASSWORD=$BOUWDOSSIERS_OBJECTSTORE_PASSWORD
ARG https_proxy=http://10.240.2.1:8080/
ENV https_proxy=$https_proxy


EXPOSE 8000

WORKDIR /app

# CI hook - see .jenkins/README.TXT
COPY .jenkins /.jenkins
COPY .jenkins/docker-migrate.sh /app/

COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt
COPY . /app/

USER datapunt

RUN export DJANGO_SETTINGS_MODULE=stadsarchief.settings

CMD uwsgi

