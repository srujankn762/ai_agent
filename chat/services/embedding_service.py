from chat.models import DocumentChunk
from chat.services.gemini_service import GeminiService


def store_chunks(chunks, source):
    objects = []
    gemini_service = GeminiService()
    for chunk in chunks:
        embedding = gemini_service.get_embedding(chunk)

        objects.append(
            DocumentChunk(
                content=chunk,
                embedding=embedding,
                source=source
            )
        )

    DocumentChunk.objects.bulk_create(objects)

