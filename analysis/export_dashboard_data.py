"""把 results/mvp_run.jsonl（+ 可选 results/social_realism.json）聚合成
site/js/dashboard-data.js 期望的结构，直接覆盖那个文件。dashboard.js 不需要改动。

用法：
    python analysis/export_dashboard_data.py
    python analysis/export_dashboard_data.py --input results/mvp_run.jsonl --social results/social_realism.json
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from common import group_by_persona_condition, load_records  # noqa: E402
from consistency import consistency_series  # noqa: E402
from diversity import shannon_entropy  # noqa: E402
from persona import TRAIT_ORDER, load_personas  # noqa: E402

PERSONA_COLORS = {
    "frugal_introvert": "#5B4FE5",
    "open_social": "#1F8A70",
    "cautious_stable": "#C97B1E",
    "impulsive_hedonist": "#C2434A",
    "ambitious_achiever": "#3E6FB0",
    "easygoing_drifter": "#7E5BAD",
}
FALLBACK_COLORS = ["#5B4FE5", "#1F8A70", "#C97B1E", "#C2434A", "#3E6FB0", "#7E5BAD"]


def vector_to_traits(vec: list[float]) -> dict:
    return {k: vec[i] for i, k in enumerate(TRAIT_ORDER)}


def build_sample_rows(grouped: dict, personas: list, num_scenarios: int, rounds: int) -> list[dict]:
    target_meta_round = rounds // 2
    rows = []
    for idx, persona in enumerate(personas):
        by_condition = grouped.get(persona.id, {})
        target_timestep = target_meta_round * num_scenarios + (idx % num_scenarios)
        for condition in ("experimental", "baseline"):
            recs = by_condition.get(condition, [])
            match = next((r for r in recs if r["round_index"] == target_timestep), None)
            if match is None and recs:
                match = recs[len(recs) // 2]
            if match is None:
                continue
            rows.append({
                "persona": persona.name,
                "condition": condition,
                "round": match["meta_round_index"],
                "scenario": match["scenario_name"],
                "action": match["behavior"] or match["action_label"],
                "mood": match["mood"],
                "wealth": round(match["soft_state"]["wealth"]),
            })
    return rows


def build_rounds_comparison(personas: list, *runs: tuple[str, str, str]) -> list[dict]:
    """runs: 每个元素是 (label, input_jsonl_path, social_json_path)。

    用来对比"同样的代码、不同的轮次设置"得到的 social realism 胜率——
    验证 PCAA 的优势是否需要更长的时间跨度才能充分显现（参见对话里
    10 轮 vs 20 轮的发现）。缺文件就跳过那个轮次，不报错。
    """
    persona_names = {p.id: p.name for p in personas}
    comparison = []
    for label, input_path, social_path in runs:
        if not Path(input_path).exists() or not Path(social_path).exists():
            continue
        run_meta, _ = load_records(input_path)
        social = json.loads(Path(social_path).read_text(encoding="utf-8"))
        cond_a = social.get("condition_a", "experimental")
        cond_b = social.get("condition_b", "baseline")

        per_persona: dict[str, dict] = defaultdict(lambda: {"a": 0, "b": 0, "tie": 0, "total": 0})
        for d in social.get("detail", []):
            key = "a" if d["winner_label"] == cond_a else "b" if d["winner_label"] == cond_b else "tie"
            per_persona[d["persona_id"]][key] += 1
            per_persona[d["persona_id"]]["total"] += 1

        comparison.append({
            "label": label,
            "rounds": run_meta.get("rounds_per_scenario"),
            "conditionA": cond_a,
            "conditionB": cond_b,
            "experimental_win": social["experimental_win"],
            "baseline_win": social["baseline_win"],
            "tie": social["tie"],
            "perPersona": [
                {
                    "personaId": pid,
                    "personaName": persona_names.get(pid, pid),
                    "experimentalWin": v["a"],
                    "baselineWin": v["b"],
                    "tie": v["tie"],
                    "total": v["total"],
                }
                for pid, v in per_persona.items()
            ],
        })
    return comparison


def export(input_path: str, social_path: str | None, output_path: str, personas_path: str) -> None:
    run_meta, records = load_records(input_path)
    rounds = run_meta.get("rounds_per_scenario", 10)
    num_scenarios = run_meta.get("num_scenarios", 5)
    grouped = group_by_persona_condition(records)
    personas = load_personas(personas_path)

    scenario_names = []
    seen = set()
    for r in records:
        if r["scenario_id"] not in seen:
            seen.add(r["scenario_id"])
            scenario_names.append(r["scenario_name"])

    persona_entries = []
    consistency = {}
    diversity = {}
    drift_radar = {}

    for idx, persona in enumerate(personas):
        by_condition = grouped.get(persona.id, {})
        color = PERSONA_COLORS.get(persona.id, FALLBACK_COLORS[idx % len(FALLBACK_COLORS)])
        persona_entries.append({
            "id": persona.id,
            "name": persona.name,
            "color": color,
            "traits": persona.traits,
        })

        consistency[persona.id] = {
            condition: consistency_series(recs, rounds)
            for condition, recs in by_condition.items()
        }
        diversity[persona.id] = {
            condition: shannon_entropy([r["action_id"] for r in recs])
            for condition, recs in by_condition.items()
        }

        exp_recs = by_condition.get("experimental", [])
        if exp_recs:
            final_vec = max(exp_recs, key=lambda r: r["round_index"])["persona_vector_current"]
            drift_radar[persona.id] = {
                "initial": persona.traits,
                "final": vector_to_traits(final_vec),
            }

    social_realism = {"experimental_win": None, "baseline_win": None, "tie": None}
    if social_path and Path(social_path).exists():
        social_data = json.loads(Path(social_path).read_text(encoding="utf-8"))
        social_realism = {
            "experimental_win": social_data["experimental_win"],
            "baseline_win": social_data["baseline_win"],
            "tie": social_data["tie"],
        }
    else:
        print(f"警告：未找到 {social_path}，socialRealism 字段将为 null。"
              f"先跑 analysis/social_realism.py 生成它。", file=sys.stderr)

    sample_rows = build_sample_rows(grouped, personas, num_scenarios, rounds)

    rounds_comparison = build_rounds_comparison(
        personas,
        ("3p × 10 轮 vs 文本baseline", str(ROOT / "results" / "mvp_run.jsonl"), str(ROOT / "results" / "social_realism.json")),
        ("3p × 20 轮 vs 文本baseline", str(ROOT / "results" / "mvp_run_long.jsonl"), str(ROOT / "results" / "social_realism_long.json")),
        ("3p × 10 轮 vs GA-faithful baseline", str(ROOT / "results" / "mvp_run_ga.jsonl"), str(ROOT / "results" / "social_realism_ga.json")),
        ("6p × 10 轮 (v3 修复prompt)", str(ROOT / "results" / "mvp_run_v3.jsonl"), str(ROOT / "results" / "social_realism_v3.json")),
        ("6p × 10 轮 exp_ga vs base_ga", str(ROOT / "results" / "mvp_run_combined.jsonl"), str(ROOT / "results" / "social_realism_combined.json")),
    )

    data = {
        "demo": False,
        "rounds": rounds,
        "scenarios": scenario_names,
        "personas": persona_entries,
        "consistency": consistency,
        "diversity": diversity,
        "driftRadar": drift_radar,
        "socialRealism": social_realism,
        "roundsComparison": rounds_comparison,
        "sampleRows": sample_rows,
    }

    js_content = (
        "/*\n"
        " * PCAA Dashboard — 由 analysis/export_dashboard_data.py 从 "
        f"{input_path} 自动生成，请勿手动编辑。\n"
        " * 重新生成：python analysis/export_dashboard_data.py\n"
        " */\n"
        "window.PCAA_DATA = "
        + json.dumps(data, ensure_ascii=False, indent=2)
        + ";\n"
    )
    Path(output_path).write_text(js_content, encoding="utf-8")
    print(f"已写入 {output_path}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default=str(ROOT / "results" / "mvp_run.jsonl"))
    parser.add_argument("--social", default=str(ROOT / "results" / "social_realism.json"))
    parser.add_argument("--output", default=str(ROOT / "site" / "js" / "dashboard-data.js"))
    parser.add_argument("--personas-path", default=str(ROOT / "config" / "personas.json"))
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    export(args.input, args.social, args.output, args.personas_path)
