from __future__ import annotations
import hashlib
import json
import time
import httpx
from fastapi import HTTPException
from .config import Settings
from .db import Database
from .schemas import AiExplanation, ExplainMistakeRequest


SYSTEM_PROMPT = """你是一位耐心的大学英语四六级老师，面对的是英语基础较弱的大学生。
标准答案由题库提供，你只能解释标准答案，不能自行改变答案。使用简单中文，引用英文时给出中文含义。
必须输出 JSON 对象，字段为 summary、correct_reason、wrong_reason、evidence、vocabulary、grammar、strategy、follow_up_question。
evidence 是含 text 和 translation 的数组；vocabulary 是含 word 和 meaning 的数组；grammar 是字符串数组；
follow_up_question 可为 null 或含 question、answer、explanation。不要输出 Markdown 或 JSON 之外的内容。"""


def request_hash(payload: ExplainMistakeRequest, model: str) -> str:
    content = payload.model_dump(exclude={"regenerate"}) | {"model": model, "prompt_version": "v1"}
    return hashlib.sha256(json.dumps(content, ensure_ascii=False, sort_keys=True).encode()).hexdigest()


async def explain_mistake(payload: ExplainMistakeRequest, settings: Settings, database: Database):
    if not settings.deepseek_api_key:
        raise HTTPException(status_code=503, detail="尚未配置 DeepSeek API Key，请复制 backend/.env.example 为 backend/.env 后填写。")
    model = payload.model or settings.deepseek_model
    input_hash = request_hash(payload, model)
    if not payload.regenerate:
        cached = database.cached_explanation(input_hash)
        if cached:
            return AiExplanation.model_validate(cached), model, True
    user_content = json.dumps({
        "题型": payload.question_type, "原文": payload.passage, "题目": payload.question,
        "选项": payload.options, "用户答案": payload.user_answer, "标准答案": payload.correct_answer,
        "固定解析": payload.official_explanation, "用户选择的错误原因": payload.error_reason,
    }, ensure_ascii=False)
    started = time.perf_counter()
    error_message = None
    usage = {}
    try:
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                f"{settings.deepseek_base_url.rstrip('/')}/chat/completions",
                headers={"Authorization": f"Bearer {settings.deepseek_api_key}", "Content-Type": "application/json"},
                json={"model": model, "messages": [{"role": "system", "content": SYSTEM_PROMPT},
                      {"role": "user", "content": user_content}], "response_format": {"type": "json_object"},
                      "temperature": 0.2, "max_tokens": 1800},
            )
            response.raise_for_status()
            body = response.json()
            usage = body.get("usage") or {}
            explanation = AiExplanation.model_validate(json.loads(body["choices"][0]["message"]["content"]))
            database.save_explanation(input_hash, model, explanation.model_dump())
            return explanation, model, False
    except (httpx.HTTPError, KeyError, IndexError, json.JSONDecodeError, ValueError) as exc:
        error_message = str(exc)
        raise HTTPException(status_code=502, detail=f"AI解析生成失败：{error_message}") from exc
    finally:
        database.log_ai_usage(feature="mistake_explanation", model_name=model,
            prompt_tokens=usage.get("prompt_tokens", 0), completion_tokens=usage.get("completion_tokens", 0),
            total_tokens=usage.get("total_tokens", 0), duration_ms=int((time.perf_counter()-started)*1000),
            success=error_message is None, error_message=error_message)
