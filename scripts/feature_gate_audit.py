#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = ROOT / "assets" / "feature-cluster-registry.json"
sys.path.insert(0, str(ROOT / "scripts"))

import alignment_test
import ablation_test


def main() -> int:
    registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    clusters = registry.get("clusters", [])
    core = [cluster for cluster in clusters if cluster.get("runtime_tier") == "core"]
    candidate = [cluster for cluster in clusters if cluster.get("runtime_tier") == "candidate"]
    alignment_ids = {case["id"] for case in alignment_test.CASES}
    ablation_ids = {case["id"] for case in ablation_test.REAL_WORLD_CASES}

    failures: list[dict[str, object]] = []
    for cluster in core:
        support = cluster.get("support", {})
        missing = [key for key in ("research", "community", "benchmark") if not bool(support.get(key))]
        missing_alignment = [case_id for case_id in cluster.get("alignment_cases", []) if case_id not in alignment_ids]
        missing_ablation = [case_id for case_id in cluster.get("ablation_cases", []) if case_id not in ablation_ids]
        if missing or missing_alignment or missing_ablation:
            failures.append(
                {
                    "id": cluster.get("id"),
                    "missing_support": missing,
                    "missing_alignment_cases": missing_alignment,
                    "missing_ablation_cases": missing_ablation,
                }
            )

    summary = {
        "registry_version": registry.get("version"),
        "languages_specialized": registry.get("policy", {}).get("languages_specialized", []),
        "core_clusters": len(core),
        "candidate_clusters": len(candidate),
        "core_ok": len(failures) == 0,
        "failures": failures,
        "alignment_case_count": len(alignment_ids),
        "ablation_case_count": len(ablation_ids),
        "core_ids": [cluster.get("id") for cluster in core],
        "candidate_ids": [cluster.get("id") for cluster in candidate],
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
