from django.db import models
from pgvector.django import VectorField


class DocumentChunk(models.Model):
    content = models.TextField()
    embedding = VectorField(dimensions=3072)  # Gemini embedding size
    source = models.CharField(max_length=255)  # file or URL
    created_at = models.DateTimeField(auto_now_add=True)