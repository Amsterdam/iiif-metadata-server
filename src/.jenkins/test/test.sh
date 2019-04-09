#!/usr/bin/env bash

set -u # crash on missing env
set -e # stop on any error

echo "Waiting for db"
source .jenkins/docker-wait.sh
source .jenkins/docker-migrate.sh

echo "Running style checks"
flake8 --config=./tests/flake.cfg ./stadsarchief

echo "Running unit tests"
./manage.py test
