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
}

OLD_LISTING_COPY = {
    "short_description": "让 Agent 读空气，自己切工作模式",
    "default_prompt": "Use $emotion-skill to detect the user's emotional state and latent stance, render a dynamic emotion overlay, and quietly switch the agent into the right work mode.",
}

SCOPE_TERMS = {
    "coding agent", "coding-agent", "repo debugging", "repo", "routing", "orchestration", "verification depth",
    "thread priority", "guard behavior", "guard mode", "scope protection", "scope control", "queue priority",
    "reply style", "post-success", "stabilization", "debugging", "编排", "路由", "验证强度", "线程优先级",
    "收口策略", "代码工作流", "coding-task", "coding agents",
}
EMOTION_TERMS = {
    "emotion", "emotion-aware", "urgency", "frustration", "skepticism", "confusion", "caution", "satisfaction",
    "情绪", "怀疑", "谨慎", "困惑", "收口", "紧急", "挫败",
}
CRYPTO_TERMS = {
    "crypto", "cryptocurrency", "wallet", "bitcoin", "ethereum", "solana", "usdc", "usdt", "erc20", "token", "swap",
    "nft", "链上", "钱包", "加密货币", "代币",
}
PURCHASE_TERMS = {
    "purchase", "purchases", "buy", "checkout", "shop", "shopping", "order", "cart", "payment", "payments",
    "spend", "gift", "merchant", "storefront", "下单", "购买", "支付", "付款", "购物", "商城",
}


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


def capability_profile(text: str) -> dict[str, Any]:
    scope_count, scope_hits = count_hits(text, SCOPE_TERMS)
    emotion_count, emotion_hits = count_hits(text, EMOTION_TERMS)
    crypto_count, crypto_hits = count_hits(text, CRYPTO_TERMS)
    purchase_count, purchase_hits = count_hits(text, PURCHASE_TERMS)
    scope_score = round(scope_count * 0.16 + emotion_count * 0.12 - crypto_count * 0.3 - purchase_count * 0.3, 4)
    if crypto_count or purchase_count:
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
            "crypto": crypto_count > 0,
            "can_make_purchases": purchase_count > 0,
        },
        "forbidden_hits": {
            "crypto": crypto_hits,
            "can_make_purchases": purchase_hits,
        },
    }


def record(name: str, ok: bool, detail: dict[str, Any], checks: list[dict[str, Any]]) -> None:
    checks.append({"name": name, "ok": ok, "detail": detail})


def main() -> int:
    raw_public_copy = {name: read_file(path) for name, path in PUBLIC_FILES.items()}
    public_copy = build_listing_copy()
    frontmatter = extract_frontmatter(PUBLIC_FILES["skill"])
    current_profile = capability_profile(bundle_text(public_copy))
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
    openai_yaml = raw_public_copy["openai_yaml"]
    record(
        "openai_listing_scope",
        "coding agent" in normalize(openai_yaml) or "coding-agent" in normalize(openai_yaml),
        {"openai_yaml_excerpt": "\n".join(openai_yaml.splitlines()[:4])},
        checks,
    )
    record(
        "public_copy_no_crypto",
        not current_profile["capabilities"]["crypto"],
        {"hits": current_profile["forbidden_hits"]["crypto"]},
        checks,
    )
    record(
        "public_copy_no_purchase",
        not current_profile["capabilities"]["can_make_purchases"],
        {"hits": current_profile["forbidden_hits"]["can_make_purchases"]},
        checks,
    )
    record(
        "public_copy_scope_precision",
        current_profile["predicted_domain"] == "development_orchestration",
        {
            "predicted_domain": current_profile["predicted_domain"],
            "scope_score": current_profile["scope_score"],
            "scope_hits": current_profile["scope_hits"],
            "emotion_hits": current_profile["emotion_hits"],
        },
        checks,
    )

    smoke = {
        "predicted_domain": current_profile["predicted_domain"],
        "capabilities": current_profile["capabilities"],
        "forbidden_hits": current_profile["forbidden_hits"],
        "matched_scope_terms": current_profile["scope_hits"][:12],
    }
    evaluation = {
        "baseline_listing_copy": baseline_profile,
        "current_public_copy": current_profile,
        "scope_precision_delta": round(current_profile["scope_score"] - baseline_profile["scope_score"], 4),
    }
    ok = all(item["ok"] for item in checks) and smoke["predicted_domain"] == "development_orchestration"
    print(json.dumps({"ok": ok, "regression": checks, "evaluation": evaluation, "smoke": smoke}, ensure_ascii=False, indent=2))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
