#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import emotion_engine as ee


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATASET = ROOT / "assets" / "community-posthoc-calibration-v2.jsonl"


def load_jsonl(path: Path) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        rows.append(json.loads(line))
    return rows


def bootstrap_payload(message: str) -> dict[str, object]:
    return {
        "message": message,
        "calibration_state": {
            "observed_turns": 0,
            "posthoc_samples": 0,
            "consistency_samples": 0,
            "stable_prediction_hits": 0,
            "prediction_agreement": 0.0,
            "consistency_rate": 0.0,
        },
    }


def build_pack_row(case: dict[str, object]) -> dict[str, object]:
    payload = bootstrap_payload(str(case.get("message") or ""))
    result = ee.run_pipeline(payload)
    return {
        "id": case.get("id"),
        "source_url": case.get("source_url"),
        "message": case.get("message"),
        "expected_labels": case.get("expected_labels", []),
        "front_labels": result["initial_screen"]["labels"],
        "front_emotion_vector": result["initial_screen"]["emotion_vector"],
        "weight_schedule": result["weight_schedule"],
        "posthoc_plan": result["posthoc_plan"],
        "posthoc_shadow": result["posthoc_shadow"],
        "posthoc_reflection_prompt": result["prompts"]["posthoc_reflection_prompt"],
    }


def build_summary(rows: list[dict[str, object]]) -> dict[str, object]:
    label_counter: Counter[str] = Counter()
    source_counter: Counter[str] = Counter()
    for row in rows:
        for label in row.get("expected_labels", []):
            label_counter[str(label)] += 1
        source_counter[str(row.get("source_url") or "")] += 1
    return {
        "total_cases": len(rows),
        "label_counts": dict(sorted(label_counter.items())),
        "source_counts": dict(sorted(source_counter.items())),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a cold-start posthoc calibration pack from community issue samples.")
    parser.add_argument("--dataset", default=str(DEFAULT_DATASET), help="Path to the JSONL dataset.")
    parser.add_argument("--mode", choices=("pack", "summary"), default="pack")
    parser.add_argument("--limit", type=int, default=0, help="Limit the number of rows.")
    parser.add_argument("--output", help="Optional output path.")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON.")
    args = parser.parse_args()

    dataset_path = Path(args.dataset)
    rows = load_jsonl(dataset_path)
    if args.limit > 0:
        rows = rows[: args.limit]

    if args.mode == "summary":
        rendered_obj: object = build_summary(rows)
    else:
        rendered_obj = [build_pack_row(row) for row in rows]

    rendered = json.dumps(rendered_obj, ensure_ascii=False, indent=2 if args.pretty else None)
    if args.output:
        Path(args.output).write_text(rendered, encoding="utf-8")
    else:
        print(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
