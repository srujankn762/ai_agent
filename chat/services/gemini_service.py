import google.generativeai as genai
from django.conf import settings


genai.configure(api_key=settings.GEMINI_API_KEY)


class GeminiService:

    def __init__(self):
        self.model = genai.GenerativeModel(settings.GEMINI_MODEL)

    def generate_response(self, user_message, chat_history=None):
        """
        Core method to interact with Gemini
        """

        system_prompt = """
        You are a fintech customer support assistant.

        Rules:
        - Be concise
        - Be accurate
        - If unsure, say you don't know
        - Do not hallucinate
        """

        messages = []

        # Add system prompt
        messages.append({"role": "user", "parts": [system_prompt]})

        # Add history if exists
        if chat_history:
            for msg in chat_history:
                messages.append(msg)

        # Add current message
        messages.append({"role": "user", "parts": [user_message]})
        response = self.model.generate_content(messages)

        return response.text