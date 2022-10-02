#!/bin/sh

python manage.py migrate
python manage.py loaddata cars/fixtures/models.json
exec "$@"
