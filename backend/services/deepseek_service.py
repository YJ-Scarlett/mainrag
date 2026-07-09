import httpx
from fastapi import HTTPException

from core.config import settings


async def generate_answer(question: str, references: list[dict]) -> str:
    if not settings.deepseek_api_key:
        raise HTTPException(503, "尚未配置 DEEPSEEK_API_KEY，请在启动后端的终端中设置环境变量后重启")
    context = "\n\n".join(
        f"[资料：{item['document']}，片段 {item['chunk']}]\n{item['content']}" for item in references
    )
    payload = {
        "model": settings.deepseek_model,
        "temperature": 0.3,
        "messages": [
            {"role": "system", "content": "你是课程助教。只基于提供的知识库片段回答；资料不足时明确说明，不得编造。回答准确、易懂。"},
            {"role": "user", "content": f"课程知识库片段：\n{context}\n\n学生问题：{question}"},
        ],
    }
    try:
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                f"{settings.deepseek_base_url}/chat/completions",
                headers={"Authorization": f"Bearer {settings.deepseek_api_key}"}, json=payload,
            )
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]
    except httpx.HTTPStatusError as exc:
        raise HTTPException(502, f"DeepSeek 调用失败：{exc.response.text[:300]}") from exc
    except (httpx.HTTPError, KeyError, IndexError) as exc:
        raise HTTPException(502, f"DeepSeek 服务异常：{exc}") from exc

async def generate_answer_stream(question: str, references: list[dict]):
    """流式生成回答，逐块返回内容"""
    if not settings.deepseek_api_key:
        raise HTTPException(503, "尚未配置 DEEPSEEK_API_KEY")

    context = "\n\n".join(
        f"[资料：{item['document']}，片段 {item['chunk']}]\n{item['content']}" for item in references
    )
    payload = {
        "model": settings.deepseek_model,
        "temperature": 0.3,
        "stream": True,
        "messages": [
            {"role": "system", "content": "你是课程助教。只基于提供的知识库片段回答；资料不足时明确说明，不得编造。回答准确、易懂。"},
            {"role": "user", "content": f"课程知识库片段：\n{context}\n\n学生问题：{question}"},
        ],
    }
    try:
        async with httpx.AsyncClient(timeout=60) as client:
            async with client.stream(
                "POST",
                f"{settings.deepseek_base_url}/chat/completions",
                headers={"Authorization": f"Bearer {settings.deepseek_api_key}"},
                json=payload,
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data = line[6:]
                        if data == "[DONE]":
                            break
                        try:
                            import json
                            chunk = json.loads(data)
                            delta = chunk["choices"][0]["delta"].get("content")
                            if delta:
                                yield delta
                        except (json.JSONDecodeError, KeyError, IndexError):
                            continue
    except httpx.HTTPStatusError as exc:
        raise HTTPException(502, f"DeepSeek 流式调用失败：{exc.response.text[:300]}") from exc
    except (httpx.HTTPError, Exception) as exc:
        raise HTTPException(502, f"DeepSeek 服务异常：{exc}") from exc