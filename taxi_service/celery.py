import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "taxi_service.settings")

app = Celery("taxi_service")

app.config_from_object("django.conf:settings", namespace="CELERY")

app.autodiscover_tasks()
