"""Conservative local estimated-cost ledger; not a provider billing cap."""
import contextlib
import fcntl
import json
import os
import math
import time
from pathlib import Path
from uuid import uuid4

from .evidence import EvidenceError, read_json

REQUEST_RESERVATION_MICROUSD = 250_000
PROJECT_LIMIT_MICROUSD = 100_000_000


@contextlib.contextmanager
def lock(root, name):
    folder = Path(root) / "outputs/locks"
    folder.mkdir(parents=True, exist_ok=True)
    with (folder / f"{name}.lock").open("a+") as stream:
        # Dashboard reads may briefly overlap a reservation/settlement write.
        # Serialize these short ledger operations; never queue another paid run.
        deadline=time.monotonic()+(2.0 if name == "billing" else 0.0)
        while True:
            try:
                fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except BlockingIOError as exc:
                if time.monotonic() >= deadline:
                    message=("Billing ledger is busy; retry the local operation after it finishes. No automatic API retry." if name == "billing" else "Another local operation is active; no concurrent paid run allowed")
                    raise EvidenceError(message) from exc
                time.sleep(0.01)
        try: yield
        finally: fcntl.flock(stream, fcntl.LOCK_UN)


def _read(root):
    path = Path(root) / "outputs/api-ledger.json"
    data = read_json(path) if path.exists() else {"version": 1, "requests": []}
    if not isinstance(data, dict) or data.get("version") != 1 or not isinstance(data.get("requests"), list):
        raise EvidenceError("Invalid API ledger; billing review required")
    ids = set()
    for row in data["requests"]:
        if not isinstance(row, dict) or not isinstance(row.get("id"), str) or row["id"] in ids:
            raise EvidenceError("Invalid ledger request identity")
        ids.add(row["id"])
        if not isinstance(row.get("state"), str) or row["state"] not in {"reserved", "settled", "unresolved"}:
            raise EvidenceError("Invalid ledger state")
        for key in ("reservation_microusd", "accounted_microusd"):
            if type(row.get(key)) is not int or row[key] < 0:
                raise EvidenceError("Invalid ledger amount")
        if "owner_accepts_unknown_cost" in row and row["owner_accepts_unknown_cost"] is not True:
            raise EvidenceError("Invalid uncertainty acknowledgement")
        if row.get("owner_accepts_unknown_cost") and row["state"] != "settled" and (
                row["state"] != "unresolved" or row["accounted_microusd"] != row["reservation_microusd"]):
            raise EvidenceError("Acknowledged uncertainty must retain its full reservation")
    return data


def _write(root, data):
    path = Path(root) / "outputs/api-ledger.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(".json.tmp")
    with temp.open("w") as stream:
        json.dump(data, stream, indent=2, allow_nan=False)
        stream.flush(); os.fsync(stream.fileno())
    temp.replace(path)


def snapshot(root):
    with lock(root, "billing"):
        data = _read(root)
    used = sum(r["accounted_microusd"] for r in data["requests"])
    return {"accounted_or_reserved_usd": used / 1e6,
            "local_limit_usd": PROJECT_LIMIT_MICROUSD / 1e6,
            "per_request_reservation_usd": REQUEST_RESERVATION_MICROUSD / 1e6,
            "active_reserved_requests": [r["id"] for r in data["requests"] if r["state"] == "reserved"],
            "recoverable_unknown_cost_requests": [r["id"] for r in data["requests"] if r["state"] == "unresolved" and not r.get("owner_accepts_unknown_cost") and r["accounted_microusd"] == r["reservation_microusd"]],
            "unresolved_requests": [r["id"] for r in data["requests"] if r["state"] != "settled"],
            "blocking_unresolved_requests": [r["id"] for r in data["requests"] if r["state"] != "settled" and not r.get("owner_accepts_unknown_cost")],
            "acknowledged_unknown_cost_requests": [r["id"] for r in data["requests"] if r["state"] == "unresolved" and r.get("owner_accepts_unknown_cost")],
            "recorded_requests": len(data["requests"]),
            "scope": "Local MRE estimates only; excludes ECLIPSE, other apps and deleted ledgers. Not account balance or provider-enforced cap."}


def reserve(root):
    with lock(root, "billing"):
        data = _read(root)
        if any(r["state"] != "settled" and not r.get("owner_accepts_unknown_cost") for r in data["requests"]):
            raise EvidenceError("Unresolved API request: review provider billing before further calls")
        total = sum(r["accounted_microusd"] for r in data["requests"])
        if total + REQUEST_RESERVATION_MICROUSD > PROJECT_LIMIT_MICROUSD:
            raise EvidenceError("Local MRE API budget exhausted")
        id = uuid4().hex
        data["requests"].append({"id": id, "state": "reserved",
                                 "reservation_microusd": REQUEST_RESERVATION_MICROUSD,
                                 "accounted_microusd": REQUEST_RESERVATION_MICROUSD})
        _write(root, data)
        return id


def settle(root, id, usage):
    valid = isinstance(usage, dict) and all(type(usage.get(k)) is int and usage[k] >= 0 for k in ("input_tokens", "output_tokens"))
    # Wonder standard rates: $4/M input and $20/M output. Count input uncached.
    actual = usage["input_tokens"] * 4 + usage["output_tokens"] * 20 if valid else None
    with lock(root, "billing"):
        data = _read(root)
        rows = [r for r in data["requests"] if r["id"] == id]
        if len(rows) != 1 or rows[0]["state"] != "reserved":
            raise EvidenceError("Ledger reservation cannot be settled")
        row = rows[0]
        row["state"] = "settled" if valid and actual <= row["reservation_microusd"] else "unresolved"
        row["accounted_microusd"] = max(actual or 0, row["reservation_microusd"]) if row["state"] == "unresolved" else actual
        _write(root, data)
        return row.copy()


def reconcile(root, id, actual_usd, confirmed):
    if not confirmed or not isinstance(actual_usd, (int, float)) or isinstance(actual_usd, bool) or not math.isfinite(actual_usd) or actual_usd < 0:
        raise EvidenceError("Provide a finite nonnegative amount and --confirm-provider-review after checking provider billing")
    if not math.isfinite(actual_usd * 1e6):
        raise EvidenceError("Amount exceeds supported accounting range")
    with lock(root, "investigation"), lock(root, "billing"):
        data = _read(root)
        rows = [r for r in data["requests"] if r["id"] == id]
        if len(rows) != 1 or rows[0]["state"] == "settled":
            raise EvidenceError("Choose one reserved/unresolved request; settled entries are immutable")
        row = rows[0]
        row["prior_state"] = row["state"]
        row["state"] = "settled"
        row["accounted_microusd"] = math.ceil(actual_usd * 1e6)
        row["reconciliation"] = "Owner-entered amount after provider review; not independently verified"
        _write(root, data)
        return row.copy()


def acknowledge_unknown_cost(root, id, accepted):
    """Owner opt-in to continue with an unknown cost retained as a reservation."""
    if not accepted:
        raise EvidenceError("Add --accept-unknown-cost to retain the reservation and acknowledge that actual billing remains unknown")
    with lock(root, "investigation"), lock(root, "billing"):
        data = _read(root)
        rows = [r for r in data["requests"] if r["id"] == id]
        if len(rows) != 1 or rows[0]["state"] != "unresolved":
            raise EvidenceError("Choose an unresolved request, not an active reservation or settled request")
        row = rows[0]
        if row["accounted_microusd"] != row["reservation_microusd"]:
            raise EvidenceError("Known usage exceeded the reservation; provider reconciliation is required")
        row["owner_accepts_unknown_cost"] = True
        row["uncertainty_note"] = "Actual charge unknown. Full local reservation retained; owner permits continuation. Reservation is not a guaranteed upper bound or provider billing cap."
        _write(root, data)
        return row.copy()


def settle_sam_image(root,id):
    """One completed image at published $2.50/1000 SAM 3.1 images.

    Local estimate, not a provider invoice; do not apply Wonder token rates.
    """
    with lock(root,'billing'):
        data=_read(root)
        rows=[row for row in data['requests'] if row['id']==id]
        if len(rows)!=1 or rows[0]['state']!='reserved':raise EvidenceError('Invalid SAM reservation')
        row=rows[0];row.update(state='settled',accounted_microusd=2500,model='sam-3.1',
          metering_basis='One completed submitted image; estimated at published SAM 3.1 rate, not a provider invoice')
        _write(root,data);return row.copy()
