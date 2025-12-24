from app.services.email import send_registration_email
from app.tasks.celery_app import celery_app


@celery_app.task(name="send_registration_email_task")
def send_registration_email_task(to_email: str) -> None:
    send_registration_email(to_email)
