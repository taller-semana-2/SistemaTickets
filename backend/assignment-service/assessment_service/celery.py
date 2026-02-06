# assessment_service/celery.py
import os
from celery import Celery

# Configura Django para Celery
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'assessment_service.settings')

app = Celery('assessment_service')

# Cargar configuración desde settings.py
app.config_from_object('django.conf:settings', namespace='CELERY')

# Detectar tareas en todas las apps instaladas
app.autodiscover_tasks()
