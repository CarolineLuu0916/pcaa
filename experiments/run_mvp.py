"""MVP 实验编排：3 persona × 2 条件 × 5 场景 × 10 轮 = 300 agent-round。

"10 轮"对应 CLAUDE.md 3.1 表格里的"模拟轮次"，每一轮内会依次经历全部
5 个场景模板，因此每个 agent 实际跑 10 * 5 = 50 个 timestep；
3 persona * 2 条件 = 6 个 agent，6 * 50 = 300，与 CLAUDE.md 的总 agent-round
对齐。round_index 是 0-based 的全局 timestep，meta_round_index = round_index
// 5 对应"第几轮"。

输出：results/mvp_run.jsonl，每行一个 agent-round（可直接喂给 analysis/）。
"""
from __future__ import annotations

import argparse
import json
import random
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from agent import run_experimental_agent  # noqa: E402
from baseline import run_baseline_agent  # noqa: E402
from baseline_ga import run_ga_baseline_agent  # noqa: E402
from experimental_ga import run_experimental_ga_agent  # noqa: E402
from experimental_anchor import run_experimental_anchor_agent  # noqa: E402
from experimental_pga import run_experimental_pga_agent  # noqa: E402
from environment import load_scenarios  # noqa: E402
from llm_client import make_deepseek_client  # noqa: E402
from persona import load_personas  # noqa: E402

ROUNDS_PER_SCENARIO_DEFAULT = 10

# baseline_ga（更贴近 Generative Agents 的记忆架构：retrieval + reflection + planning）
# 默认不跑，因为每个 timestep 比 experimental/baseline 多花 2-3 倍 LLM 调用——
# 用 --conditions experimental,baseline_ga 显式加进来。
CONDITION_RUNNERS = {
    "experimental": lambda persona, scenarios, rounds, client, args: run_experimental_agent(
        persona, scenarios, rounds=rounds, client=client, drift_rate=args.drift_rate,
        nudge_seed=args.nudge_seed,
    ),
    "baseline": lambda persona, scenarios, rounds, client, args: run_baseline_agent(
        persona, scenarios, rounds=rounds, client=client,
        nudge_seed=args.nudge_seed,
    ),
    "baseline_ga": lambda persona, scenarios, rounds, client, args: run_ga_baseline_agent(
        persona, scenarios, rounds=rounds, client=client,
    ),
    "experimental_ga": lambda persona, scenarios, rounds, client, args: run_experimental_ga_agent(
        persona, scenarios, rounds=rounds, client=client, drift_rate=args.drift_rate,
    ),
    "experimental_anchor": lambda persona, scenarios, rounds, client, args: run_experimental_anchor_agent(
        persona, scenarios, rounds=rounds, client=client, drift_rate=args.drift_rate,
        nudge_seed=args.nudge_seed,
    ),
    "experimental_pga": lambda persona, scenarios, rounds, client, args: run_experimental_pga_agent(
        persona, scenarios, rounds=rounds, client=client, drift_rate=args.drift_rate,
    ),
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="跑 PCAA MVP 实验")
    parser.add_argument("--personas-path", default=str(ROOT / "config" / "personas.json"))
    parser.add_argument("--scenarios-path", default=str(ROOT / "config" / "scenarios.json"))
    parser.add_argument("--output", default=str(ROOT / "results" / "mvp_run.jsonl"))
    parser.add_argument("--rounds-per-scenario", type=int, default=ROUNDS_PER_SCENARIO_DEFAULT)
    parser.add_argument("--drift-rate", type=float, default=0.05)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--nudge-seed", dest="nudge_seed", type=int, default=None,
                        help="每轮情境扰动的随机种子，None=每次运行不同，整数=可复现")
    parser.add_argument(
        "--conditions", default="experimental,baseline",
        help="逗号分隔，可选 experimental,baseline,baseline_ga,experimental_ga",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    random.seed(args.seed)

    personas = load_personas(args.personas_path)
    scenarios = load_scenarios(args.scenarios_path)
    total_timesteps = args.rounds_per_scenario * len(scenarios)
    conditions = [c.strip() for c in args.conditions.split(",") if c.strip()]
    for c in conditions:
        if c not in CONDITION_RUNNERS:
            raise SystemExit(f"未知 condition={c!r}，可选：{list(CONDITION_RUNNERS)}")

    client = make_deepseek_client()

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    run_meta = {
        "type": "run_meta",
        "seed": args.seed,
        "rounds_per_scenario": args.rounds_per_scenario,
        "num_scenarios": len(scenarios),
        "total_timesteps_per_agent": total_timesteps,
        "num_personas": len(personas),
        "drift_rate": args.drift_rate,
        "conditions": conditions,
        "started_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
    }

    written = 0
    with output_path.open("w", encoding="utf-8") as f:
        f.write(json.dumps(run_meta, ensure_ascii=False) + "\n")

        for persona in personas:
            for condition in conditions:
                print(f"[{condition}] persona={persona.id} 开始 {total_timesteps} 个 timestep ...")
                records = CONDITION_RUNNERS[condition](persona, scenarios, total_timesteps, client, args)
                for r in records:
                    f.write(json.dumps(r.to_dict(), ensure_ascii=False) + "\n")
                    written += 1

    print(f"完成，共写入 {written} 条 agent-round 记录到 {output_path}")


if __name__ == "__main__":
    main()
