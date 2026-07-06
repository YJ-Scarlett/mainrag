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
            {"role": "system", "content": "你是课程助教。只基于提供的知识库片段回答；资料不足时明确说明，不得编造。回答准确、易懂，并标注参考资料名称。"},
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
