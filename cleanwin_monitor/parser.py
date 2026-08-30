from __future__ import annotations
import json
import re
from collections import OrderedDict
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup, Comment
from .models import Block, PageSnapshot
from .utils import normalize_space, sha256_text, slug, same_host, canonicalize_url

def _strip_noise(soup: BeautifulSoup, cfg: dict) -> None:
    for tag in soup(["script", "style", "noscript", "svg", "iframe", "template"]):
        tag.decompose()
    for comment in soup.find_all(string=lambda t: isinstance(t, Comment)):
        comment.extract()
    for selector in cfg.get("ignore_selectors", []):
        try:
            for node in soup.select(selector):
                node.decompose()
        except Exception:
            continue
    volatile = set(x.lower() for x in cfg.get("volatile_attributes", []))
    for tag in soup.find_all(True):
        for attr in list(tag.attrs):
            low = attr.lower()
            if low in volatile or low.startswith("data-wp-"):
                del tag.attrs[attr]

def _clean_text(text: str, cfg: dict) -> str:
    text = normalize_space(text)
    if not text:
        return ""
    for pattern in cfg.get("ignore_text_patterns", []):
        try:
            if re.match(pattern, text, flags=re.I):
                return ""
        except re.error:
            pass
    return text

def _jsonld(raw_html: str) -> str:
    soup = BeautifulSoup(raw_html, "lxml")
    values = []
    for node in soup.find_all("script", attrs={"type": re.compile(r"ld\+json", re.I)}):
        raw = (node.string or node.get_text(" ", strip=True) or "").strip()
        if not raw:
            continue
        try:
            obj = json.loads(raw)
            raw = json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        except Exception:
            raw = normalize_space(raw)
        values.append(raw)
    return "\n".join(sorted(values))

def _main_node(soup: BeautifulSoup, cfg: dict):
    for selector in cfg.get("main_selectors", ["main", "article", "body"]):
        try:
            node = soup.select_one(selector)
        except Exception:
            node = None
        if node:
            return node
    return soup.body or soup

def _extract_blocks(main, cfg: dict) -> OrderedDict[str, Block]:
    candidates = [x for x in main.find_all(["section", "article"], recursive=False)]
    if len(candidates) < 2:
        candidates = [x for x in main.find_all(["section", "article"])]
    if not candidates:
        candidates = [x for x in getattr(main, "children", []) if getattr(x, "name", None)]
    blocks = OrderedDict()
    seen = {}
    for idx, node in enumerate(candidates, 1):
        text = _clean_text(node.get_text(" ", strip=True), cfg)
        if not text:
            continue
        heading_node = node.find(["h1", "h2", "h3"])
        heading = _clean_text(heading_node.get_text(" ", strip=True), cfg) if heading_node else ""
        ident = (node.get("id") or "").strip()
        base = slug(ident or heading or f"{node.name}-{idx}")
        seen[base] = seen.get(base, 0) + 1
        key = base if seen[base] == 1 else f"{base}-{seen[base]}"
        blocks[key] = Block(key=key, heading=heading, text=text, digest=sha256_text(text))
    if not blocks:
        text = _clean_text(main.get_text(" ", strip=True), cfg)
        blocks["main"] = Block("main", "", text, sha256_text(text))
    return blocks

def parse_page(requested_url: str, response, cfg: dict) -> PageSnapshot:
    raw_html = response.text
    raw_soup = BeautifulSoup(raw_html, "lxml")
    title = normalize_space(raw_soup.title.get_text(" ", strip=True) if raw_soup.title else "")
    desc = raw_soup.find("meta", attrs={"name": re.compile(r"^description$", re.I)})
    description = normalize_space(desc.get("content", "") if desc else "")
    h1 = [normalize_space(x.get_text(" ", strip=True)) for x in raw_soup.find_all("h1")]
    h1 = [x for x in h1 if x]
    canonical = ""
    for link in raw_soup.find_all("link", href=True):
        rel = link.get("rel") or []
        rel = rel if isinstance(rel, list) else [rel]
        if any(str(x).lower() == "canonical" for x in rel):
            canonical = urljoin(response.url, link.get("href", "").strip())
            break
    canonical = canonicalize_url(canonical) if canonical else ""
    robots = raw_soup.find("meta", attrs={"name": re.compile(r"^robots$", re.I)})
    robots = normalize_space(robots.get("content", "") if robots else "")
    jsonld = _jsonld(raw_html)
    soup = BeautifulSoup(raw_html, "lxml")
    _strip_noise(soup, cfg)
    main = _main_node(soup, cfg)
    blocks = _extract_blocks(main, cfg)
    links = set()
    for a in main.find_all("a", href=True):
        href = urljoin(response.url, a.get("href", "").strip())
        p = urlparse(href)
        if p.scheme in ("http", "https") and same_host(response.url, href):
            links.add(canonicalize_url(href))
    internal_links = sorted(links)
    content_chars = sum(len(x.text) for x in blocks.values())
    payload = {"title": title, "description": description, "h1": h1, "canonical": canonical, "robots": robots, "internal_links": internal_links, "jsonld": jsonld, "blocks": {k: v.digest for k, v in blocks.items()}}
    semantic_hash = sha256_text(json.dumps(payload, ensure_ascii=False, sort_keys=True))
    return PageSnapshot(url=canonicalize_url(requested_url), final_url=canonicalize_url(response.url), status=response.status_code, content_type=response.headers.get("Content-Type", ""), etag=response.headers.get("ETag", ""), last_modified=response.headers.get("Last-Modified", ""), title=title, description=description, h1=h1, canonical=canonical, robots=robots, internal_links=internal_links, jsonld=jsonld, blocks=dict(blocks), semantic_hash=semantic_hash, content_chars=content_chars, html_bytes=len(response.content))
