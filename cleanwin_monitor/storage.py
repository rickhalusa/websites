from __future__ import annotations
import hashlib
from pathlib import Path
from .models import PageSnapshot
from .utils import load_json, dump_json

def _page_key(url: str) -> str:
    return hashlib.sha1(url.encode("utf-8")).hexdigest()

class StateStore:
    def __init__(self, root: Path):
        self.root = root
        self.pages_dir = root / "pages"
        self.index_path = root / "index.json"
        self.pages_dir.mkdir(parents=True, exist_ok=True)
        self.index = load_json(self.index_path, {"urls": {}})

    def get(self, url: str):
        key = self.index.get("urls", {}).get(url)
        if not key:
            return None
        path = self.pages_dir / f"{key}.json"
        return load_json(path, None)

    def put(self, snapshot: PageSnapshot):
        key = _page_key(snapshot.url)
        self.index.setdefault("urls", {})[snapshot.url] = key
        dump_json(self.pages_dir / f"{key}.json", snapshot.to_dict())

    def save_index(self):
        dump_json(self.index_path, self.index)
