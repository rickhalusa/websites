from __future__ import annotations
import difflib
from .models import Change, PageSnapshot
from .utils import short_text

def _field_change(old, new, limit):
    return {"before": short_text(old if isinstance(old, str) else str(old), limit), "after": short_text(new if isinstance(new, str) else str(new), limit)}

def _block_diff(old_text: str, new_text: str, max_diff: int, max_text: int):
    old_lines = [x.strip() for x in (old_text or "").split(". ") if x.strip()]
    new_lines = [x.strip() for x in (new_text or "").split(". ") if x.strip()]
    diff = "\n".join(difflib.unified_diff(old_lines, new_lines, fromfile="vorher", tofile="nachher", lineterm=""))
    return {"before": short_text(old_text, max_text), "after": short_text(new_text, max_text), "diff": short_text(diff, max_diff), "similarity": round(difflib.SequenceMatcher(None, old_text or "", new_text or "").ratio(), 4)}

def compare(old: dict | None, new: PageSnapshot, cfg: dict) -> Change | None:
    if old is None:
        return Change(url=new.url, risk="info", categories=["baseline"], reasons=["Baseline erstellt"], status=new.status, final_url=new.final_url, first_baseline=True)
    if old.get("semantic_hash") == new.semantic_hash and int(old.get("status", 0)) == new.status:
        return None
    c = Change(url=new.url, risk="low", status=new.status, final_url=new.final_url)
    limit = int(cfg.get("max_before_after_chars", 3000))
    max_diff = int(cfg.get("max_diff_chars_per_block", 5000))
    if int(old.get("status", 0)) != new.status:
        c.categories.append("transport")
        c.reasons.append(f"HTTP-Status {old.get('status')} → {new.status}")
        c.fields["status"] = _field_change(old.get("status"), new.status, limit)
    if old.get("final_url", "") != new.final_url:
        c.categories.append("redirect")
        c.reasons.append("Finale URL geändert")
        c.fields["final_url"] = _field_change(old.get("final_url", ""), new.final_url, limit)
    important = [("title", new.title, "Title", "medium"), ("description", new.description, "Meta Description", "medium"), ("h1", new.h1, "H1", "medium"), ("canonical", new.canonical, "Canonical", "high"), ("robots", new.robots, "Robots", "high"), ("jsonld", new.jsonld, "Strukturierte Daten", "medium"), ("internal_links", new.internal_links, "Interne Links", "low")]
    rank = {"info": 0, "low": 1, "medium": 2, "high": 3, "critical": 4}
    risk = "low"
    for key, new_value, label, field_risk in important:
        old_value = old.get(key)
        if old_value != new_value:
            c.categories.append(key)
            c.reasons.append(f"{label} geändert")
            c.fields[key] = _field_change(old_value, new_value, limit)
            if rank[field_risk] > rank[risk]:
                risk = field_risk
    old_robots = (old.get("robots") or "").lower()
    new_robots = (new.robots or "").lower()
    if "noindex" not in old_robots and "noindex" in new_robots:
        c.reasons.append("noindex neu gesetzt")
        risk = "critical"
    old_blocks = old.get("blocks") or {}
    new_blocks = new.to_dict().get("blocks") or {}
    keys = sorted(set(old_blocks) | set(new_blocks))
    total_old = sum(len((v or {}).get("text", "")) for v in old_blocks.values())
    total_new = sum(len((v or {}).get("text", "")) for v in new_blocks.values())
    total_max = max(total_old, total_new, 1)
    content_delta = abs(total_new - total_old) / total_max
    for key in keys:
        ob = old_blocks.get(key)
        nb = new_blocks.get(key)
        if ob and nb and ob.get("digest") == nb.get("digest"):
            continue
        before = (ob or {}).get("text", "")
        after = (nb or {}).get("text", "")
        if before == after:
            continue
        c.blocks[key] = _block_diff(before, after, max_diff, limit)
    if c.blocks:
        c.categories.append("content")
        c.reasons.append(f"{len(c.blocks)} Inhaltsblock/-blöcke geändert")
        medium = float(cfg.get("content_change_medium_ratio", 0.03))
        high = float(cfg.get("content_change_high_ratio", 0.20))
        if content_delta >= high:
            risk = max(risk, "high", key=lambda x: rank[x])
            c.reasons.append(f"Grössere Inhaltsänderung ({content_delta:.1%})")
        elif content_delta >= medium:
            risk = max(risk, "medium", key=lambda x: rank[x])
    if old.get("title") and not new.title:
        c.reasons.append("Title entfernt")
        risk = "high"
    if old.get("h1") and not new.h1:
        c.reasons.append("H1 entfernt")
        risk = "high"
    old_chars = int(old.get("content_chars") or 0)
    if old_chars > 0 and new.content_chars < old_chars * 0.35:
        c.reasons.append("Hauptinhalt stark geschrumpft")
        risk = "critical"
    c.categories = list(dict.fromkeys(c.categories))
    c.reasons = list(dict.fromkeys(c.reasons))
    c.risk = risk
    return c
