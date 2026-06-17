"""DeepSeek / OpenAI 兼容客户端的最小封装，统一处理结构化 JSON 输出与重试。

API key 通过 .env 文件（python-dotenv）或系统环境变量读取，从不在代码或
对话记录里出现明文 key——见项目根目录的 .env.example。
"""
from __future__ import annotations

import json
import os
import re
import time

from dotenv import load_dotenv
from openai import OpenAI, RateLimitError

load_dotenv()

DEEPSEEK_BASE_URL = "https://api.deepseek.com"
DEEPSEEK_MODEL = "deepseek-chat"

OPENAI_JUDGE_MODEL = "gpt-4o"
KIMI_BASE_URL = "https://api.moonshot.cn/v1"
KIMI_JUDGE_MODEL = os.environ.get("KIMI_JUDGE_MODEL", "moonshot-v1-8k")
DEEPSEEK_JUDGE_MODEL = "deepseek-chat"


class LLMCallError(RuntimeError):
    pass


def make_deepseek_client() -> OpenAI:
    api_key = os.environ.get("DEEPSEEK_API_KEY")
    if not api_key:
        raise LLMCallError("环境变量 DEEPSEEK_API_KEY 未设置（可以写在项目根目录的 .env 文件里）")
    return OpenAI(api_key=api_key, base_url=DEEPSEEK_BASE_URL)


def make_deepseek_judge_client() -> tuple[OpenAI, str]:
    """DeepSeek-chat 作为第二个 judge，用于与 Kimi 结果交叉验证。"""
    api_key = os.environ.get("DEEPSEEK_API_KEY")
    if not api_key:
        raise LLMCallError("需要 DEEPSEEK_API_KEY 来使用 DeepSeek 作为 judge")
    return OpenAI(api_key=api_key, base_url=DEEPSEEK_BASE_URL), DEEPSEEK_JUDGE_MODEL


def make_judge_client() -> tuple[OpenAI, str]:
    """优先用 OPENAI_API_KEY（GPT-4o）；没有的话回退到 MOONSHOT_API_KEY（Kimi，
    OpenAI 兼容接口）。返回 (client, model)，调用方需要把 model 传给 chat_json。
    """
    openai_key = os.environ.get("OPENAI_API_KEY")
    if openai_key:
        return OpenAI(api_key=openai_key), OPENAI_JUDGE_MODEL

    kimi_key = os.environ.get("MOONSHOT_API_KEY")
    if kimi_key:
        return OpenAI(api_key=kimi_key, base_url=KIMI_BASE_URL), KIMI_JUDGE_MODEL

    raise LLMCallError(
        "需要 OPENAI_API_KEY 或 MOONSHOT_API_KEY 其中一个作为 judge 的 API key"
        "（写在项目根目录的 .env 文件里）"
    )


def _extract_json(text: str) -> dict:
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        raise LLMCallError(f"无法从响应中提取 JSON：{text[:200]!r}")
    return json.loads(match.group(0))


def chat_json(
    client: OpenAI,
    system_prompt: str,
    user_prompt: str,
    model: str = DEEPSEEK_MODEL,
    temperature: float = 0.7,
    max_retries: int = 4,
) -> dict:
    """调用 chat completion，要求模型返回单个 JSON 对象，429/过载时指数退避重试。"""
    last_error: Exception | None = None
    for attempt in range(max_retries + 1):
        try:
            resp = client.chat.completions.create(
                model=model,
                temperature=temperature,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
            )
            content = resp.choices[0].message.content
            return _extract_json(content)
        except RateLimitError as exc:
            last_error = exc
            if attempt < max_retries:
                wait = 30 * (2 ** attempt)  # 30s, 60s, 120s, 240s
                print(f"[chat_json] 429 过载，{wait}s 后重试（第 {attempt+1}/{max_retries} 次）...")
                time.sleep(wait)
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            if attempt < max_retries:
                continue
    raise LLMCallError(f"调用 LLM 失败（已重试 {max_retries} 次）：{last_error}") from last_error
