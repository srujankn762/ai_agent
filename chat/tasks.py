from celery import shared_task
from django.core.mail import EmailMessage

from chat.models import UploadLog
from chat.services.embedding_service import _store_chunks


@shared_task(bind=True, max_retries=3)
def store_chunks(self, chunks, source, file_hash=None, upload_id=None):
    try:
        result = _store_chunks(chunks, source, file_hash)
        if upload_id:
            UploadLog.objects.filter(upload_id=upload_id).update(
                status=UploadLog.Status.SUCCESS,
                message="File processed successfully",
                attempt_number=self.request.retries + 1,
                task_id=self.request.id,
            )
        return result
    except Exception as e:
        if upload_id:
            attempt_number = self.request.retries + 1
            status_value = UploadLog.Status.FAILURE if self.request.retries >= self.max_retries else UploadLog.Status.PROCESSING
            UploadLog.objects.filter(upload_id=upload_id).update(
                status=status_value,
                message=str(e),
                attempt_number=attempt_number,
                task_id=self.request.id,
            )
        raise self.retry(exc=e, countdown=5)


@shared_task(bind=True, max_retries=3)
def send_email_task(self, subject, body, recipients):
    try:
        email = EmailMessage(
            subject=subject,
            body=body,
            to=recipients,
        )
        email.send(fail_silently=False)
        return {
            "recipients": recipients,
            "status": "sent",
        }
    except Exception as e:
        raise self.retry(exc=e, countdown=5)
