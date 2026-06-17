"""离线验证整条 MVP pipeline（没有 DEEPSEEK_API_KEY / OPENAI_API_KEY 时使用）。

用 tests/mock_llm.py 的 MockOpenAIClient 替代真实 API，跑一遍小规模的
agent/baseline 循环 -> 写 JSONL -> consistency/diversity 分析 -> mock 版
social realism -> export_dashboard_data，确认每一步的数据结构和字段名
都对得上，不会等真的有 API key 跑正式实验时才发现 bug。

跑法：python tests/test_pipeline_offline.py
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "analysis"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from agent import run_experimental_agent  # noqa: E402
from baseline import run_baseline_agent  # noqa: E402
from environment import load_scenarios  # noqa: E402
from judge import compare_social_realism, score_persona_consistency  # noqa: E402
from mock_llm import MockOpenAIClient  # noqa: E402
from persona import load_personas  # noqa: E402

import consistency as consistency_mod  # noqa: E402
import diversity as diversity_mod  # noqa: E402
import export_dashboard_data  # noqa: E402

ROUNDS_PER_SCENARIO = 2  # 离线验证只需要跑通逻辑，轮次拉小一点更快


def run_mock_mvp() -> Path:
    personas = load_personas(str(ROOT / "config" / "personas.json"))
    scenarios = load_scenarios(str(ROOT / "config" / "scenarios.json"))
    total_timesteps = ROUNDS_PER_SCENARIO * len(scenarios)
    client = MockOpenAIClient(seed=1)

    output_path = ROOT / "results" / "mvp_run_mock.jsonl"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    run_meta = {
        "type": "run_meta",
        "seed": 1,
        "rounds_per_scenario": ROUNDS_PER_SCENARIO,
        "num_scenarios": len(scenarios),
        "total_timesteps_per_agent": total_timesteps,
        "num_personas": len(personas),
        "drift_rate": 0.05,
        "mock": True,
    }

    written = 0
    with output_path.open("w", encoding="utf-8") as f:
        f.write(json.dumps(run_meta, ensure_ascii=False) + "\n")
        for persona in personas:
            exp_records = run_experimental_agent(persona, scenarios, rounds=total_timesteps, client=client)
            base_records = run_baseline_agent(persona, scenarios, rounds=total_timesteps, client=client)
            for r in exp_records + base_records:
                f.write(json.dumps(r.to_dict(), ensure_ascii=False) + "\n")
                written += 1

    expected = len(personas) * 2 * total_timesteps
    assert written == expected, f"期望写入 {expected} 条记录，实际 {written}"
    print(f"[1/5] mock MVP 跑通：{written} 条 agent-round 写入 {output_path.name}")
    return output_path


def run_mock_analysis(jsonl_path: Path) -> None:
    consistency = consistency_mod.consistency_by_persona(str(jsonl_path))
    diversity = diversity_mod.diversity_by_persona(str(jsonl_path))

    for persona_id, by_condition in consistency.items():
        for condition, series in by_condition.items():
            assert len(series) == ROUNDS_PER_SCENARIO, (
                f"{persona_id}/{condition} consistency 长度应为 {ROUNDS_PER_SCENARIO}，实际 {len(series)}"
            )
            for v in series:
                assert -1.0001 <= v <= 1.0001, f"cosine similarity 超出范围：{v}"

    for persona_id, by_condition in diversity.items():
        for condition, entropy in by_condition.items():
            assert entropy >= 0, f"entropy 不应为负：{entropy}"

    print(f"[2/5] consistency/diversity 分析跑通：{len(consistency)} 个 persona")


def run_mock_judge() -> None:
    client = MockOpenAIClient(seed=2)
    demo_records = [
        {"round_index": 0, "scenario_name": "日常一天", "action_label": "在家省钱度过",
         "behavior": "在家做饭", "mood": "neutral"},
    ]
    score_result = score_persona_consistency(client, "你是一个节俭的人。", demo_records, model="mock-model")
    assert 1 <= score_result["score"] <= 5, f"score 超出 1-5：{score_result}"

    ab_result = compare_social_realism(
        client, demo_records, demo_records, label_a="experimental", label_b="baseline", model="mock-model",
    )
    assert ab_result["winner_label"] in ("experimental", "baseline", "tie")
    print("[3/5] judge.py（consistency 打分 + social realism A/B）跑通")


def run_mock_social_realism_export(jsonl_path: Path) -> Path:
    social_path = ROOT / "results" / "social_realism_mock.json"
    fake_summary = {
        "experimental_win": 50, "baseline_win": 30, "tie": 20, "num_comparisons": 6, "detail": [],
    }
    social_path.write_text(json.dumps(fake_summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[4/5] mock social realism 汇总写入 {social_path.name}")
    return social_path


def run_mock_export(jsonl_path: Path, social_path: Path) -> None:
    output_path = ROOT / "results" / "dashboard-data.mock.js"
    export_dashboard_data.export(
        input_path=str(jsonl_path),
        social_path=str(social_path),
        output_path=str(output_path),
        personas_path=str(ROOT / "config" / "personas.json"),
    )

    raw = output_path.read_text(encoding="utf-8")
    match = re.search(r"window\.PCAA_DATA = (\{.*\});", raw, re.DOTALL)
    assert match, "导出的 JS 里找不到 window.PCAA_DATA = {...};"
    data = json.loads(match.group(1))

    assert data["demo"] is False
    assert data["rounds"] == ROUNDS_PER_SCENARIO
    assert len(data["personas"]) == 3
    assert set(data["consistency"].keys()) == {p["id"] for p in data["personas"]}
    assert data["socialRealism"]["experimental_win"] == 50
    assert len(data["sampleRows"]) > 0
    print(f"[5/5] export_dashboard_data 跑通，结构校验通过 -> {output_path.name}")


def main() -> None:
    jsonl_path = run_mock_mvp()
    run_mock_analysis(jsonl_path)
    run_mock_judge()
    social_path = run_mock_social_realism_export(jsonl_path)
    run_mock_export(jsonl_path, social_path)
    print("\n离线管线验证全部通过（不代表真实 LLM 输出质量，只代表代码逻辑/数据结构正确）。")


if __name__ == "__main__":
    main()
