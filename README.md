# AI Agent

A Django REST API project that connects Gemini with document retrieval, URL ingestion, tool calling, and asynchronous background jobs.

## Features

### Gemini Chat API

- Provides a `POST /api/chat/` endpoint for user messages.
- Uses Google Gemini as the LLM provider.
- Applies a system prompt that asks the model to stay concise, accurate, and avoid hallucinations.
- Supports optional `recipients` input for email-related requests.

### Agent Decision Flow

The chat endpoint uses `AgentService` to decide how a request should be handled:

- `DIRECT`: answer directly with Gemini.
- `RAG`: search uploaded documents or ingested URLs, then answer using retrieved context.
- `API`: call a mock wallet-balance tool.
- `EMAIL`: generate email content and queue an email-sending task.

### Retrieval-Augmented Generation

- Stores document chunks in PostgreSQL with pgvector embeddings.
- Uses Gemini embeddings through `models/gemini-embedding-001`.
- Retrieves similar chunks using cosine distance.
- Builds a context-aware RAG prompt and asks Gemini to answer only from that context.

### PDF Upload And Processing

- Provides `POST /api/upload/` for PDF uploads.
- Extracts text from uploaded PDFs using `pypdf`.
- Splits text into overlapping chunks.
- Generates embeddings for each chunk.
- Stores chunks in the `document_chunk` table.
- Uses SHA-256 file hashes to avoid processing duplicate files.

### URL Ingestion

- Provides `POST /api/upload-url/` for ingesting website content.
- Fetches page HTML with `requests`.
- Extracts readable text with BeautifulSoup.
- Chunks, embeds, and stores URL content for later RAG queries.
- Avoids reprocessing URLs already present in the vector store.

### Background Jobs With Celery

- Uses Celery for long-running work.
- `store_chunks` embeds and stores document or URL chunks asynchronously.
- `send_email_task` sends generated emails asynchronously.
- Tasks retry up to 3 times on failure.
- RabbitMQ is configured as the default broker.

### Upload Tracking

- Stores upload status in the `upload_log` table.
- Tracks upload ID, Celery task ID, file hash, attempt count, status, message, and last update time.
- Provides a read-only `upload-logs` API with pagination, filtering, and ordering.

Available filters:

- `status`
- `upload_id`
- `task_id`
- `file_hash`

### Email Tool

- Detects recipients from the request or accepts them through the `recipients` field.
- Uses Gemini to create a JSON email draft with `subject` and `body`.
- Sends email through Django's configured email backend.
- Queues delivery with Celery.

### API Request Logging

- Includes middleware that logs incoming requests and outgoing responses using Rich formatting.
- Adds request IDs, timestamps, process/thread details, status codes, and response time.
- Masks sensitive fields such as passwords, tokens, authorization headers, access tokens, and refresh tokens.
- Avoids logging uploaded file contents.

### Vector Visualization

- Includes `visualise_vectors.py` to plot stored document embeddings.
- Can generate 2D and 3D PCA plots.
- Can embed a user query, plot it alongside stored chunks, and print nearest chunks.
- Saves output images such as `embeddings_2d.png` and `embeddings_3d.png`.

## Main API Endpoints

| Method | Endpoint | Purpose |
| --- | --- | --- |
| `POST` | `/api/chat/` | Send a user message to the agent |
| `POST` | `/api/upload/` | Upload and process a PDF |
| `POST` | `/api/upload-url/` | Ingest a web page by URL |
| `GET` | `/api/upload-logs/` | List upload processing logs |
| `GET` | `/api/upload-logs/{id}/` | View one upload log |

## Tech Stack

- Django and Django REST Framework
- Google Gemini API
- PostgreSQL with pgvector
- Celery
- RabbitMQ
- pypdf
- BeautifulSoup
- Rich and colorlog
- NumPy and Matplotlib for embedding visualization

## Local Setup

1. Create and activate a virtual environment.
2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Start PostgreSQL with pgvector and RabbitMQ:

   ```bash
   docker compose up -d
   ```

4. Configure environment variables. The project expects values such as:

   ```bash
   GEMINI_API_KEY=...
   GEMINI_MODEL=gemini-2.5-flash
   DB_NAME=ai_agent
   DB_USER=postgres
   DB_PASSWORD=postgres
   DB_HOST=localhost
   DB_PORT=5434
   DB_SCHEMA=ai_agent
   CELERY_BROKER_URL=amqp://guest:guest@localhost:5673//
   EMAIL_HOST=...
   EMAIL_PORT=587
   EMAIL_HOST_USER=...
   EMAIL_HOST_PASSWORD=...
   DEFAULT_FROM_EMAIL=...
   ```

5. Run migrations:

   ```bash
   python manage.py migrate
   ```

6. Start the Django server:

   ```bash
   python manage.py runserver
   ```

7. Start a Celery worker in another terminal:

   ```bash
   celery -A ai_agent worker --loglevel=info
   ```

## Example Requests

### Chat

```bash
curl -X POST http://localhost:8000/api/chat/ \
  -H "Content-Type: application/json" \
  -d '{"message": "Summarize the uploaded document"}'
```

### Send Email Through Agent

```bash
curl -X POST http://localhost:8000/api/chat/ \
  -H "Content-Type: application/json" \
  -d '{"message": "Send a sick leave email", "recipients": ["person@example.com"]}'
```

### Upload PDF

```bash
curl -X POST http://localhost:8000/api/upload/ \
  -F "file=@sample.pdf"
```

### Ingest URL

```bash
curl -X POST http://localhost:8000/api/upload-url/ \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com"}'
```

### View Upload Logs

```bash
curl http://localhost:8000/api/upload-logs/
```

## Notes

- The wallet-balance API tool is currently mocked.
- RAG quality depends on uploaded or ingested content being processed successfully.
- Email sending requires valid SMTP settings.
- Background processing requires RabbitMQ and a running Celery worker.
