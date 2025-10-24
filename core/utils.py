import random
from django.core.mail import EmailMessage
from django.conf import settings


def generate_otp() -> str:
    return f"{random.randint(0, 999999):06d}"


def send_otp_email(email: str, code: str, subject: str = 'Your OTP Code'):
    body = f"Your OTP code is: {code}. It expires in 5 minutes."
    msg = EmailMessage(subject=subject, body=body, from_email=settings.DEFAULT_FROM_EMAIL, to=[email])
    msg.send(fail_silently=True)
