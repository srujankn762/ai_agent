from rest_framework.views import APIView
from rest_framework import status
from rest_framework.response import Response

from chat.services.embedding_service import store_chunks
from chat.utils import extract_text_from_pdf, extract_text_from_url
from chat.utils import chunk_text
import hashlib

from .services.gemini_service import GeminiService
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

        gemini = GeminiService()

        try:
            # reply = gemini.generate_response(user_message) # Method1: Direct LLM call
            reply, sources = gemini.generate_rag_response(user_message) #Method2: Generate Context (RAG) and do LLM call

            return Response({
                "user_message": user_message,
                "reply": reply,
                "sources": sources
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
            return Response({"error": "File required"}, status=400)

        file_bytes = file.read()
        file_hash = hashlib.sha256(file_bytes).hexdigest()

        file.seek(0)  # Reset pointer, Python reads the file and moves the internal cursor to the end.
                      # So if you try to read it again later for PDF extraction, it has to begin from the start

        # Step 1: extract text
        text = extract_text_from_pdf(file)

        # Step 2: chunk
        chunks = chunk_text(text)


        # Step 3: embed + store
        message = store_chunks(chunks, file.name, file_hash)

        return Response({
            "message": message,
            "chunks_created": len(chunks)
        })


class UploadURLView(APIView):

    def post(self, request):
        url = request.data.get("url")

        if not url:
            return Response({"error": "URL required"}, status=400)

        # Step 1: Extract
        text = extract_text_from_url(url)

        # Step 2: Chunk
        chunks = chunk_text(text)

        # Step 3: Embed + store
        message = store_chunks(chunks, url)


        return Response({
            "message": message,
            "chunks_created": len(chunks)
        })