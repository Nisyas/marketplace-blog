import smtplib
from email.message import EmailMessage

from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)
from loguru import logger
from app.core.config import get_settings


settings = get_settings()


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    retry=retry_if_exception_type((smtplib.SMTPException, ConnectionError)),
)
def send_registration_email(to_email: str) -> None:
    logger.info("Preparing registration email: to_email={to_email}", to_email=to_email)

    if not to_email or "@" not in to_email:
        logger.warning("Invalid email address for registration email: to_email={to_email}", to_email=to_email)
        raise ValueError("Invalid email address")

    message = EmailMessage()
    message["Subject"] = "Регистрация в блоге маркетплейса"
    message["From"] = settings.email_from
    message["To"] = to_email

    text = (
        "Вы успешно зарегистрировались в блоге маркетплейса🥳.\n"
        "Спасибо, что присоединились к нашей платформе 🥰!"
    )
    message.set_content(text)

    try:
        logger.debug(
            "Connecting to SMTP server: host={host} port={port} use_tls={use_tls}",
            host=settings.smtp_host,
            port=settings.smtp_port,
            use_tls=settings.smtp_use_tls,
        )

        with smtplib.SMTP(
            host=settings.smtp_host,
            port=settings.smtp_port,
            timeout=30,
        ) as smtp:
            if settings.smtp_use_tls:
                smtp.starttls()
                logger.debug("SMTP TLS started")

            smtp.login(settings.smtp_user, settings.smtp_password)
            logger.debug("SMTP login successful: user={user}", user=settings.smtp_user)

            smtp.send_message(message)

        logger.info("Registration email sent successfully: to_email={to_email}", to_email=to_email)

    except smtplib.SMTPAuthenticationError as e:
        logger.error("SMTP authentication failed: error={error}", error=str(e))
        raise RuntimeError(f"SMTP authentication failed: {e}") from e
    except smtplib.SMTPServerError as e:
        logger.error("SMTP server error: error={error}", error=str(e))
        raise RuntimeError(f"SMTP server error: {e}") from e
