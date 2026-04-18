import json
import re

from django.core.exceptions import ImproperlyConfigured

from chat.services.prompts import EMAIL_CONTENT_PROMPT
from chat.tasks import send_email_task


class QueuedEmailMessage:
    def __init__(self, subject, body, to):
        self.subject = subject
        self.body = body
        self.to = to or []

    def send(self, fail_silently=False):
        if not self.to:
            if fail_silently:
                return 0
            raise ValueError("Recipient email is required to send an email")

        send_email_task.delay(
            subject=self.subject,
            body=self.body,
            recipients=self.to,
        )
        return "email will be sent"


def get_wallet_balance(user_id):
    # mock for now
    return {
        "balance": 100.12,
        "currency": "INR"
    }


def search_documents(query, rag_response_generator):
    return rag_response_generator(query)


EMAIL_REGEX = r"([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,})"




def extract_email_recipients(user_message):
    return list(dict.fromkeys(re.findall(EMAIL_REGEX, user_message or "")))


def normalize_recipients(recipients=None, user_message=None):
    if recipients is None:
        return extract_email_recipients(user_message)

    if isinstance(recipients, str):
        recipients = [email.strip() for email in recipients.split(",") if email.strip()]
    else:
        recipients = [email for email in recipients if email]

    return list(dict.fromkeys(recipients))


def build_email_content(user_message, content_generator):
    prompt = EMAIL_CONTENT_PROMPT.format(user_message=user_message)
    response = content_generator(prompt).text.strip()

    cleaned_response = response.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    payload = json.loads(cleaned_response)
    subject = payload.get("subject", "").strip()
    body = payload.get("body", "").strip()

    if not subject or not body:
        raise ValueError("Email subject/body could not be generated")

    return {
        "subject": subject,
        "body": body,
    }


def send_contextual_email(user_message, content_generator, recipients=None):
    resolved_recipients = normalize_recipients(recipients=recipients, user_message=user_message)

    if not resolved_recipients:
        raise ValueError("Recipient email is required to send an email")

    email_content = build_email_content(user_message, content_generator)

    try:
        email = QueuedEmailMessage(
            subject=email_content["subject"],
            body=email_content["body"],
            to=resolved_recipients,
        )
        message = email.send(fail_silently=False)
    except ImproperlyConfigured as exc:
        raise ImproperlyConfigured("Email settings are not configured correctly") from exc

    return {
        "recipient": resolved_recipients,
        "subject": email_content["subject"],
        "message": message,
    }
