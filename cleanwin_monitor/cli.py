from __future__ import annotations
import argparse
import json
import time
from datetime import datetime, timezone
from pathlib import Path
import requests
from .diffing import compare
from .fetcher import fetch_page
from .linkcheck import check_links
from .parser import parse_page
from .reporting import write_reports
from .sitemap import load_sitemap
from .storage import StateStore
from .utils import load_json, dump_json
ROOT = Path(__file__).resolve().parents[1]

def run(mode: str, sitemap_url: str | None = None, local_sitemap: str | None = None):
    cfg = load_json(ROOT / "config.json", {})
    session = requests.Session()
    session.headers.update({"User-Agent": cfg.get("user_agent", "CleanwinChangeMonitor/2.0"), "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"})
    if sitemap_url is None:
        sitemap_url = cfg.get("sitemap_url")
    local_path = ROOT / (local_sitemap or cfg.get("local_sitemap", "sitemap.xml"))
    urls = load_sitemap(session=session, sitemap_url=sitemap_url, local_path=local_path, timeout=int(cfg.get("timeout_seconds", 20)))
    store = StateStore(ROOT / "state")
    changes, fetch_failures, ai_queue = [], [], []
    internal_links = set()
    unchanged = baseline = checked = 0
    delay = float(cfg.get("request_delay_seconds", 0.05))
    ai_risks = set(cfg.get("ai_risks", ["medium", "high", "critical"]))
    for url in urls:
        checked += 1
        old = store.get(url)
        result = fetch_page(session, url, old, cfg)
        if result.not_modified:
            unchanged += 1
            continue
        if result.error:
            fetch_failures.append({"url": url, "error": result.error})
            continue
        response = result.response
        if "text/html" not in (response.headers.get("Content-Type", "").lower()):
            fetch_failures.append({"url": url, "error": f"Kein HTML Content-Type: {response.headers.get('Content-Type', '')}"})
            continue
        snapshot = parse_page(url, response, cfg)
        internal_links.update(snapshot.internal_links)
        change = compare(old, snapshot, cfg)
        if change is None:
            unchanged += 1
        elif change.first_baseline:
            baseline += 1
            changes.append(change.to_dict())
        else:
            changes.append(change.to_dict())
            if change.risk in ai_risks:
                ai_queue.append({"url": change.url, "risk": change.risk, "reasons": change.reasons, "fields": change.fields, "blocks": change.blocks, "instruction": "Prüfe ausschliesslich die hier dokumentierte Änderung. Bewerte SEO, Content, unbeabsichtigte Änderung und geschäftliche Relevanz. Nutze Vorher/Nachher und den Diff. Lade die vollständige Landingpage nur, wenn diese Informationen für die Bewertung nicht ausreichen."})
        store.put(snapshot)
        if delay:
            time.sleep(delay)
    store.save_index()
    link_issues = []
    if mode in ("weekly", "monthly"):
        link_issues = check_links(session, list(internal_links), int(cfg.get("timeout_seconds", 20)))
        dump_json(ROOT / "reports" / "link_issues.json", link_issues)
    if mode == "monthly":
        queued = {x["url"] for x in ai_queue}
        for url in urls:
            if url not in queued:
                ai_queue.append({"url": url, "risk": "audit", "reasons": ["Monatlicher Vollaudit"], "fields": {}, "blocks": {}, "instruction": "Führe für diese Landingpage einen vollständigen SEO- und Content-Audit durch."})
    real_changes = [x for x in changes if not x.get("first_baseline")]
    summary = {"checked_at": datetime.now(timezone.utc).isoformat(), "mode": mode, "urls_in_sitemap": len(urls), "checked": checked, "unchanged": unchanged, "changed": len(real_changes), "baseline": baseline, "fetch_failures": len(fetch_failures), "ai_queue": len(ai_queue), "link_issues": len(link_issues), "risk_counts": {risk: sum(1 for x in real_changes if x.get("risk") == risk) for risk in ("low", "medium", "high", "critical")}}
    write_reports(ROOT / "reports", summary, changes, fetch_failures, ai_queue)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0

def self_test():
    from requests import Response
    cfg = load_json(ROOT / "config.json", {})
    html1 = '<!doctype html><html><head><title>Fensterreinigung Zürich</title><meta name="description" content="Professionelle Fensterreinigung"><link rel="canonical" href="https://cleanwin.ch/leistungen/fensterreinigung/zuerich/"></head><body><main><section><h1>Fensterreinigung Zürich</h1><p>Saubere Fenster für Unternehmen.</p></section><section><h2>Vorteile</h2><p>Schnell und zuverlässig.</p></section></main></body></html>'
    html2 = html1.replace("Saubere Fenster für Unternehmen.", "Saubere Fenster für Unternehmen und Verwaltungen.")
    def resp(html):
        r = Response(); r.status_code = 200; r.url = "https://cleanwin.ch/leistungen/fensterreinigung/zuerich/"; r._content = html.encode("utf-8"); r.headers["Content-Type"] = "text/html; charset=utf-8"; return r
    s1 = parse_page(resp(html1).url, resp(html1), cfg)
    s2 = parse_page(resp(html2).url, resp(html2), cfg)
    c1 = compare(None, s1, cfg); assert c1 and c1.first_baseline
    c2 = compare(s1.to_dict(), s2, cfg); assert c2 is not None and c2.blocks and any("Inhaltsblock" in x for x in c2.reasons)
    c3 = compare(s2.to_dict(), s2, cfg); assert c3 is None
    print("Self-Test erfolgreich: Baseline, Änderung und Unverändert-Erkennung funktionieren.")
    return 0

def main():
    p = argparse.ArgumentParser(description="Cleanwin mehrstufiger Website Change Monitor")
    p.add_argument("--mode", choices=["daily", "weekly", "monthly"], default="daily")
    p.add_argument("--sitemap-url", default=None)
    p.add_argument("--local-sitemap", default=None)
    p.add_argument("--self-test", action="store_true")
    args = p.parse_args()
    if args.self_test:
        raise SystemExit(self_test())
    raise SystemExit(run(args.mode, args.sitemap_url, args.local_sitemap))

if __name__ == "__main__":
    main()
