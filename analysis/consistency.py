"""Persona Consistency（CLAUDE.md §4.1）：

cosine_similarity(trait_signal_of_chosen_action, initial_persona_vector)，
按 meta_round_index 取平均（同一轮内可能跨多个场景），得到长度 = rounds 的曲线。
LLM-as-a-Judge 的 1-5 打分见 judge.score_persona_consistency，是这里的独立验证，
不参与这条曲线的计算（避免循环依赖同一个评分来源）。
"""
from __future__ import annotations

from collections import defaultdict

from common import cosine_similarity, group_by_persona_condition, load_records, trait_signal_to_vector


def consistency_series(records: list[dict], rounds: int) -> list[float]:
    """records 必须属于同一个 persona + condition。按 meta_round_index 平均。"""
    buckets: dict[int, list[float]] = defaultdict(list)
    for r in records:
        vec = trait_signal_to_vector(r["trait_signal"])
        sim = cosine_similarity(vec, r["persona_vector_initial"])
        buckets[r["meta_round_index"]].append(sim)
    return [
        sum(buckets[i]) / len(buckets[i]) if buckets.get(i) else 0.0
        for i in range(rounds)
    ]


def consistency_by_persona(jsonl_path: str) -> dict[str, dict[str, list[float]]]:
    run_meta, records = load_records(jsonl_path)
    rounds = run_meta.get("rounds_per_scenario", 10)
    grouped = group_by_persona_condition(records)

    result: dict[str, dict[str, list[float]]] = {}
    for persona_id, by_condition in grouped.items():
        result[persona_id] = {
            condition: consistency_series(recs, rounds)
            for condition, recs in by_condition.items()
        }
    return result


if __name__ == "__main__":
    import json
    import sys

    path = sys.argv[1] if len(sys.argv) > 1 else "results/mvp_run.jsonl"
    print(json.dumps(consistency_by_persona(path), ensure_ascii=False, indent=2))
