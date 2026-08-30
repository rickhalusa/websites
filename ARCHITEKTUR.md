# Architektur

## Stufe 0

Conditional Requests über ETag und Last-Modified.

HTTP 304 beendet die Seite sofort.

## Stufe 1

HTML laden und normalisieren.

Scripts, Styles, Cookie-Banner, volatile Attribute und Ladehinweise werden entfernt.

## Stufe 2

Deterministische Extraktion von:

- Title
- Description
- H1
- Canonical
- Robots
- JSON-LD
- internen Links
- semantischen Inhaltsblöcken

Jedes Element erhält einen SHA-256-Hash.

## Stufe 3

Hashvergleich mit der GitHub-Baseline.

Unverändert bedeutet Ende.

## Stufe 4

Nur geänderte Felder und Blöcke erzeugen Vorher/Nachher und Unified Diff.

## Stufe 5

Regelbasierte Risikoeinstufung.

Nur `medium`, `high` und `critical` werden standardmässig in die AI Queue geschrieben.

## Stufe 6

Der Skill analysiert nur die AI Queue.

Die vollständige Landingpage wird nur geladen, wenn der Diff nicht ausreicht.
