from __future__ import annotations
import json
from pathlib import Path
from .utils import dump_json

def write_reports(report_dir: Path, summary: dict, changes: list[dict], fetch_failures: list[dict], ai_queue: list[dict]):
    report_dir.mkdir(parents=True, exist_ok=True)

    dump_json(report_dir / "summary.json", summary)
    dump_json(report_dir / "changes.json", changes)
    dump_json(report_dir / "fetch_failures.json", fetch_failures)

    with (report_dir / "ai_queue.jsonl").open("w", encoding="utf-8") as f:
        for row in ai_queue:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    lines = [
        "# Cleanwin Änderungsbericht",
        "",
        f"Modus {summary['mode']}",
        f"URLs in Sitemap {summary['urls_in_sitemap']}",
        f"Geprüft {summary['checked']}",
        f"Unverändert {summary['unchanged']}",
        f"Geändert {summary['changed']}",
        f"Baseline {summary['baseline']}",
        f"Abruffehler {summary['fetch_failures']}",
        f"AI Queue {summary['ai_queue']}",
        "",
    ]

    relevant = [x for x in changes if not x.get("first_baseline")]
    if not relevant:
        lines += ["## Ergebnis", "", "Keine relevanten Inhaltsänderungen erkannt.", ""]
    else:
        lines += ["## Änderungen", ""]
        for change in relevant:
            lines += [
                f"### {change['url']}",
                "",
                f"Risiko {change['risk']}",
                "",
                "Gründe",
                "",
            ]
            for reason in change.get("reasons", []):
                lines.append(f"- {reason}")
            lines.append("")

            if change.get("fields"):
                lines += ["Feldänderungen", ""]
                for name, value in change["fields"].items():
                    lines += [
                        f"#### {name}",
                        "",
                        "Vorher",
                        "",
                        "```text",
                        str(value.get("before", "")),
                        "```",
                        "",
                        "Nachher",
                        "",
                        "```text",
                        str(value.get("after", "")),
                        "```",
                        "",
                    ]

            if change.get("blocks"):
                lines += ["Inhaltsblöcke", ""]
                for name, value in change["blocks"].items():
                    lines += [
                        f"#### {name}",
                        "",
                        "Vorher",
                        "",
                        "```text",
                        value.get("before", ""),
                        "```",
                        "",
                        "Nachher",
                        "",
                        "```text",
                        value.get("after", ""),
                        "```",
                        "",
                        "Diff",
                        "",
                        "```diff",
                        value.get("diff", ""),
                        "```",
                        "",
                    ]

    if fetch_failures:
        lines += [
            "## Abruffehler",
            "",
            "Diese Einträge werden separat protokolliert und nicht als Inhaltsänderung an die KI weitergegeben.",
            ""
        ]
        for item in fetch_failures:
            lines.append(f"- {item['url']} — {item['error']}")

    (report_dir / "report.md").write_text("\n".join(lines), encoding="utf-8")
