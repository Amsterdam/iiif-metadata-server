ARG PYTHON_VERSION=3.13

# Builder
FROM python:${PYTHON_VERSION}-slim-bookworm AS builder

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED 1

RUN set -eux && \
    python -m ensurepip --upgrade && \
    apt-get update && apt-get install -y gcc && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

WORKDIR /app/install

COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt


FROM python:${PYTHON_VERSION}-slim-bookworm AS app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED 1

ENV CONSUL_HOST=${CONSUL_HOST:-notset}
ENV CONSUL_PORT=${CONSUL_PORT:-8500}

ARG USE_JWKS_TEST_KEY=true

RUN set -eux && \
    python -m ensurepip --upgrade && \
    apt-get update && apt-get install -y \
        libgeos3.11.1 \
        gdal-bin && \
    useradd --user-group --system datapunt && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Copy the Python dependencies from the builder stage
COPY --from=builder /usr/local/lib/python3.13/site-packages/ /usr/local/lib/python3.13/site-packages/
COPY --from=builder /usr/local/bin/ /usr/local/bin

WORKDIR /app/src
COPY src .

ARG SECRET_KEY=collectstatic
RUN python manage.py collectstatic --no-input

USER datapunt
WORKDIR /app/src

CMD ["uwsgi", "--ini", "/app/src/main/uwsgi.ini"]

# devserver
FROM app AS dev

USER root
WORKDIR /app/install

COPY requirements_dev.txt requirements_dev.txt

RUN pip install --no-cache-dir -r requirements_dev.txt

WORKDIR /app/src
USER datapunt

# Any process that requires to write in the home dir
# we write to /tmp since we have no home dir
ENV HOME /tmp

CMD ["./manage.py", "runserver", "0.0.0.0"]

# tests
FROM dev AS tests

WORKDIR /app
USER datapunt

COPY pyproject.toml pyproject.toml

ENV COVERAGE_FILE=/tmp/.coverage

CMD ["pytest"]

# linting
FROM python:${PYTHON_VERSION}-alpine AS linting

WORKDIR /app
COPY . .

RUN pip install --no-cache-dir -r requirements_linting.txt
