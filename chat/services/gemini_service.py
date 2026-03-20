import google.generativeai as genai
from django.conf import settings
from .prompts import SYSTEM_PROMPT, RAG_PROMPT
from chat.services.retrieval_service import search_similar_chunks

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

    def generate_rag_response(self, user_message):

        # Step 1: Convert query → embedding
        query_embedding = self.get_embedding(user_message)

        # Step 2: Retrieve similar chunks
        chunks = search_similar_chunks(query_embedding)

        # Step 3: Build context
        context = "\n\n".join([chunk.content for chunk in chunks])
        # Step 4: Create prompt
        prompt = RAG_PROMPT.format(context=context, user_message=user_message)

        # Step 5: Generate response
        response = self.model.generate_content(prompt)
        return response.text

    def get_embedding(self, text):
        result = genai.embed_content(
            model="models/gemini-embedding-001",
            content=text
        )
        return result["embedding"]