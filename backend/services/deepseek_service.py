import json

import httpx
from fastapi import HTTPException

from core.config import settings


def _build_payload(question: str, references: list[dict], stream: bool = False) -> dict:
    def label(item: dict) -> str:
        if item.get("start_time") is not None and item.get("end_time") is not None:
            return f"资料：{item['document']}，时间 {item['start_time']:.1f}s-{item['end_time']:.1f}s"
        return f"资料：{item['document']}，片段 {item['chunk']}"

    context = "\n\n".join(
        f"[{label(item)}]\n{item['content']}" for item in references
    )
    return {
        "model": settings.deepseek_model,
        "temperature": 0.3,
        "stream": stream,
        "messages": [
            {
                "role": "system",
                "content": (
                    "你是课程助教。只基于提供的知识库片段回答；资料不足时明确说明，不得编造。"
                    "回答要准确、易懂，并尽量使用 Markdown 格式：重点内容用 **加粗**，步骤、分类和结论用有序列表。"
                    "不要在正文末尾重复输出“参考资料”“参考来源”等来源列表，系统会在回答下方单独展示可追溯来源标签。"
                ),
            },
            {"role": "user", "content": f"课程知识库片段：\n{context}\n\n学生问题：{question}"},
        ],
    }


async def generate_answer(question: str, references: list[dict]) -> str:
    if not settings.deepseek_api_key:
        raise HTTPException(503, "尚未配置 DEEPSEEK_API_KEY，请在启动后端的终端中设置环境变量后重启")

    try:
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                f"{settings.deepseek_base_url}/chat/completions",
                headers={"Authorization": f"Bearer {settings.deepseek_api_key}"},
                json=_build_payload(question, references),
            )
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]
    except httpx.HTTPStatusError as exc:
        raise HTTPException(502, f"DeepSeek 调用失败：{exc.response.text[:300]}") from exc
    except (httpx.HTTPError, KeyError, IndexError) as exc:
        raise HTTPException(502, f"DeepSeek 服务异常：{exc}") from exc


async def stream_answer(question: str, references: list[dict]):
    if not settings.deepseek_api_key:
        raise HTTPException(503, "尚未配置 DEEPSEEK_API_KEY，请在启动后端的终端中设置环境变量后重启")

    try:
        async with httpx.AsyncClient(timeout=None) as client:
            async with client.stream(
                "POST",
                f"{settings.deepseek_base_url}/chat/completions",
                headers={"Authorization": f"Bearer {settings.deepseek_api_key}"},
                json=_build_payload(question, references, stream=True),
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if not line or not line.startswith("data:"):
                        continue
                    data = line.removeprefix("data:").strip()
                    if data == "[DONE]":
                        break
                    try:
                        payload = json.loads(data)
                        delta = payload["choices"][0].get("delta", {}).get("content", "")
                    except (json.JSONDecodeError, KeyError, IndexError):
                        delta = ""
                    if delta:
                        yield delta
    except httpx.HTTPStatusError as exc:
        raise HTTPException(502, f"DeepSeek 调用失败：{exc.response.text[:300]}") from exc
    except httpx.HTTPError as exc:
        raise HTTPException(502, f"DeepSeek 服务异常：{exc}") from exc
