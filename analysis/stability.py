"""Long-term Stability（CLAUDE.md §4.4）：滚动窗口 cosine similarity。

跟 consistency.py 不一样的地方：这里比较的是相邻两个滚动窗口的平均行为向量
（trait_signal），而不是某一轮 vs round 0 的"初始人格数值"。这样设计是为了
不把 PCAA 自己允许的"慢漂移"（95% 继承 + 5% 漂移）误判成"不稳定"——只要
相邻窗口之间变化是平滑的，分数就该高；只有窗口与窗口之间发生突变（某一段
时间人格突然崩塌/写崩了）才会被这个指标抓到，对应 CLAUDE.md 4.4 的验证目标
"观察人格是否在后期崩塌"。
"""
from __future__ import annotations

from collections import defaultdict

from common import cosine_similarity, group_by_persona_condition, load_records, trait_signal_to_vector
from persona import TRAIT_ORDER


def _chunk_avg_vectors(records: list[dict], rounds: int, chunk_size: int) -> list[list[float]]:
    """把 rounds 切成不重叠的连续段（最后不足一段的尾巴丢弃），每段取平均行为向量。

    用不重叠的分段而不是逐步滑动的窗口，是因为如果窗口长度跟总轮数同一个量级，
    相邻滑动窗口会共享几乎全部数据，cosine similarity 永远逼近 1，把真实的漂移/
    突变信号磨平了——分段窗口能让相邻两段尽量不共享数据，对变化更敏感。
    """
    buckets: dict[int, list[list[float]]] = defaultdict(list)
    for r in records:
        buckets[r["meta_round_index"]].append(trait_signal_to_vector(r["trait_signal"]))

    dim = len(TRAIT_ORDER)
    per_round_avg = []
    for i in range(rounds):
        vecs = buckets.get(i, [])
        if not vecs:
            per_round_avg.append([0.0] * dim)
        else:
            per_round_avg.append([sum(v[k] for v in vecs) / len(vecs) for k in range(dim)])

    num_chunks = rounds // chunk_size
    chunks = []
    for c in range(num_chunks):
        start = c * chunk_size
        chunk = per_round_avg[start:start + chunk_size]
        chunks.append([sum(v[k] for v in chunk) / len(chunk) for k in range(dim)])
    return chunks


def rolling_stability_series(records: list[dict], rounds: int, window: int) -> list[float]:
    """长度 = num_chunks - 1 的序列：第 i 个值 = 第 i 段和第 i+1 段的平均行为向量之间
    的 cosine similarity。越接近 1 越稳定；某一处骤降代表那个时间点附近发生了行为突变。
    """
    chunks = _chunk_avg_vectors(records, rounds, window)
    return [
        cosine_similarity(chunks[i], chunks[i + 1])
        for i in range(len(chunks) - 1)
    ]


def stability_by_persona(jsonl_path: str, window: int | None = None) -> dict[str, dict]:
    run_meta, records = load_records(jsonl_path)
    rounds = run_meta.get("rounds_per_scenario", 10)
    if window is None:
        window = min(10, max(2, rounds // 4))
    grouped = group_by_persona_condition(records)

    result: dict[str, dict] = {}
    for persona_id, by_condition in grouped.items():
        result[persona_id] = {"window": window}
        for condition, recs in by_condition.items():
            series = rolling_stability_series(recs, rounds, window)
            result[persona_id][condition] = {
                "series": series,
                "mean": sum(series) / len(series) if series else None,
                "min": min(series) if series else None,
            }
    return result


if __name__ == "__main__":
    import json
    import sys

    path = sys.argv[1] if len(sys.argv) > 1 else "results/mvp_run.jsonl"
    print(json.dumps(stability_by_persona(path), ensure_ascii=False, indent=2))
