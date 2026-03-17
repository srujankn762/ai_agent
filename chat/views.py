from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

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




import google.generativeai as genai
from django.conf import settings

genai.configure(api_key=settings.GEMINI_API_KEY)

for m in genai.list_models():
    print(m.name, m.supported_generation_methods)