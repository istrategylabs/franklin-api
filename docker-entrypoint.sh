#!/bin/bash

# Migrate database
python manage.py migrate

exec $@
