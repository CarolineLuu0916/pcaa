"""离线 mock LLM 客户端：不发任何网络请求，只用于验证整条 pipeline
（agent/baseline/judge/run_mvp/analysis/export）在没有 API key 时也能跑通、
不会在某个环节因为格式不匹配而崩溃。不保证生成内容的"真实感"。

通过解析 user_prompt 里的内容判断这是哪种调用（agent 行为选择 / persona
consistency 打分 / social realism A-B），分别返回符合各自 schema 的 JSON。
"""
from __future__ import annotations

import random
import re


class _Message:
    def __init__(self, content: str) -> None:
        self.content = content


class _Choice:
    def __init__(self, content: str) -> None:
        self.message = _Message(content)


class _Response:
    def __init__(self, content: str) -> None:
        self.choices = [_Choice(content)]


MOCK_BEHAVIORS = [
    "按照当下的心情和状态做了一个比较自然的选择。",
    "权衡了一下手头的状况，最终选了这个选项。",
    "没有想太多，凭直觉做了这个决定。",
]
MOCK_MOODS = ["happy", "neutral", "sad", "anxious"]


class MockOpenAIClient:
    """接口形状对齐 openai.OpenAI：client.chat.completions.create(...)。"""

    def __init__(self, seed: int = 0) -> None:
        self._rng = random.Random(seed)
        self.chat = self
        self.completions = self

    def create(self, model=None, temperature=None, response_format=None, messages=None, **kwargs) -> _Response:
        user_prompt = messages[1]["content"]
        content = self._mock_content(user_prompt)
        return _Response(content)

    def _mock_content(self, user_prompt: str) -> str:
        if "action_id" in user_prompt and "本轮可选的行为选项" in user_prompt:
            option_ids = re.findall(r'id="([^"]+)"', user_prompt)
            action_id = self._rng.choice(option_ids) if option_ids else "unknown"
            behavior = self._rng.choice(MOCK_BEHAVIORS)
            mood = self._rng.choice(MOCK_MOODS)
            return f'{{"action_id": "{action_id}", "behavior": "{behavior}", "mood": "{mood}"}}'

        if '"score"' in user_prompt:
            score = self._rng.randint(1, 5)
            return f'{{"score": {score}, "reason": "mock 评分，仅用于离线管线验证"}}'

        if '"winner"' in user_prompt:
            winner = self._rng.choice(["A", "B", "tie"])
            return f'{{"winner": "{winner}", "reason": "mock 判断，仅用于离线管线验证"}}'

        return "{}"
