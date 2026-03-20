from pgvector.django import CosineDistance
from chat.models import DocumentChunk


def search_similar_chunks(query_embedding, top_k=5):
    results = (
        DocumentChunk.objects
        .annotate(distance=CosineDistance("embedding", query_embedding))
        .order_by("distance")[:top_k]
    )

    return results