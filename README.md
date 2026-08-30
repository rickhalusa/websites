# Cleanwin Website Change Monitor

Mehrstufiger Website-Crawler für tägliche Landingpage-Überwachung.

## Prinzip

```text
Sitemap
  ↓
Conditional HTTP Request
  ↓
HTML normalisieren
  ↓
SEO-Felder + Inhaltsblöcke extrahieren
  ↓
Hashes vergleichen
  ↓
keine Änderung → Ende
  ↓
Änderung → Vorher/Nachher + Diff
  ↓
Relevanz einstufen
  ↓
nur relevante Änderung → AI Queue
```

Der Crawler selbst verwendet keine KI.

## Installation

```bash
python -m pip install -r requirements.txt
```

## Test

```bash
python -m cleanwin_monitor.cli --self-test
```

## Erster Lauf

```bash
python -m cleanwin_monitor.cli --mode daily
```

Der erste Lauf erzeugt die Baseline. Er soll nicht als inhaltlicher Alarm interpretiert werden.

## Folgeprüfung

```bash
python -m cleanwin_monitor.cli --mode daily
```

Erzeugte Dateien:

```text
reports/summary.json
reports/changes.json
reports/report.md
reports/ai_queue.jsonl
reports/fetch_failures.json
state/index.json
state/pages/*.json
```

## Daily

Schneller Content- und SEO-Change-Check.

## Weekly

Daily plus technischer Check der internen Links.

```bash
python -m cleanwin_monitor.cli --mode weekly
```

## Monthly

Weekly plus vollständige Audit-Queue.

```bash
python -m cleanwin_monitor.cli --mode monthly
```

## GitHub Actions

`.github/workflows/website-monitor.yml` enthält:

- Werktags Daily
- sonntags Weekly
- monatlich Monthly
- manueller Start

Die Baseline und Reports werden nach dem Lauf wieder in das Repository committed.

Damit bleibt die Vergleichsbasis zwischen GitHub-Action-Läufen erhalten.

## Kostenlogik

161 unveränderte Seiten benötigen keine KI-Analyse.

Nur Einträge in:

```text
reports/ai_queue.jsonl
```

werden später an ChatGPT bzw. den Prüf-Skill übergeben.

## Wichtige Filter

Der Monitor ignoriert typische volatile Elemente wie Cookie-Banner, Script-Code, Styles, Nonces und Ladehinweise.

Abruffehler werden separat protokolliert und lösen keine Content-KI-Prüfung aus.
