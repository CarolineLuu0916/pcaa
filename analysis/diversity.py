"""Behavioral Diversity（CLAUDE.md §4.2）：Shannon Entropy over 行为分布。

陷阱（CLAUDE.md 原话）："Persona Lock 不应该导致所有 Agent 行为雷同"——
所以这里既要看单个 persona 内部跨场景/轮次的行为熵，预期 experimental
不应显著低于 baseline。
"""
from __future__ import annotations

import math
from collections import Counter

from common import group_by_persona_condition, load_records


def shannon_entropy(labels: list[str]) -> float:
    if not labels:
        return 0.0
    counts = Counter(labels)
    total = len(labels)
    return -sum((c / total) * math.log2(c / total) for c in counts.values())


def diversity_by_persona(jsonl_path: str) -> dict[str, dict[str, float]]:
    _, records = load_records(jsonl_path)
    grouped = group_by_persona_condition(records)

    result: dict[str, dict[str, float]] = {}
    for persona_id, by_condition in grouped.items():
        result[persona_id] = {
            condition: shannon_entropy([r["action_id"] for r in recs])
            for condition, recs in by_condition.items()
        }
    return result


if __name__ == "__main__":
    import json
    import sys

    path = sys.argv[1] if len(sys.argv) > 1 else "results/mvp_run.jsonl"
    print(json.dumps(diversity_by_persona(path), ensure_ascii=False, indent=2))
