import json
import re

from django.core.mail import EmailMessage
from django.core.exceptions import ImproperlyConfigured

from chat.services.prompts import EMAIL_CONTENT_PROMPT


def get_wallet_balance(user_id):
    # mock for now
    return {
        "balance": 100.12,
        "currency": "INR"
    }


def search_documents(query, rag_response_generator):
    return rag_response_generator(query)


EMAIL_REGEX = r"([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,})"




def extract_email_recipient(user_message):
    match = re.search(EMAIL_REGEX, user_message or "")
    if match:
        return match.group(1)
    return None


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


def send_contextual_email(user_message, content_generator, recipient=None):
    resolved_recipient = recipient or extract_email_recipient(user_message)

    if not resolved_recipient:
        raise ValueError("Recipient email is required to send an email")

    email_content = build_email_content(user_message, content_generator)

    try:
        email = EmailMessage(
            subject=email_content["subject"],
            body=email_content["body"],
            to=[resolved_recipient],
        )
        email.send(fail_silently=False)
    except ImproperlyConfigured as exc:
        raise ImproperlyConfigured("Email settings are not configured correctly") from exc

    return {
        "recipient": resolved_recipient,
        "subject": email_content["subject"],
        "message": f"Email sent successfully to {resolved_recipient} with subject '{email_content['subject']}'",
    }
