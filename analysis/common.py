"""分析脚本共用的小工具：加载 JSONL 结果、余弦相似度、按 persona/condition 分组。"""
from __future__ import annotations

import json
import math
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from persona import TRAIT_ORDER  # noqa: E402


def load_records(jsonl_path: str | Path) -> tuple[dict, list[dict]]:
    """返回 (run_meta, records)。run_meta 是第一行 type=="run_meta" 的记录。"""
    run_meta: dict = {}
    records: list[dict] = []
    with open(jsonl_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            if row.get("type") == "run_meta":
                run_meta = row
            else:
                records.append(row)
    return run_meta, records


def group_by_persona_condition(records: list[dict]) -> dict[str, dict[str, list[dict]]]:
    grouped: dict[str, dict[str, list[dict]]] = defaultdict(lambda: defaultdict(list))
    for r in records:
        grouped[r["persona_id"]][r["condition"]].append(r)
    return grouped


def cosine_similarity(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def trait_signal_to_vector(trait_signal: dict[str, float]) -> list[float]:
    return [trait_signal[k] for k in TRAIT_ORDER]
