def get_wallet_balance(user_id):
    # mock for now
    return {
        "balance": 100.12,
        "currency": "INR"
    }


def search_documents(query, gemini_service):
    return gemini_service.generate_rag_response(query)