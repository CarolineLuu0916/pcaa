"""实验组 Agent Loop：Hard Persona JSON 作为先验注入 system prompt，
每轮在场景给定的封闭行为选项中做选择，行为效应与人格漂移均由
environment.py / persona.py 确定性计算，LLM 只负责"选哪个 + 怎么描述"。
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field

from openai import OpenAI

from environment import apply_action_effects, apply_environment_effects, find_action_category, next_scenario
from llm_client import DEEPSEEK_MODEL, chat_json
from memory import AgentMemory, MemoryEntry
from persona import TRAIT_ORDER, HardPersona, SoftState

RESPONSE_INSTRUCTIONS = """请只返回一个 JSON 对象，不要任何多余文字，字段如下：
{
  "action_id": "<必须是上面给出的某个行为选项的 id，原样照抄>",
  "behavior": "<用第一人称简短描述你这一轮具体做了什么、是怎么想的，1-2句话>",
  "mood": "<happy / neutral / sad / anxious 中的一个，描述这轮结束后的心情>"
}"""


def build_options_block(scenario: dict) -> str:
    lines = [
        f'- id="{c["id"]}"：{c["label"]}（{c["prompt_hint"]}）'
        for c in scenario["action_categories"]
    ]
    return "本轮可选的行为选项（必须从中选择一个）：\n" + "\n".join(lines)


_TRAIT_LABELS = {
    "frugality":         ("极度爱消费/大方花钱，不在乎节省", "极度节俭，很少做非必要花费"),
    "social":            ("非常内向，偏好独处，不喜欢社交", "非常外向，热爱与人互动和社交"),
    "risk_appetite":     ("极度厌恶风险，偏好稳定确定", "热衷冒险，拥抱高风险高回报"),
    "conscientiousness": ("随性而为，缺乏计划性和自律性", "极有条理，做事非常有计划性和责任心"),
    "openness":          ("保守传统，不喜欢新鲜事物", "好奇心旺盛，非常乐于尝试新事物和想法"),
    "agreeableness":     ("个性强硬，以自我为中心，不太妥协", "非常随和友善，愿意照顾他人感受"),
}


def _trait_interpretation(trait: str, value: float) -> str:
    low_desc, high_desc = _TRAIT_LABELS.get(trait, ("低端", "高端"))
    v = f"{value:.2f}"
    if value <= 0.25:
        return f"强烈偏向[{low_desc}]（{v}，极低）"
    if value <= 0.4:
        return f"偏向[{low_desc}]（{v}，偏低）"
    if value <= 0.6:
        return f"居中（{v}，中等），两端行为概率相近"
    if value <= 0.75:
        return f"偏向[{high_desc}]（{v}，偏高）"
    return f"强烈偏向[{high_desc}]（{v}，极高）"


def build_persona_block(persona: HardPersona) -> str:
    traits = persona.traits
    interp_lines = "\n".join(
        "  " + t + ": " + _trait_interpretation(t, traits[t])
        for t in ["frugality", "social", "risk_appetite", "conscientiousness", "openness", "agreeableness"]
        if t in traits
    )
    return (
        "以下是你的人格先验（范围 0-1，影响各选项被选中的概率分布，不是必须遵守的规则）：\n"
        + persona.to_prompt_json()
        + "\n\n每个维度的行为倾向解读：\n"
        + interp_lines
        + "\n\n关键原则：\n"
        "- 上面的倾向影响的是概率偏移，不是绝对排除。\n"
        "  极低 frugality 意味着你大概率花钱，但偶尔也可能克制；"
        "  极高 social 意味着你大概率选择社交，但也可能某天只想独处。\n"
        "- 即使同一场景多次出现，也要结合当下心情、精力、财富、最近经历"
        "做出有起伏的具体选择，不能每次都选同一行为类别。\n"
        "- 长期来看选择分布要与这套人格大致吻合，但任何单轮都不应机械地只选同一类行为。"
    )


_DAILY_NUDGES = [
    "今天精力格外充沛，感觉可以做很多事。",
    "有点头疼，身体略感不适，做决定时有些提不起劲。",
    "睡眠不足，思维有些迟钝，但还是想把事情处理好。",
    "心情比平时好一些，对很多事都觉得无所谓。",
    "有点烦躁，容易被小事影响情绪。",
    "感觉平静，情绪很稳定，不偏向任何一边。",
    "刚和老朋友聊过天，有点怀旧，想起了一些过去的事。",
    "最近工作压力有点大，脑子里装着别的事。",
    "今天有点想一个人待着，不太想和人打交道。",
    "上周花了不少钱，今天对钱的事格外敏感。",
    "最近看了下账户余额，感觉财务状况还不错，心里踏实。",
    "今天时间比较充裕，不用赶，可以慢慢想清楚。",
    "今天事情比较多，有点赶，倾向于快点做决定。",
    "早上遇到了点小麻烦，心里有点疙瘩还没解开。",
    "天气很好，心情受到了正面影响，感觉什么都可以。",
    "最近在思考一些长远的事，今天的决定会放在更大的框架里考虑。",
    "刚看到一条让人沮丧的新闻，整个人有点低落。",
    "感觉自己最近有点太放纵了，今天想稍微收一收。",
    "感觉最近太压抑了，今天想让自己放松一下。",
    "没什么特别的感觉，就是普通的一天。",
]


def sample_daily_nudge(rng: "random.Random") -> str:
    return rng.choice(_DAILY_NUDGES)


def build_state_block(soft_state: SoftState, scenario: dict, memory_text: str, daily_nudge: str = "") -> str:
    nudge_line = f"今日小情境：{daily_nudge}\n" if daily_nudge else ""
    return (
        f"当前场景：{scenario['name']} —— {scenario['description']}\n"
        f"你当前的状态：心情={soft_state.mood}，精力={soft_state.energy:.2f}，"
        f"财富={soft_state.wealth:.0f}，疲劳度={soft_state.fatigue:.2f}\n"
        f"{nudge_line}"
        f"最近的经历：\n{memory_text}\n\n"
        f"{build_options_block(scenario)}\n\n"
        f"{RESPONSE_INSTRUCTIONS}"
    )


@dataclass
class RoundRecord:
    condition: str
    persona_id: str
    persona_name: str
    round_index: int
    meta_round_index: int
    scenario_id: str
    scenario_name: str
    action_id: str
    action_label: str
    behavior: str
    mood: str
    trait_signal: dict
    persona_vector_initial: list
    persona_vector_current: list | None
    soft_state: dict

    def to_dict(self) -> dict:
        return {
            "condition": self.condition,
            "persona_id": self.persona_id,
            "persona_name": self.persona_name,
            "round_index": self.round_index,
            "meta_round_index": self.meta_round_index,
            "scenario_id": self.scenario_id,
            "scenario_name": self.scenario_name,
            "action_id": self.action_id,
            "action_label": self.action_label,
            "behavior": self.behavior,
            "mood": self.mood,
            "trait_signal": self.trait_signal,
            "persona_vector_initial": self.persona_vector_initial,
            "persona_vector_current": self.persona_vector_current,
            "soft_state": self.soft_state,
        }


def run_experimental_agent(
    persona: HardPersona,
    scenarios: list[dict],
    rounds: int,
    client: OpenAI,
    model: str = DEEPSEEK_MODEL,
    drift_rate: float = 0.05,
    nudge_seed: int | None = None,
) -> list[RoundRecord]:
    """跑完一个 persona 在实验条件下的完整轮次，返回每轮记录。

    CLAUDE.md 里"每轮 persona[t+1] = 0.95*persona[t] + 0.05*delta"的"轮"，
    指的是 3.1 节表格里的"模拟轮次"（MVP=10 轮），而每一轮内部会依次经历
    全部 num_scenarios 个场景（= rounds // num_scenarios 个 timestep 才算一轮）。
    所以漂移只应该在每个"轮"结束时触发一次，用这一轮内全部 timestep 的
    trait_signal 平均值作为 delta；如果每个 timestep 都触发一次漂移，
    50 个 timestep 会让 (1-rate) 连乘 50 次，几轮之内就把初始人格洗掉，
    远超"慢漂移"的设计意图。
    """
    import random
    rng = random.Random(nudge_seed)

    initial_vector = persona.as_vector()
    current = persona
    soft_state = SoftState()
    memory = AgentMemory()
    records: list[RoundRecord] = []
    num_scenarios = len(scenarios)
    pending_signals: list[dict] = []

    for round_index in range(rounds):
        scenario = next_scenario(round_index, scenarios)
        soft_state = apply_environment_effects(soft_state, scenario)

        daily_nudge = sample_daily_nudge(rng)
        system_prompt = build_persona_block(current)
        user_prompt = build_state_block(soft_state, scenario, memory.compress(), daily_nudge=daily_nudge)
        response = chat_json(client, system_prompt, user_prompt, model=model)

        action_id = response["action_id"]
        action_category = find_action_category(scenario, action_id)
        behavior = response.get("behavior", "")
        mood = response.get("mood", soft_state.mood)

        soft_state = apply_action_effects(soft_state, action_category, mood)
        memory.append(MemoryEntry(
            round_index=round_index,
            scenario_name=scenario["name"],
            action_label=action_category["label"],
            behavior=behavior,
            mood=mood,
        ))
        pending_signals.append(action_category["trait_signal"])

        is_meta_round_end = (round_index + 1) % num_scenarios == 0
        if is_meta_round_end:
            avg_signal = {
                k: sum(s[k] for s in pending_signals) / len(pending_signals)
                for k in TRAIT_ORDER
            }
            current = current.drift(avg_signal, rate=drift_rate)
            pending_signals = []

        records.append(RoundRecord(
            condition="experimental",
            persona_id=persona.id,
            persona_name=persona.name,
            round_index=round_index,
            meta_round_index=round_index // len(scenarios),
            scenario_id=scenario["id"],
            scenario_name=scenario["name"],
            action_id=action_id,
            action_label=action_category["label"],
            behavior=behavior,
            mood=mood,
            trait_signal=action_category["trait_signal"],
            persona_vector_initial=initial_vector,
            persona_vector_current=current.as_vector(),
            soft_state=soft_state.to_dict(),
        ))

    return records


if __name__ == "__main__":
    import sys

    from llm_client import make_deepseek_client
    from persona import load_personas
    from environment import load_scenarios

    personas = load_personas("config/personas.json")
    scenarios = load_scenarios("config/scenarios.json")
    client = make_deepseek_client()

    target = personas[0]
    records = run_experimental_agent(target, scenarios, rounds=3, client=client)
    for r in records:
        print(json.dumps(r.to_dict(), ensure_ascii=False, indent=2))
