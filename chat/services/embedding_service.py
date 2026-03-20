from chat.models import DocumentChunk
from chat.services.gemini_service import GeminiService


def store_chunks(chunks, source, file_hash=None):
    if file_hash:
        if DocumentChunk.objects.filter(file_hash=file_hash).exists():
            return "File already processed"

    objects = []
    gemini_service = GeminiService()
    for chunk in chunks:
        embedding = gemini_service.get_embedding(chunk)

        objects.append(
            DocumentChunk(
                content=chunk,
                embedding=embedding,
                source=source,
                file_hash=file_hash
            )
        )

    DocumentChunk.objects.bulk_create(objects)
    return "Document processed"
