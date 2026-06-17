"""Social Realism（CLAUDE.md §4.3）：盲测 A/B，"哪一段更像真实人类"。

每个 persona 抽样若干个 meta_round 的窗口，对比同一窗口 experimental vs
baseline 的行为轨迹文本（judge 看不到 condition 标签，呈现顺序随机打乱），
汇总成 experimental_win / baseline_win / tie 的百分比，结构对应
site/js/dashboard-data.js 的 socialRealism 字段。

需要 OPENAI_API_KEY（GPT-4o）或 MOONSHOT_API_KEY（Kimi）之一——见
llm_client.make_judge_client()，是本项目里唯一不调用 DeepSeek 的脚本。
"""
from __future__ import annotations

import json
import random
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from common import group_by_persona_condition, load_records  # noqa: E402
from judge import compare_social_realism  # noqa: E402
from llm_client import make_deepseek_judge_client, make_judge_client  # noqa: E402


def sample_windows(records: list[dict], window_size: int, num_samples: int, rng: random.Random) -> list[list[dict]]:
    """把 records 按 meta_round_index 分组，随机抽 num_samples 个长度为 window_size 的连续窗口。"""
    by_round: dict[int, list[dict]] = defaultdict(list)
    for r in records:
        by_round[r["meta_round_index"]].append(r)
    sorted_rounds = sorted(by_round)
    if len(sorted_rounds) <= window_size:
        return [records] if records else []

    starts = list(range(0, len(sorted_rounds) - window_size + 1))
    rng.shuffle(starts)
    windows = []
    for start in starts[:num_samples]:
        chosen_rounds = sorted_rounds[start:start + window_size]
        window_records = [r for rd in chosen_rounds for r in by_round[rd]]
        windows.append(window_records)
    return windows


def run_social_realism(
    jsonl_path: str,
    window_size: int = 3,
    num_samples: int = 3,
    seed: int = 42,
    condition_a: str = "experimental",
    condition_b: str = "baseline",
    judge: str = "kimi",
) -> dict:
    """condition_a/condition_b 默认是 experimental/baseline，也可以传 baseline_ga
    之类的第三个条件——比如 condition_b="baseline_ga" 用来检验 PCAA 相对一个更
    贴近 Generative Agents 记忆架构的对照组，胜率是否还站得住。"""
    run_meta, records = load_records(jsonl_path)
    grouped = group_by_persona_condition(records)
    rng = random.Random(seed)
    client, model = make_deepseek_judge_client() if judge == "deepseek" else make_judge_client()

    tally = Counter()
    detail = []

    for persona_id, by_condition in grouped.items():
        a_records = by_condition.get(condition_a, [])
        b_records = by_condition.get(condition_b, [])
        a_windows = sample_windows(a_records, window_size, num_samples, rng)
        b_windows = sample_windows(b_records, window_size, num_samples, rng)

        for a_w, b_w in zip(a_windows, b_windows):
            result = compare_social_realism(
                client, a_w, b_w, label_a=condition_a, label_b=condition_b, model=model, rng=rng,
            )
            tally[result["winner_label"]] += 1
            detail.append({"persona_id": persona_id, **result})

    total = sum(tally.values()) or 1
    summary = {
        "experimental_win": round(100 * tally.get(condition_a, 0) / total),
        "baseline_win": round(100 * tally.get(condition_b, 0) / total),
        "tie": round(100 * tally.get("tie", 0) / total),
        "num_comparisons": total,
        "condition_a": condition_a,
        "condition_b": condition_b,
        "detail": detail,
    }
    return summary


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("input", nargs="?", default="results/mvp_run.jsonl")
    parser.add_argument("output", nargs="?", default="results/social_realism.json")
    parser.add_argument("condition_a", nargs="?", default="experimental")
    parser.add_argument("condition_b", nargs="?", default="baseline")
    parser.add_argument("--judge", default="kimi", choices=["kimi", "deepseek"],
                        help="judge 模型：kimi（moonshot-v1-8k）或 deepseek（deepseek-chat）")
    args = parser.parse_args()
    summary = run_social_realism(
        args.input, condition_a=args.condition_a, condition_b=args.condition_b, judge=args.judge,
    )
    Path(args.output).write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"写入 {args.output}：{summary['experimental_win']}% / {summary['baseline_win']}% / {summary['tie']}%")
