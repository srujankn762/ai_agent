import gc
from contextlib import nullcontext
from types import SimpleNamespace
from unittest.mock import patch
import weakref

from celery.exceptions import MaxRetriesExceededError
from django.db import connection
from django.test import SimpleTestCase

from chat.models import UploadLog
from chat.services import embedding_service
from chat.tasks import store_chunks
from chat.utils import chunk_text


class UploadRegressionTests(SimpleTestCase):
    def test_failed_upload_can_be_retried_but_active_and_successful_uploads_cannot(self):
        for status, expected in (
            (UploadLog.Status.FAILURE, False),
            (UploadLog.Status.PROCESSING, True),
            (UploadLog.Status.SUCCESS, True),
        ):
            with self.subTest(status=status):
                with patch.object(embedding_service.UploadLog.objects, "filter") as logs, patch.object(
                    embedding_service.DocumentChunk.objects, "filter", return_value=False
                ):
                    logs.return_value.exists.return_value = status != UploadLog.Status.FAILURE
                    result = embedding_service.is_file_already_processed("file-hash")

                self.assertEqual(bool(result), expected)
                self.assertEqual(
                    logs.call_args.kwargs["status__in"],
                    [UploadLog.Status.SUCCESS, UploadLog.Status.PROCESSING],
                )

    def test_final_retry_marks_upload_failed(self):
        for retries, expected_status in ((0, UploadLog.Status.PROCESSING), (3, UploadLog.Status.FAILURE)):
            with self.subTest(retries=retries):
                store_chunks.push_request(retries=retries, id="task-id")
                try:
                    with patch("chat.tasks._store_chunks", side_effect=RuntimeError("embedding failed")), patch.object(
                        UploadLog.objects, "filter"
                    ) as logs, patch.object(store_chunks, "retry", side_effect=MaxRetriesExceededError):
                        with self.assertRaises(MaxRetriesExceededError):
                            store_chunks.run(["chunk"], "source", "hash", "upload-id")

                    self.assertEqual(logs.return_value.update.call_args.kwargs["status"], expected_status)
                    self.assertEqual(logs.return_value.update.call_args.kwargs["attempt_number"], retries + 1)
                finally:
                    store_chunks.pop_request()

    def test_embedding_runs_outside_database_transaction(self):
        def check_transaction(*args):
            self.assertFalse(connection.in_atomic_block)
            return "Success"

        with patch("chat.tasks._store_chunks", side_effect=check_transaction):
            self.assertEqual(store_chunks.run(["chunk"], "source"), "Success")

    def test_stored_chunks_are_released_after_bulk_create(self):
        saved_chunk_refs = []

        class FakeChunk:
            def __init__(self, **kwargs):
                self.content = kwargs["content"]

        def bulk_create(chunks):
            saved_chunk_refs.extend(weakref.ref(chunk) for chunk in chunks)

        FakeChunk.objects = SimpleNamespace(bulk_create=bulk_create)
        with patch.object(embedding_service, "DocumentChunk", FakeChunk), patch.object(
            embedding_service, "GeminiService"
        ) as gemini, patch.object(embedding_service.transaction, "atomic", return_value=nullcontext()):
            gemini.return_value.get_embedding.return_value = [0.1]
            self.assertEqual(embedding_service._store_chunks(["first", "second"], "source"), "Success")

        self.assertEqual(len(saved_chunk_refs), 2)
        gc.collect()
        self.assertTrue(all(ref() is None for ref in saved_chunk_refs))

    def test_chunk_text_preserves_short_trailing_tail(self):
        text = "a" * 500 + "b" * 10
        self.assertEqual(chunk_text(text), [text[:500], text[450:]])
        self.assertEqual(chunk_text("short"), ["short"])
