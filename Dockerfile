FROM python:3.8-buster as app

ENV PYTHONUNBUFFERED 1 \
    PIP_NO_CACHE_DIR=off
ENV CONSUL_HOST=${CONSUL_HOST:-notset}
ENV CONSUL_PORT=${CONSUL_PORT:-8500}
ENV DATAPUNT_API_URL=${DATAPUNT_API_URL:-https://bouwdossiers.amsterdam.nl/}
ARG JWKS_USE_TEST_KEY=true

RUN apt-get update \
 && apt-get dist-upgrade -y \
 && apt-get install --no-install-recommends -y \
        gdal-bin \
        postgresql-client-11 \
 && pip install --upgrade pip \
 && pip install uwsgi \
 && useradd --user-group --system datapunt

WORKDIR /app_install
ADD requirements.txt requirements.txt
RUN pip install -r requirements.txt

ADD deploy /deploy

WORKDIR /src
ADD src .

ARG SECRET_KEY=collectstatic
RUN python manage.py collectstatic --no-input

USER datapunt

CMD ["/deploy/docker-run.sh"]

# devserver
FROM app as dev

USER root
WORKDIR /app_install
ADD requirements_dev.txt requirements_dev.txt
RUN pip install -r requirements_dev.txt
RUN chmod -R a+r /app_install

WORKDIR /src
USER datapunt

# Any process that requires to write in the home dir
# we write to /tmp since we have no home dir
ENV HOME /tmp

CMD ["./manage.py", "runserver", "0.0.0.0"]

# tests
FROM dev as tests

USER datapunt

ENV COVERAGE_FILE=/tmp/.coverage

CMD ["pytest"]
