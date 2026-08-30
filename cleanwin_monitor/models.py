from __future__ import annotations
from dataclasses import dataclass, asdict, field
from typing import Dict, List

@dataclass
class Block:
    key: str
    heading: str
    text: str
    digest: str

@dataclass
class PageSnapshot:
    url: str
    final_url: str
    status: int
    content_type: str
    etag: str
    last_modified: str
    title: str
    description: str
    h1: List[str]
    canonical: str
    robots: str
    internal_links: List[str]
    jsonld: str
    blocks: Dict[str, Block]
    semantic_hash: str
    content_chars: int
    html_bytes: int

    def to_dict(self):
        d = asdict(self)
        return d

@dataclass
class Change:
    url: str
    risk: str
    categories: List[str] = field(default_factory=list)
    reasons: List[str] = field(default_factory=list)
    fields: Dict[str, dict] = field(default_factory=dict)
    blocks: Dict[str, dict] = field(default_factory=dict)
    status: int = 0
    final_url: str = ""
    first_baseline: bool = False

    def to_dict(self):
        return asdict(self)
