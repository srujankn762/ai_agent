from django.db import models
from pgvector.django import VectorField


class DocumentChunk(models.Model):
    content = models.TextField()
    embedding = VectorField(dimensions=3072)  # Gemini embedding size
    source = models.CharField(max_length=255)  # file or URL
    file_hash = models.CharField(max_length=64, db_index=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'document_chunk'


class UploadLog(models.Model):
    class Status(models.TextChoices):
        PROCESSING = "PROCESSING", "Processing"
        SUCCESS = "SUCCESS", "Success"
        FAILURE = "FAILURE", "Failure"
    class Message:
        FILE_ALREADY_PROCESSED = "File was already processed (or) is waiting in the queue"
        FILE_SUBMITTED_FOR_PROCESSING = "File is submitted for processing"
        URL_ALREADY_PROCESSED = "Url already processed"
        CHUNKS_QUEUED_FOR_PROCESSING = "Chunks queued for processing"

    upload_id = models.CharField(max_length=36, unique=True)
    task_id = models.CharField(max_length=255, null=True, blank=True)
    attempt_number = models.PositiveIntegerField(default=0)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PROCESSING,
    )
    message = models.TextField(null=True, blank=True)
    file_hash = models.CharField(max_length=64)
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "upload_log"
