from django.db import transaction

from chat.models import DocumentChunk, UploadLog
from chat.services.gemini_service import GeminiService

def is_file_already_processed(file_hash):
    return UploadLog.objects.filter(file_hash=file_hash,
                                    status__in=[UploadLog.Status.SUCCESS,
                                                UploadLog.Status.PROCESSING]).exists() or DocumentChunk.objects.filter(
                                                file_hash=file_hash)


def is_url_already_processed(source):
    return DocumentChunk.objects.filter(source=source).exists()


def _store_chunks(chunks, source, file_hash=None):
    objects = []
    gemini_service = GeminiService()
    for chunk in chunks:
        embedding = gemini_service.get_embedding(chunk)
        objects.append(
            DocumentChunk(
                content=chunk,
                embedding=embedding,
                source=source,
                file_hash=file_hash,
            )
        )

    with transaction.atomic():
        DocumentChunk.objects.bulk_create(objects)

    return "Success"
