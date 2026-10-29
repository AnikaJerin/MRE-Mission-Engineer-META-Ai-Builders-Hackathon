"""Owner-invoked local file registration. Never downloads source material."""

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path

from .evidence import EvidenceError, read_json, validate_manifest


def _check_id(source_id):
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,80}", source_id):
        raise EvidenceError("Source ID must be a safe lowercase identifier")


def fingerprint(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def register_file(root, source_id, path):
    _check_id(source_id)
    root = Path(root).resolve()
    sources = validate_manifest(read_json(root / "sources/manifest.json"))
    if source_id not in sources:
        raise EvidenceError(f"Unknown source: {source_id}")
    path = Path(path).expanduser().resolve(strict=True)
    if not path.is_file() or path.stat().st_size == 0:
        raise EvidenceError("Choose a non-empty regular file")
    if sources[source_id]["format"].startswith("PDF"):
        with path.open("rb") as stream:
            if not stream.read(1024).lstrip().startswith(b"%PDF-"):
                raise EvidenceError("Expected PDF header; this may be a downloaded HTML error page")
    receipt = {
        "schema_version": "1.0", "source_id": source_id,
        "registered_at": datetime.now(timezone.utc).isoformat(),
        "path": str(path), "bytes": path.stat().st_size, "sha256": fingerprint(path),
        "source_url": sources[source_id]["url"],
        "status": "owner-registered-local-file",
        "verification_scope": "Local integrity only; source identity, contents and reuse rights are not certified",
    }
    target = root / "outputs/acquisitions" / f"{source_id}.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    # Registration is an explicit owner action; replace only this source's receipt.
    temporary = target.with_suffix(".json.tmp")
    temporary.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    temporary.replace(target)
    return receipt


def acquisition_status(root, source_id):
    _check_id(source_id)
    receipt_path = Path(root) / "outputs/acquisitions" / f"{source_id}.json"
    if not receipt_path.exists():
        return {"status": "not-registered"}
    try:
        receipt = read_json(receipt_path)
        if receipt.get("source_id") != source_id:
            raise EvidenceError("Receipt source mismatch")
        path = Path(receipt["path"])
        # Recheck file integrity; never trust the previous 'registered' status alone.
        if not path.is_file():
            status = "registered-file-missing"
        elif path.stat().st_size != receipt["bytes"] or fingerprint(path) != receipt["sha256"]:
            status = "registered-file-changed"
        else:
            status = "local-hash-matches"
        return {"status": status, "sha256": receipt["sha256"],
                "bytes": receipt["bytes"], "registered_at": receipt["registered_at"],
                "scope": "Integrity only, not scientific or license certification"}
    except (OSError, ValueError, KeyError, TypeError) as exc:
        return {"status": "receipt-needs-review", "reason": str(exc)}
