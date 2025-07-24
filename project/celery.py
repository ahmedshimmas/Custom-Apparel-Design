import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')

app = Celery('project')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()


# app.conf.beat_schedule = {
#     'delete-unverified-users-daily': {
#         'task': 'users.tasks.delete_unverified_users',
#         'schedule': crontab(hour=0, minute=0),  # every day at midnight
#         # OR: 'schedule': timedelta(days=1),
#     },
# }