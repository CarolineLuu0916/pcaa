"""更贴近 Generative Agents (Park et al., 2023) 的记忆子系统：
memory stream + retrieval(recency/importance/relevance) + reflection。

跟 memory.py（PCAA 实验组/简单 baseline 用的"最近 K 条"窗口）的区别：
这里每条记忆有 importance（LLM 打分）、last_accessed（用于 recency 衰减），
retrieve() 按 recency + importance + relevance 加权排序取 top-k，
而不是无脑取最近 k 条；并且会在累计 importance 超过阈值时触发一次
reflection（从近期记忆里提炼更高层次的感悟，写回记忆流）。

诚实声明一个简化点：原始 GA 论文的 relevance 是 embedding cosine similarity，
这里没有引入任何 embedding API（项目至今只用 chat completion，不想为了这一个
baseline 多接一个付费依赖），改用字符 bigram 频次向量的 cosine similarity
作为轻量级替代——对中文短句已经够用，但不等价于语义嵌入，论文/网站里需要
如实说明这一点，不能假装是论文原版的 embedding retrieval。
"""
from __future__ import annotations

import math
from collections import Counter
from dataclasses import dataclass, field

from openai import OpenAI

from llm_client import chat_json


def _char_bigrams(text: str) -> Counter:
    chars = [c for c in text if not c.isspace()]
    if len(chars) < 2:
        return Counter(chars)
    return Counter("".join(chars[i:i + 2]) for i in range(len(chars) - 1))


def text_relevance(a: str, b: str) -> float:
    """字符 bigram 频次向量的 cosine similarity，充当 embedding relevance 的轻量替代。"""
    ca, cb = _char_bigrams(a), _char_bigrams(b)
    if not ca or not cb:
        return 0.0
    common = set(ca) & set(cb)
    dot = sum(ca[g] * cb[g] for g in common)
    norm_a = math.sqrt(sum(v * v for v in ca.values()))
    norm_b = math.sqrt(sum(v * v for v in cb.values()))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def score_importance(client: OpenAI, model: str, content: str) -> int:
    """1-10 打分，越高代表这条记忆对当事人越值得长期记住（GA 论文 poignancy 打分的简化版）。"""
    system_prompt = (
        "你在给一段模拟生活中的记忆打重要性分数，回答这段经历对当事人的日常生活/"
        "身份认同有多重要、多值得长期记住。1=完全日常、毫无意义的小事，"
        "10=人生级别的重大事件。这是虚构模拟里的日常小事居多，分数应该大多落在"
        "1-5 之间，只有真正特殊的情况才给高分，不要为了好看而普遍打高分。"
    )
    user_prompt = f"记忆内容：{content}\n只返回 JSON：{{\"importance\": <1-10整数>}}"
    result = chat_json(client, system_prompt, user_prompt, model=model, temperature=0)
    try:
        return max(1, min(10, int(result.get("importance", 3))))
    except (TypeError, ValueError):
        return 3


@dataclass
class GAMemoryEntry:
    round_index: int
    kind: str  # "observation" | "reflection"
    content: str
    importance: int
    last_accessed: int


@dataclass
class GAMemoryStream:
    entries: list[GAMemoryEntry] = field(default_factory=list)
    importance_since_reflection: int = 0
    reflection_threshold: int = 25
    recency_decay: float = 0.98

    def add(self, content: str, round_index: int, client: OpenAI, model: str, kind: str = "observation") -> GAMemoryEntry:
        importance = score_importance(client, model, content) if kind == "observation" else 8
        entry = GAMemoryEntry(
            round_index=round_index, kind=kind, content=content,
            importance=importance, last_accessed=round_index,
        )
        self.entries.append(entry)
        if kind == "observation":
            self.importance_since_reflection += importance
        return entry

    def retrieve(self, query: str, current_round: int, k: int = 5) -> list[GAMemoryEntry]:
        if not self.entries:
            return []
        scored = []
        for e in self.entries:
            recency = self.recency_decay ** max(0, current_round - e.last_accessed)
            importance_norm = e.importance / 10.0
            relevance = text_relevance(query, e.content)
            score = recency + importance_norm + relevance
            scored.append((score, e))
        scored.sort(key=lambda x: -x[0])
        top = [e for _, e in scored[:k]]
        for e in top:
            e.last_accessed = current_round
        return top

    def should_reflect(self) -> bool:
        return self.importance_since_reflection >= self.reflection_threshold

    def reset_reflection_counter(self) -> None:
        self.importance_since_reflection = 0

    def recent_observations(self, n: int = 10) -> list[GAMemoryEntry]:
        obs = [e for e in self.entries if e.kind == "observation"]
        return obs[-n:]
