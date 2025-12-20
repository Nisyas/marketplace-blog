import smtplib
from email.message import EmailMessage

from app.core.config import get_settings


settings = get_settings()


def send_registration_email(to_email: str) -> None:
    message = EmailMessage()
    message["Subject"] = "Регистрация в блоге маркетплейса"
    message["From"] = settings.email_from
    message["To"] = to_email

    text = (
        "Вы успешно зарегистрировались в блоге маркетплейса🥳.\n"
        "Спасибо, что присоединились к нашей платформе 🥰!"
    )

    message.set_content(text)

    with smtplib.SMTP(host=settings.smtp_host, port=settings.smtp_port) as smtp:
        if settings.smtp_use_tls:
            smtp.starttls()
        smtp.login(settings.smtp_user, settings.smtp_password)
        smtp.send_message(message)
