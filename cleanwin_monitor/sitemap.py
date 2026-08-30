from __future__ import annotations
from pathlib import Path
from typing import List
import xml.etree.ElementTree as ET
import requests
from .utils import canonicalize_url

def parse_sitemap(xml_text: str) -> List[str]:
    root = ET.fromstring(xml_text)
    urls = []
    for elem in root.iter():
        if elem.tag.endswith("loc") and elem.text:
            value = elem.text.strip()
            if value.startswith(("http://", "https://")):
                urls.append(canonicalize_url(value))
    return list(dict.fromkeys(urls))

def load_sitemap(
    session: requests.Session,
    sitemap_url: str | None,
    local_path: Path | None,
    timeout: int
) -> List[str]:
    if sitemap_url:
        try:
            r = session.get(sitemap_url, timeout=timeout)
            r.raise_for_status()
            urls = parse_sitemap(r.text)
            if urls:
                return urls
        except Exception:
            pass

    if not local_path or not local_path.exists():
        raise RuntimeError("Weder Remote- noch lokale Sitemap konnte geladen werden.")
    return parse_sitemap(local_path.read_text(encoding="utf-8"))
