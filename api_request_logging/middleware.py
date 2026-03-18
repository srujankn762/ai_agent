import time
import json
import threading
import os
import uuid
from datetime import datetime, timezone

from rich.console import Console
from rich.json import JSON

console = Console()

SENSITIVE_KEYS = {"password", "token", "authorization", "access", "refresh"}


def mask_sensitive_data(data):
    if isinstance(data, dict):
        return {
            k: ("***" if k.lower() in SENSITIVE_KEYS else mask_sensitive_data(v))
            for k, v in data.items()
        }
    elif isinstance(data, list):
        return [mask_sensitive_data(item) for item in data]
    return data


class RichAPILoggingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start_time = time.time()
        start_timestamp = datetime.now(timezone.utc).isoformat()

        request_id = str(uuid.uuid4())
        process_id = os.getpid()
        thread_id = threading.get_ident()

        # -------- Request Body --------
        try:
            body = request.body.decode("utf-8")
            body = json.loads(body) if body else {}
        except Exception:
            body = str(request.body)

        body = mask_sensitive_data(body)

        # -------- Headers --------
        headers = dict(request.headers)
        headers = mask_sensitive_data(headers)

        request_log = {
            "timestamp": start_timestamp,
            "event": "request_received",
            "request_id": request_id,
            "path": request.path,
            "method": request.method,
            "headers": headers,
            "body": body,
            "process_id": process_id,
            "thread_id": thread_id,
        }

        console.print("\n[bold green]Incoming Request[/bold green]")
        console.print(JSON.from_data(request_log))

        # -------- Process Request --------
        response = self.get_response(request)

        duration_ms = round((time.time() - start_time) * 1000, 2)
        end_timestamp = datetime.now(timezone.utc).isoformat()

        # -------- Response Body --------
        try:
            if hasattr(response, "content"):
                response_body = json.loads(response.content.decode("utf-8"))
            else:
                response_body = "Streaming/No content"
        except Exception:
            response_body = str(response.content)

        response_body = mask_sensitive_data(response_body)

        response_log = {
            "timestamp": end_timestamp,
            "event": "response_sent",
            "request_id": request_id,
            "path": request.path,
            "method": request.method,
            "status_code": response.status_code,
            "response": response_body,
            "duration_ms": duration_ms,
            "process_id": process_id,
            "thread_id": thread_id,
        }

        console.print("[bold blue]Outgoing Response[/bold blue]")
        console.print(JSON.from_data(response_log))

        return response