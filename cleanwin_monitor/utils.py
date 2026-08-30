from __future__ import annotations
import hashlib
import json
import re
from pathlib import Path
from urllib.parse import urlparse, urlunparse

def sha256_text(value: str) -> str:
    return hashlib.sha256((value or "").encode("utf-8", errors="ignore")).hexdigest()

def normalize_space(value: str) -> str:
    return re.sub(r"\s+", " ", value or "").strip()

def slug(value: str, max_len: int = 70) -> str:
    value = normalize_space(value).lower()
    value = re.sub(r"[^a-z0-9äöüéèàç_-]+", "-", value, flags=re.I)
    value = re.sub(r"-+", "-", value).strip("-")
    return value[:max_len] or "block"

def canonicalize_url(url: str) -> str:
    p = urlparse(url)
    path = re.sub(r"/+", "/", p.path or "/")
    if not path.endswith("/") and "." not in path.rsplit("/", 1)[-1]:
        path += "/"
    return urlunparse((p.scheme.lower(), p.netloc.lower(), path, "", p.query, ""))

def same_host(a: str, b: str) -> bool:
    return urlparse(a).netloc.lower() == urlparse(b).netloc.lower()

def load_json(path: Path, default):
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))

def dump_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")

def short_text(text: str, limit: int) -> str:
    text = text or ""
    if len(text) <= limit:
        return text
    return text[:limit] + "\n… [gekürzt]"
