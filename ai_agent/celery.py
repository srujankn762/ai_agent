import os

from celery import Celery

hhh
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ai_agent.settings")

app = Celery("ai_agent")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
