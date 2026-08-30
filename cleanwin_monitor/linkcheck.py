from __future__ import annotations
import requests

def check_links(session: requests.Session, urls: list[str], timeout: int) -> list[dict]:
    results = []
    for url in sorted(set(urls)):
        try:
            r = session.head(url, allow_redirects=True, timeout=timeout)
            if r.status_code in (403, 405):
                r = session.get(url, allow_redirects=True, timeout=timeout, stream=True)
            if r.status_code >= 400:
                results.append({"url": url, "status": r.status_code})
        except requests.RequestException as exc:
            results.append({"url": url, "status": "fetch_error", "error": str(exc)})
    return results
