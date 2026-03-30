from rest_framework.views import APIView
from rest_framework import status
from rest_framework.response import Response
from uuid import uuid4

from chat.services.embedding_service import is_file_already_processed, is_url_already_processed
from chat.tasks import store_chunks
from chat.utils import extract_text_from_pdf, extract_text_from_url
from chat.utils import chunk_text
import hashlib
from chat.models import UploadLog

from .services.agent_service import AgentService
import logging
logger = logging.getLogger(__name__)


class ChatView(APIView):

    def post(self, request):
        user_message = request.data.get("message")

        if not user_message:
            return Response(
                {"error": "Message is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # gemini = GeminiService()
        agent = AgentService()

        try:
            # reply = gemini.generate_response(user_message) # Method1: Direct LLM call
            # reply = gemini.generate_rag_response(user_message) #Method2: Generate Context (RAG) and do LLM call
            reply = agent.decide_and_act(user_message)
            return Response({
                "user_message": user_message,
                "reply": reply
            })

        except Exception as e:
            logger.error(f"Message Generation failed due to: {e}")
            return Response(
                {"error": "Unable to generate response"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class UploadDocumentView(APIView):

    def post(self, request):
        file = request.FILES.get("file")

        if not file:
            return Response({"error": "File required"}, status=status.HTTP_400_BAD_REQUEST)

        file_bytes = file.read()
        file_hash = hashlib.sha256(file_bytes).hexdigest()
        upload_log = UploadLog(
            upload_id=str(uuid4()),
            file_hash=file_hash,
        )

        if is_file_already_processed(file_hash):
            upload_log.status = UploadLog.Status.FAILURE
            upload_log.message = UploadLog.Message.FILE_ALREADY_PROCESSED
            upload_log.save()
            return Response(
                {
                    "status": UploadLog.Status.FAILURE.label,
                    "message": UploadLog.Message.FILE_ALREADY_PROCESSED,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        upload_log.status = UploadLog.Status.PROCESSING
        upload_log.message = UploadLog.Message.FILE_SUBMITTED_FOR_PROCESSING
        upload_log.save()

        try:
            file.seek(0)
            # Step 1: extract text
            text = extract_text_from_pdf(file)

            # Step 2: chunk
            chunks = chunk_text(text)

            # Step 3: enqueue embed + store\
            task = store_chunks.delay(chunks, file.name, file_hash, upload_log.upload_id)
            upload_log.task_id = task.id
            upload_log.save()
        except Exception as e:
            upload_log.status = UploadLog.Status.FAILURE
            upload_log.message = str(e)
            upload_log.save()
            logger.error(f"File upload processing failed due to: {e}")
            return Response(
                {
                    "status": UploadLog.Status.FAILURE.label,
                    "message": str(e),
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return Response(
            {
                "status": "processing",
                "message": UploadLog.Message.FILE_SUBMITTED_FOR_PROCESSING,
                "chunks_created": len(chunks),
                "task_id": task.id,
                "upload_id": upload_log.upload_id,
            },
            status=status.HTTP_201_CREATED,
        )


class UploadURLView(APIView):

    def post(self, request):
        url = request.data.get("url")

        if not url:
            return Response({"error": "URL required"}, status=400)

        if is_url_already_processed(url):
            return Response({
                "message": UploadLog.Message.URL_ALREADY_PROCESSED,
                "chunks_created": 0,
            })
        # Step 1: Extract
        text = extract_text_from_url(url)

        # Step 2: Chunk
        chunks = chunk_text(text)

        # Step 3: enqueue embed + store
        task = store_chunks.delay(chunks, url)


        return Response({
            "message": UploadLog.Message.CHUNKS_QUEUED_FOR_PROCESSING,
            "chunks_created": len(chunks),
            "task_id": task.id,
        })
