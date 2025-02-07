import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'alx_travel_app.settings')

app = Celery('alx_travel_app', broker='amqp://localhost')

# Load task modules from all registered Django app configs.
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()