from chat.models import DocumentChunk
from chat.services.gemini_service import GeminiService


def is_file_already_processed(file_hash):
    return DocumentChunk.objects.filter(file_hash=file_hash).exists()

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

    DocumentChunk.objects.bulk_create(objects)
    return "Success"
