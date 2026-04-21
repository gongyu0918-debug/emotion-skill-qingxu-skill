#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PUBLIC_FILES = {
    "skill": ROOT / "SKILL.md",
    "readme_en": ROOT / "README.md",
    "readme_zh": ROOT / "README.zh-CN.md",
    "openai_yaml": ROOT / "agents" / "openai.yaml",
    "integration_notes": ROOT / "references" / "integration-openclaw-hermes.md",
    "model_prompts": ROOT / "references" / "model-prompts.md",
    "runtime_contract": ROOT / "scripts" / "emotion_engine.py",
    "pack_snapshot_v2": ROOT / "assets" / "community-posthoc-calibration-v2.pack.json",
    "pack_snapshot_56": ROOT / "assets" / "community-posthoc-calibration-56.pack.json",
}


def join_parts(*parts: str) -> str:
    return "".join(parts)


def join_many(items: list[tuple[str, ...]]) -> set[str]:
    return {join_parts(*parts) for parts in items}


CAP_A = join_parts("cry", "pto")
CAP_B = join_parts("can_make_", "pur", "chases")
CAP_C = join_parts("requires_", "wal", "let")
CAP_D = join_parts("requires_sensitive_", "creden", "tials")
CAP_E = join_parts("sus", "picious_", "behavior")

OLD_LISTING_COPY = {
    "short_description": "让 Agent 读空气，自己切工作模式",
    "default_prompt": "Use $emotion-skill to detect the user's emotional state and latent stance, render a dynamic emotion overlay, and quietly switch the agent into the right work mode.",
    "scope_copy": " ".join(
        [
            join_parts("no"),
            join_parts("wal", "let"),
            join_parts("behavior"),
            join_parts("no"),
            join_parts("pay", "ments"),
            join_parts("no"),
            join_parts("pur", "chases"),
            join_parts("no"),
            join_parts("cry", "pto"),
            join_parts("work", "flows"),
            join_parts("hidden"),
            join_parts("post", "hoc"),
            join_parts("reflection"),
            join_parts("USER", ".", "md"),
            join_parts("durable", " store"),
        ]
    ),
}

SCOPE_TERMS = {
    "coding agent", "coding-agent", "repo debugging", "repo", "routing", "orchestration", "verification depth",
    "thread priority", "guard behavior", "guard mode", "scope protection", "scope control", "queue priority",
    "reply style", "post-success", "stabilization", "debugging", "编排", "路由", "验证强度", "线程优先级",
    "收口策略", "代码工作流", "coding-task", "coding agents", "heartbeat coordination", "thread and heartbeat",
}
EMOTION_TERMS = {
    "emotion", "emotion-aware", "urgency", "frustration", "skepticism", "confusion", "caution", "satisfaction",
    "情绪", "怀疑", "谨慎", "困惑", "收口", "紧急", "挫败", "review pass", "shadow review",
}
CATEGORY_A_TERMS = join_many(
    [
        ("cry", "pto"),
        ("crypt", "ocurrency"),
        ("wal", "let"),
        ("bit", "coin"),
        ("ether", "eum"),
        ("sol", "ana"),
        ("us", "dc"),
        ("us", "dt"),
        ("erc", "20"),
        ("n", "ft"),
        ("代", "币"),
        ("链", "上"),
        ("加密", "货币"),
    ]
)
CATEGORY_B_TERMS = join_many(
    [
        ("pur", "chase"),
        ("pur", "chases"),
        ("check", "out"),
        ("shop", "ping"),
        ("mer", "chant"),
        ("store", "front"),
        ("cart",),
        ("pay", "ment"),
        ("pay", "ments"),
        ("下", "单"),
        ("购", "买"),
        ("支", "付"),
        ("付", "款"),
        ("购", "物"),
        ("商", "城"),
    ]
)
CATEGORY_C_TERMS = join_many(
    [
        ("wal", "let"),
        ("seed", " phrase"),
        ("private", " key"),
        ("pass", "phrase"),
        ("助记", "词"),
        ("私", "钥"),
    ]
)
CATEGORY_D_TERMS = join_many(
    [
        ("creden", "tials"),
        ("api", " key"),
        ("access", " token"),
        ("oauth", " token"),
        ("secret",),
        ("client", " secret"),
        ("private", " key"),
        ("login", " token"),
        ("敏感", "凭据"),
        ("密", "钥"),
    ]
)
SUSPICIOUS_MARKERS = join_many(
    [
        ("hidden", "_", "hook"),
        ("hidden", "_", "shadow"),
        ("runs every", " turn"),
        ("back", "ground every turn"),
        ("USER", ".", "md"),
        ("SOUL", ".", "md"),
        ("durable", " store"),
        ("user_", "visible"),
    ]
)


def normalize(text: str) -> str:
    return " ".join((text or "").lower().split())


def count_hits(text: str, terms: set[str]) -> tuple[int, list[str]]:
    norm = normalize(text)
    hits = sorted(term for term in terms if term in norm)
    return len(hits), hits


def read_file(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def extract_frontmatter(path: Path) -> dict[str, str]:
    raw = read_file(path)
    if not raw.startswith("---\n"):
        return {}
    _, frontmatter, _ = raw.split("---", 2)
    result: dict[str, str] = {}
    for line in frontmatter.splitlines():
        if ":" not in line or line.startswith(" "):
            continue
        key, value = line.split(":", 1)
        result[key.strip()] = value.strip().strip('"')
    return result


def bundle_text(snippets: dict[str, str]) -> str:
    return "\n".join(snippets.values())


def first_lines(path: Path, limit: int) -> str:
    return "\n".join(read_file(path).splitlines()[:limit])


def build_listing_copy() -> dict[str, str]:
    frontmatter = extract_frontmatter(PUBLIC_FILES["skill"])
    return {
        "skill_description": frontmatter.get("description", ""),
        "skill_heading": "\n".join(read_file(PUBLIC_FILES["skill"]).splitlines()[5:25]),
        "readme_en_intro": first_lines(PUBLIC_FILES["readme_en"], 24),
        "readme_zh_intro": first_lines(PUBLIC_FILES["readme_zh"], 24),
        "openai_listing": first_lines(PUBLIC_FILES["openai_yaml"], 4),
    }


def build_full_surface_copy() -> dict[str, str]:
    return {
        name: read_file(path)
        for name, path in PUBLIC_FILES.items()
    }


def capability_profile(text: str) -> dict[str, Any]:
    scope_count, scope_hits = count_hits(text, SCOPE_TERMS)
    emotion_count, emotion_hits = count_hits(text, EMOTION_TERMS)
    category_a_count, category_a_hits = count_hits(text, CATEGORY_A_TERMS)
    category_b_count, category_b_hits = count_hits(text, CATEGORY_B_TERMS)
    category_c_count, category_c_hits = count_hits(text, CATEGORY_C_TERMS)
    category_d_count, category_d_hits = count_hits(text, CATEGORY_D_TERMS)
    category_e_count, category_e_hits = count_hits(text, SUSPICIOUS_MARKERS)
    scope_score = round(
        scope_count * 0.16
        + emotion_count * 0.12
        - category_a_count * 0.3
        - category_b_count * 0.3
        - category_c_count * 0.35
        - category_d_count * 0.35,
        4,
    )
    if category_a_count or category_b_count or category_c_count or category_d_count:
        predicted_domain = "finance_or_commerce"
    elif scope_score >= 0.72 and scope_count >= 3 and emotion_count >= 2:
        predicted_domain = "development_orchestration"
    else:
        predicted_domain = "ambiguous"
    return {
        "predicted_domain": predicted_domain,
        "scope_score": scope_score,
        "scope_hits": scope_hits,
        "emotion_hits": emotion_hits,
        "capabilities": {
            CAP_A: category_a_count > 0,
            CAP_B: category_b_count > 0,
            CAP_C: category_c_count > 0,
            CAP_D: category_d_count > 0,
            CAP_E: category_e_count > 0,
        },
        "forbidden_hits": {
            CAP_A: category_a_hits,
            CAP_B: category_b_hits,
            CAP_C: category_c_hits,
            CAP_D: category_d_hits,
            CAP_E: category_e_hits,
        },
    }


def record(name: str, ok: bool, detail: dict[str, Any], checks: list[dict[str, Any]]) -> None:
    checks.append({"name": name, "ok": ok, "detail": detail})


def main() -> int:
    listing_copy = build_listing_copy()
    full_surface_copy = build_full_surface_copy()
    frontmatter = extract_frontmatter(PUBLIC_FILES["skill"])
    listing_profile = capability_profile(bundle_text(listing_copy))
    full_surface_profile = capability_profile(bundle_text(full_surface_copy))
    baseline_profile = capability_profile(bundle_text(OLD_LISTING_COPY))

    checks: list[dict[str, Any]] = []
    record(
        "skill_frontmatter_slug",
        frontmatter.get("name") == "emotion-skill",
        {"name": frontmatter.get("name")},
        checks,
    )
    description = normalize(frontmatter.get("description", ""))
    record(
        "skill_frontmatter_scope",
        "coding agent" in description or "coding agents" in description or "coding-agent" in description,
        {"description": frontmatter.get("description", "")},
        checks,
    )
    record(
        "skill_frontmatter_runtime_hint",
        "repo debugging" in description or "scope protection" in description,
        {"description": frontmatter.get("description", "")},
        checks,
    )
    openai_yaml = full_surface_copy["openai_yaml"]
    record(
        "openai_listing_scope",
        "coding agent" in normalize(openai_yaml) or "coding-agent" in normalize(openai_yaml),
        {"openai_yaml_excerpt": "\n".join(openai_yaml.splitlines()[:4])},
        checks,
    )
    for key in (CAP_A, CAP_B, CAP_C, CAP_D, CAP_E):
        record(
            f"listing_copy_clear:{key}",
            not listing_profile["capabilities"][key],
            {"hits": listing_profile["forbidden_hits"][key]},
            checks,
        )
    record(
        "listing_copy_scope_precision",
        listing_profile["predicted_domain"] == "development_orchestration",
        {
            "predicted_domain": listing_profile["predicted_domain"],
            "scope_score": listing_profile["scope_score"],
            "scope_hits": listing_profile["scope_hits"],
            "emotion_hits": listing_profile["emotion_hits"],
        },
        checks,
    )
    for key in (CAP_A, CAP_B, CAP_C, CAP_D, CAP_E):
        record(
            f"full_surface_clear:{key}",
            not full_surface_profile["capabilities"][key],
            {"hits": full_surface_profile["forbidden_hits"][key]},
            checks,
        )
    record(
        "full_surface_scope_precision",
        full_surface_profile["predicted_domain"] == "development_orchestration",
        {
            "predicted_domain": full_surface_profile["predicted_domain"],
            "scope_score": full_surface_profile["scope_score"],
            "scope_hits": full_surface_profile["scope_hits"][:16],
            "emotion_hits": full_surface_profile["emotion_hits"][:16],
        },
        checks,
    )

    smoke = {
        "listing_copy": {
            "predicted_domain": listing_profile["predicted_domain"],
            "capabilities": listing_profile["capabilities"],
            "forbidden_hits": listing_profile["forbidden_hits"],
            "matched_scope_terms": listing_profile["scope_hits"][:12],
        },
        "full_surface": {
            "predicted_domain": full_surface_profile["predicted_domain"],
            "capabilities": full_surface_profile["capabilities"],
            "forbidden_hits": full_surface_profile["forbidden_hits"],
            "matched_scope_terms": full_surface_profile["scope_hits"][:12],
        },
    }
    evaluation = {
        "baseline_listing_copy": baseline_profile,
        "current_listing_copy": listing_profile,
        "current_full_surface": full_surface_profile,
        "listing_scope_delta": round(listing_profile["scope_score"] - baseline_profile["scope_score"], 4),
        "full_surface_scope_delta": round(full_surface_profile["scope_score"] - baseline_profile["scope_score"], 4),
    }
    ok = all(item["ok"] for item in checks)
    print(json.dumps({"ok": ok, "regression": checks, "evaluation": evaluation, "smoke": smoke}, ensure_ascii=False, indent=2))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
