web: bin/start-pgbouncer uvicorn rivendell.asgi:application --limit-max-requests=1200 --port $PORT --host 0.0.0.0
worker: python manage.py runworker channel_layer -v2