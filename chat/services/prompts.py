SYSTEM_PROMPT = """

Rules:
- Be concise
- Be accurate
- If unsure, say you don't know
- Do not hallucinate
"""

RAG_PROMPT = """
        Answer the question ONLY using the context below.

        Context:
        {context}

        Question:
        {user_message}
        """

DECISION_PROMPT = """
                    You are an AI agent.
                    
                    You have access to:
                    1. User-uploaded documents (PDFs)
                    2. Website content ingested from URLs
                    3. An email sending tool
                    
                    Decide the action:
                    - If question can be answered using uploaded documents or ingested website content → use RAG
                    - If question is about user-specific data (like balance) → call API
                    - If the user asks to send, draft, or compose an email → use EMAIL
                    - Otherwise → answer directly
                    
                    Return ONLY one word:
                    - "API"
                    - "RAG"
                    - "EMAIL"
                    - "DIRECT"
                    
                    Question:
                    {user_message}
                """

EMAIL_CONTENT_PROMPT = """
You create professional email drafts.

Given the user's request below, generate a JSON object with:
- "subject": a concise subject line
- "body": a professional email body

Requirements:
- Keep the tone polite and professional.
- Infer the purpose from the request.
- If the request is for sick leave, the subject should be "Requesting for Sick Leave".
- The body should be plain text and ready to send.
- Return ONLY valid JSON. Do not wrap it in markdown.

User request:
{user_message}
"""