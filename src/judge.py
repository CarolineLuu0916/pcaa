"""LLM-as-a-Judge：默认 GPT-4o，没有 OpenAI key 时回退到 Kimi（Moonshot），
temperature=0。两者都通过 llm_client.make_judge_client() 统一获取，
调用方拿到 (client, model) 后把 model 传进下面两个函数。

两个评测任务（CLAUDE.md §4.1 / §4.3）：
1. Persona Consistency 打分（1-5）—— 只给评测者人设的文字描述 + 行为轨迹，
   不告诉它这条轨迹来自实验组还是对照组（blinding）。
2. Social Realism A/B 盲测 —— 两条轨迹谁更像真实人类；内部随机打乱呈现顺序，
   避免"永远是第一条更容易被选中"的位置偏差，返回前再映射回原始标签。
"""
from __future__ import annotations

import random

from openai import OpenAI

from llm_client import chat_json


def trace_to_text(records: list[dict]) -> str:
    lines = [
        f"第{r['round_index'] + 1}轮·{r['scenario_name']}：选择了「{r['action_label']}」"
        f"（{r['behavior']}），心情{r['mood']}。"
        for r in records
    ]
    return "\n".join(lines)


def score_persona_consistency(
    client: OpenAI,
    persona_description: str,
    records: list[dict],
    model: str,
) -> dict:
    """评测者只看到文字人设描述（两组共用同一份，公平），不知道这是哪一组的轨迹。"""
    system_prompt = (
        "你是一位评测者，任务是判断一段行为轨迹是否符合给定的人物设定。"
        "你不知道也不需要知道这段轨迹是用什么方法生成的，只根据内容打分。"
    )
    user_prompt = (
        f"人物设定：\n{persona_description}\n\n"
        f"行为轨迹：\n{trace_to_text(records)}\n\n"
        "请判断这段行为轨迹与人物设定的符合程度，打分 1-5（5=高度符合，1=完全不符合）。"
        '只返回 JSON：{"score": <1-5整数>, "reason": "<一句话理由>"}'
    )
    return chat_json(client, system_prompt, user_prompt, model=model, temperature=0)


def compare_social_realism(
    client: OpenAI,
    trace_a: list[dict],
    trace_b: list[dict],
    label_a: str,
    label_b: str,
    model: str,
    rng: random.Random | None = None,
) -> dict:
    """盲测两条轨迹哪个更像真实人类；随机打乱呈现顺序，返回时映射回原始 label。

    label_a / label_b 通常是 "experimental" / "baseline"，仅用于调用方记录结果，
    不会出现在送给模型的 prompt 里。
    """
    rng = rng or random
    traces = [(label_a, trace_a), (label_b, trace_b)]
    if rng.random() < 0.5:
        traces = [traces[1], traces[0]]
    (first_label, first_trace), (second_label, second_trace) = traces

    system_prompt = (
        "你是一位评测者，任务是比较两段行为轨迹，判断哪一段更像真实人类的行为模式"
        "（更自然、更有人格连贯性，而不是生硬或前后矛盾）。你不知道这两段轨迹是怎么生成的。"
    )
    user_prompt = (
        f"轨迹 A：\n{trace_to_text(first_trace)}\n\n"
        f"轨迹 B：\n{trace_to_text(second_trace)}\n\n"
        '请只返回 JSON：{"winner": "A" 或 "B" 或 "tie", "reason": "<一句话理由>"}'
    )
    result = chat_json(client, system_prompt, user_prompt, model=model, temperature=0)

    winner_slot = result.get("winner")
    if winner_slot == "A":
        result["winner_label"] = first_label
    elif winner_slot == "B":
        result["winner_label"] = second_label
    else:
        result["winner_label"] = "tie"
    return result


if __name__ == "__main__":
    import json

    from llm_client import make_judge_client

    client, model = make_judge_client()
    demo_persona = "你是一个非常节俭的人，平时不太喜欢社交，更愿意独处。"
    demo_records = [
        {"round_index": 0, "scenario_name": "日常一天", "action_label": "在家省钱度过",
         "behavior": "在家做饭看书", "mood": "neutral"},
        {"round_index": 1, "scenario_name": "涨工资", "action_label": "把多出来的钱全部存起来",
         "behavior": "把涨薪的钱全部存进了银行账户", "mood": "happy"},
    ]
    print(json.dumps(
        score_persona_consistency(client, demo_persona, demo_records, model=model),
        ensure_ascii=False, indent=2,
    ))
