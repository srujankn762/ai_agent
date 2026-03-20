from chat.services.gemini_service import GeminiService
from chat.services.tools import get_wallet_balance, search_documents
from .prompts import DECISION_PROMPT


class AgentService:

    def __init__(self):
        self.gemini = GeminiService()

    def decide_and_act(self, user_message):

        # Step 1: Ask LLM what to do
        decision_prompt = DECISION_PROMPT.format(user_message=user_message)

        decision = self.gemini.model.generate_content(decision_prompt).text.strip()

        # Step 2: Execute decision

        if decision == "API":
            result = get_wallet_balance(user_id=1)

            return f"Your balance is {result['balance']} {result['currency']}"

        elif decision == "RAG":
            return search_documents(user_message, self.gemini)

        else:
            return self.gemini.generate_response(user_message)