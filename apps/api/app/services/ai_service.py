from __future__ import annotations

import json
import re
from typing import Any

import httpx

from app.core.config import settings


SCORE_SCHEMA_HINT = """
Respond ONLY with valid JSON (no markdown) using this shape:
{
  "reply_zh": "your next Chinese message in character",
  "reply_vi": "Vietnamese translation of your reply",
  "grammar": 0-100,
  "vocabulary": 0-100,
  "naturalness": 0-100,
  "corrected_zh": "improved learner sentence or same if already good",
  "corrected_vi": "Vietnamese meaning of corrected sentence",
  "feedback_vi": "short coaching tip in Vietnamese"
}
"""


def _mock_roleplay(user_message: str, starter: str) -> dict[str, Any]:
    return {
        "reply_zh": "好的，请继续说明具体情况。",
        "reply_vi": "Được, hãy tiếp tục giải thích tình hình cụ thể.",
        "grammar": 78,
        "vocabulary": 80,
        "naturalness": 72,
        "corrected_zh": user_message.strip() or "老板，订单可能会延期两天。",
        "corrected_vi": "Sếp, đơn hàng có thể sẽ trễ hai ngày.",
        "feedback_vi": "Chế độ demo (chưa cấu hình OPENAI_API_KEY). Câu của bạn đã được ghi nhận.",
        "_demo": True,
        "_starter": starter,
    }


async def generate_roleplay_turn(
    *,
    system_prompt: str,
    history: list[dict[str, str]],
    user_message: str,
) -> dict[str, Any]:
    if not settings.openai_api_key:
        starter = history[0]["content"] if history else "你好。"
        return _mock_roleplay(user_message, starter)

    messages = [
        {"role": "system", "content": f"{system_prompt}\n\n{SCORE_SCHEMA_HINT}"},
        *history,
        {"role": "user", "content": user_message},
    ]
    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(
            f"{settings.openai_base_url.rstrip('/')}/chat/completions",
            headers={
                "Authorization": f"Bearer {settings.openai_api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": settings.openai_model,
                "temperature": 0.4,
                "messages": messages,
                "response_format": {"type": "json_object"},
            },
        )
        resp.raise_for_status()
        data = resp.json()
        content = data["choices"][0]["message"]["content"]
    try:
        parsed = json.loads(content)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", content, re.DOTALL)
        parsed = json.loads(match.group(0)) if match else _mock_roleplay(user_message, "")
    return parsed
