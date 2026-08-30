from __future__ import annotations
import time
import requests

class FetchResult:
    def __init__(self, response=None, error=None, not_modified=False):
        self.response = response
        self.error = error
        self.not_modified = not_modified

def fetch_page(session, url, old_state, cfg):
    headers = {}
    if old_state:
        if old_state.get("etag"):
            headers["If-None-Match"] = old_state["etag"]
        if old_state.get("last_modified"):
            headers["If-Modified-Since"] = old_state["last_modified"]

    attempts = int(cfg.get("retries", 2)) + 1
    timeout = int(cfg.get("timeout_seconds", 20))
    backoff = float(cfg.get("retry_backoff_seconds", 1.0))

    last_error = None
    for attempt in range(attempts):
        try:
            r = session.get(url, headers=headers, timeout=timeout, allow_redirects=True)
            if r.status_code == 304:
                return FetchResult(not_modified=True)
            return FetchResult(response=r)
        except requests.RequestException as exc:
            last_error = str(exc)
            if attempt + 1 < attempts:
                time.sleep(backoff * (attempt + 1))

    return FetchResult(error=last_error or "Unbekannter Abruffehler")
