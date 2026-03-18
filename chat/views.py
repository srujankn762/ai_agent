from rest_framework.views import APIView
from rest_framework import status
from rest_framework.response import Response

from chat.services.embedding_service import store_chunks
from chat.utils import extract_text_from_pdf
from chat.utils import chunk_text

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
            reply = gemini.generate_response(user_message)

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
            return Response({"error": "File required"}, status=400)

        # Step 1: extract text
        text = extract_text_from_pdf(file)

        # Step 2: chunk
        chunks = chunk_text(text)

        # Step 3: embed + store
        gemini = GeminiService()
        store_chunks(chunks, file.name, gemini)

        return Response({
            "message": "Document processed",
            "chunks_created": len(chunks)
        })