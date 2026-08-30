---
name: cleanwin-website-pruefung
description: Kosteneffiziente mehrstufige Prüfung der Cleanwin-Website. Nutzt den GitHub-Crawler als deterministische Vorstufe und analysiert mit KI nur relevante Änderungen.
---

# Cleanwin Website Prüfung

## Ziel

Die Website darf nicht bei jedem Prüflauf vollständig durch einen Agenten analysiert werden.

Der Crawler ist die erste Instanz.

Er lädt die Landingpages, normalisiert den sichtbaren Inhalt, bildet Hashes und vergleicht den aktuellen Stand mit der gespeicherten Baseline.

Nur relevante Änderungen werden für eine KI-Prüfung vorbereitet.

## Verbindlicher Ablauf

1. Crawler im gewünschten Modus ausführen.
2. `reports/summary.json` lesen.
3. Wenn `ai_queue` gleich 0 ist, keine Landingpage mit KI erneut vollständig prüfen.
4. Wenn `ai_queue` grösser als 0 ist, `reports/ai_queue.jsonl` lesen.
5. Zuerst ausschliesslich die gelieferten Vorher-/Nachher-Werte und Diffs analysieren.
6. Eine Landingpage nur dann vollständig laden, wenn der Diff zur Bewertung nicht ausreicht.
7. Ergebnis pro Änderung mit direkter URL ausgeben.

## Modi

### daily

Tägliche Änderungserkennung.

Prüft semantisch:

- Title
- Meta Description
- H1
- Canonical
- Robots
- JSON-LD
- interne Links
- sichtbare Inhaltsblöcke

Unveränderte Seiten enden nach Hash-/Conditional-Request-Prüfung.

### weekly

Enthält `daily` und prüft zusätzlich interne Links technisch.

### monthly

Enthält `weekly` und erzeugt zusätzlich eine vollständige Audit-Queue für alle Landingpages.

## Abruffehler

Abruffehler werden wiederholt versucht und separat in `reports/fetch_failures.json` gespeichert.

Sie gelten nicht als Contentänderung.

Sie werden standardmässig nicht an die KI weitergereicht.

Keine Warnungen erzeugen für:

- "wird geladen"
- React-Hydration-Effekte
- reine Messlücken
- volatile Tracking- oder Cookie-Elemente

## Contentänderungen

Im Report müssen bei jeder relevanten Änderung direkt sichtbar sein:

- URL
- Risiko
- geänderter Bereich
- Inhalt vorher
- Inhalt nachher
- Diff

Der Nutzer darf die Vergleichswerte nicht manuell in Snapshot-Dateien suchen müssen.

## GitHub

Der Crawler speichert seine Baseline unter `state/`.

GitHub Actions führt die Prüfungen automatisch aus.

Berichte liegen unter `reports/`.

Die Datei `reports/ai_queue.jsonl` ist die Übergabe an den KI-Prüfschritt.

## Befehle

```bash
python -m cleanwin_monitor.cli --self-test
python -m cleanwin_monitor.cli --mode daily
python -m cleanwin_monitor.cli --mode weekly
python -m cleanwin_monitor.cli --mode monthly
```
