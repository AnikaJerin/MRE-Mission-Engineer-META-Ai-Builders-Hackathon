"""One explicit Meta Responses request at a time; no automatic retries."""
import json
import os
import urllib.error
import urllib.request

from . import api_budget
from .evidence import EvidenceError

MODEL = "muse-wonder-1.0"
ENDPOINT = "https://api.meta.ai/v1/responses"
MAX_REQUESTS = 5
REQUEST_TIMEOUT_SECONDS = 180
MAX_OUTPUT_TOKENS = 3000
# Local serialized-payload bound, not a provider token/context limit.
# Final revision includes both reviews plus actual tool evidence.
MAX_CONTEXT_BYTES = 64_000


def http_diagnostic(error, key):
    """Extract bounded public error fields; never log headers or request body."""
    details = {"category": "http_error", "http_status": error.code}
    try:
        raw = error.read(16_385)
        if len(raw) > 16_384:
            details["body_status"] = "too_large"
            return details
        value = json.loads(raw)
        error_body = value.get("error", value) if isinstance(value, dict) else None
        if isinstance(error_body, dict):
            for field in ("type", "code", "param", "message"):
                item = error_body.get(field)
                if isinstance(item, (str, int)) and not isinstance(item, bool):
                    text = str(item)
                    details[field] = (text.replace(key, "[redacted]") if key else text)[:1200]
        else:
            details["body_status"] = "no_error_object"
    except Exception:
        details["body_status"] = "unreadable_or_non_json"
    return details


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        raise EvidenceError("API redirect refused; no automatic retry")


class MetaClient:
    def __init__(self, root, record):
        self.root, self.record = root, record
        self.calls = 0
        self.context_sizes = {}

    def request(self, body):
        key = os.environ.get("MODEL_API_KEY", "").strip()
        if not key:
            raise EvidenceError("Set MODEL_API_KEY in the terminal; never put it in chat or source files")
        if self.calls >= MAX_REQUESTS:
            raise EvidenceError("Five-request investigation limit reached")
        payload = {**body, "model": MODEL, "max_output_tokens": MAX_OUTPUT_TOKENS,
                   "reasoning": {"effort": "minimal"}, "tool_choice": "auto", "parallel_tool_calls": False}
        encoded = json.dumps(payload, allow_nan=False, ensure_ascii=False, separators=(",", ":")).encode()
        previous = payload.get("previous_response_id")
        prior = self.context_sizes.get(previous, 0) if previous else 0
        if previous and previous not in self.context_sizes:
            raise EvidenceError("Unknown response chain")
        if prior + len(encoded) > MAX_CONTEXT_BYTES:
            raise EvidenceError(f"Local request context too large ({prior + len(encoded)} bytes; limit {MAX_CONTEXT_BYTES}). This request was not sent or charged; retain the saved partial review.")
        self.record("request_context_checked", {"request_number": self.calls + 1, "bytes": prior + len(encoded), "local_limit_bytes": MAX_CONTEXT_BYTES})
        reservation = api_budget.reserve(self.root)
        self.calls += 1
        self.record("api_reserved", {"request_number": self.calls, "reservation_id": reservation,
                                     "reserved_usd": 0.25, "model": MODEL, "timeout_seconds": REQUEST_TIMEOUT_SECONDS})
        request = urllib.request.Request(ENDPOINT, data=encoded, method="POST",
                    headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"})
        try:
            with urllib.request.build_opener(NoRedirect()).open(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
                raw = response.read(1_000_001)
                if len(raw) > 1_000_000:
                    raise ValueError("Response too large")
                result = json.loads(raw)
        except urllib.error.HTTPError as exc:
            details = http_diagnostic(exc, key)
            api_budget.settle(self.root, reservation, None)
            self.record("api_error", {"request_number": self.calls, "reservation_id": reservation, **details})
            message = details.get("message", "No readable provider error message")
            raise EvidenceError(f"Meta HTTP {exc.code}: {message}. See api_error event; billing unresolved, no automatic retry.") from None
        except Exception as exc:
            api_budget.settle(self.root, reservation, None)
            category = "timeout" if isinstance(exc, TimeoutError) else "connection_error" if isinstance(exc, urllib.error.URLError) else "unreadable_response"
            self.record("api_error", {"request_number": self.calls, "reservation_id": reservation, "category": category})
            raise EvidenceError(f"Meta {category}; see api_error event. Billing uncertain; inspect provider dashboard. No automatic retry.") from None
        if not isinstance(result, dict):
            api_budget.settle(self.root, reservation, None)
            raise EvidenceError("Unexpected API response; billing review required")
        accounting = api_budget.settle(self.root, reservation, result.get("usage"))
        self.record("api_response", {"request_number": self.calls, "response_id": result.get("id"),
                                    "response_status": result.get("status"), "billing": accounting})
        if accounting["state"] != "settled":
            raise EvidenceError("Missing usage or reservation exceeded; billing review required before more requests")
        if result.get("status") != "completed" or not isinstance(result.get("output"), list) or not isinstance(result.get("id"), str):
            raise EvidenceError("Meta response incomplete or invalid; no automatic continuation/retry")
        self.context_sizes[result["id"]] = prior + len(encoded) + len(raw)
        return result
