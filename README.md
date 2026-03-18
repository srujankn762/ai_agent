## Phase 1: LLM Integration

### Overview

* Built a Django-based backend service to integrate with a Large Language Model (Gemini).
* Established a clean architecture separating API, service, and configuration layers.
* Designed the system to be extensible for future features like RAG and tool calling.

### API Design

* Implemented a `POST /api/chat/` endpoint to handle user queries.
* The API accepts a message and returns a generated response from Gemini.
* Basic validation and error handling ensure robustness.

### Gemini Integration

* Created a dedicated `GeminiService` to encapsulate all LLM interactions.
* Used `gemini-2.5-flash` for fast and reliable response generation.
* Added system prompts to control tone, accuracy, and domain-specific behavior.

### Key Design Decisions

* Separated LLM logic from views to maintain scalability and testability.
* Used environment variables to securely manage API keys and configuration.
* Preserved Markdown formatting in responses for flexible frontend rendering.

### Limitations

* No memory or context persistence between requests.
* No document-based retrieval or external API integration.

### Next Steps

* Extend the system with embeddings and vector storage using PostgreSQL and pgvector.
* Implement Retrieval-Augmented Generation (RAG) for context-aware responses.
