FROM amsterdam/python
MAINTAINER datapunt@amsterdam.nl

ENV PYTHONUNBUFFERED 1
ARG BOUWDOSSIERS_OBJECTSTORE_PASSWORD
ENV BOUWDOSSIERS_OBJECTSTORE_PASSWORD=$BOUWDOSSIERS_OBJECTSTORE_PASSWORD

EXPOSE 8000


ARG https_proxy=http://10.240.2.1:8080/
ENV https_proxy=$https_proxy

WORKDIR /app/
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

RUN mkdir -p /static && chown datapunt /static

ENV DJANGO_SETTINGS_MODULE=stadsarchief.settings.docker

COPY stadsarchief /app/
COPY .jenkins-import /.jenkins-import/

USER datapunt

RUN ./manage.py collectstatic

CMD uwsgi
