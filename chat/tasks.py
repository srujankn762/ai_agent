from celery import shared_task

from chat.services.embedding_service import _store_chunks

@shared_task(bind=True, max_retries=3)
def store_chunks(self, chunks, source, file_hash=None):
    try:
        return _store_chunks(chunks, source, file_hash)
    except Exception as e:
        raise self.retry(exc=e, countdown=5)
