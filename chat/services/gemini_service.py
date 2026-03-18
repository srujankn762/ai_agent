import google.generativeai as genai
from django.conf import settings
from .helpers import SYSTEM_PROMPT


genai.configure(api_key=settings.GEMINI_API_KEY)


class GeminiService:

    def __init__(self):
        self.model = genai.GenerativeModel(settings.GEMINI_MODEL)

    def generate_response(self, user_message, chat_history=None):
        """
        Core method to interact with Gemini
        """

        messages = []

        # Add system prompt
        messages.append({"role": "user", "parts": [SYSTEM_PROMPT]})

        # Add history if exists
        if chat_history:
            for msg in chat_history:
                messages.append(msg)

        # Add current message
        messages.append({"role": "user", "parts": [user_message]})
        response = self.model.generate_content(messages)

        return response.text