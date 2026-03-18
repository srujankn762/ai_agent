from chat.models import DocumentChunk


def store_chunks(chunks, source, gemini_service):
    objects = []

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