#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]

SCENARIOS: list[dict[str, Any]] = [
    {
        "id": "regression-loop-scope-violation",
        "family": "repeated failure",
        "source": "https://github.com/anthropics/claude-code/issues/4520",
        "expected_terms": ["basis first", "failed path", "scope"],
    },
    {
        "id": "missing-tool-result-dead-state",
        "family": "silent tool failure",
        "source": "https://github.com/CopilotKit/CopilotKit/issues/2504",
        "expected_terms": ["missing failure path", "avoid guessing", "host/tool contract"],
    },
    {
        "id": "path-special-character-ambiguity",
        "family": "confusion",
        "source": "https://github.com/orgs/community/discussions/145254",
        "expected_terms": ["exact path", "inspected boundary", "fix"],
    },
    {
        "id": "repo-grounding-limits",
        "family": "evidence-first",
        "source": "https://github.com/orgs/community/discussions/162634",
        "expected_terms": ["code was inspected", "not yet known", "files/tests"],
    },
    {
        "id": "silent-background-job-alert-gap",
        "family": "silent progress risk",
        "source": "https://www.reddit.com/r/SaaS/comments/1sb8esi/my_automated_background_jobs_silently_broke_for_3/",
        "expected_terms": ["progress visible", "next checkpoint", "check/alert path"],
    },
    {
        "id": "post-success-closeout-guard",
        "family": "post-success closeout",
        "source": "field-pattern: accepted fix closeout",
        "expected_terms": ["summarize completed scope", "smoke/regression", "stop expanding"],
    },
]


def read_reference(name: str) -> str:
    return (ROOT / "references" / name).read_text(encoding="utf-8").lower()


def main() -> int:
    routing = read_reference("routing-playbook.md")
    constraints = read_reference("response-constraints.md")
    scenario_doc = read_reference("real-scenarios.md")
    rows: list[dict[str, Any]] = []

    for scenario in SCENARIOS:
        scenario_id = scenario["id"]
        family = scenario["family"]
        expected_terms = scenario["expected_terms"]
        doc_hit = scenario_id in scenario_doc
        family_hit = family in scenario_doc and family in (scenario_doc + "\n" + routing)
        behavior_hits = [term for term in expected_terms if term in scenario_doc or term in constraints or term in routing]
        ok = doc_hit and family_hit and len(behavior_hits) >= max(2, len(expected_terms) - 1)
        rows.append(
            {
                "id": scenario_id,
                "source": scenario["source"],
                "ok": ok,
                "family": family,
                "documented": doc_hit,
                "family_covered": family_hit,
                "behavior_hits": behavior_hits,
                "missing_terms": [term for term in expected_terms if term not in behavior_hits],
            }
        )

    anti_overfit = (
        "not exact phrase triggers" in scenario_doc
        and "new synonym" in scenario_doc
        and "phrase-specific routing rules" in routing
    )
    rows.append(
        {
            "id": "anti-one-case-fix",
            "source": "release policy",
            "ok": anti_overfit,
            "detail": "scenario doc requires family-level routing rather than exact phrase patches",
        }
    )

    result = {"ok": all(row["ok"] for row in rows), "count": len(rows), "rows": rows}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
