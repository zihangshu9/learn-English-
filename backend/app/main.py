from contextlib import asynccontextmanager
import mimetypes
import os
from pathlib import Path
import sys

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from .ai import explain_mistake
from .config import Settings, get_settings
from .db import Database
from .schemas import (
    AiSettingsUpdate, AiStatusResponse, DashboardResponse, ExplainMistakeRequest,
    ExplainMistakeResponse, LessonCompleteRequest, LessonCompleteResponse, LessonResponse,
    WordReviewRequest, WordReviewResponse, WordSessionResponse,
)


settings = get_settings()
database = Database(settings.database_file)
APP_API_VERSION = 3

# Windows can inherit an incorrect `.js` MIME mapping from the registry.
# ES module scripts are blocked by browsers unless they are served as JavaScript.
mimetypes.add_type("application/javascript", ".js", strict=True)
mimetypes.add_type("application/javascript", ".js", strict=False)


@asynccontextmanager
async def lifespan(_: FastAPI):
    database.initialize()
    yield


app = FastAPI(title=settings.app_name, version="0.1.0", description="个人本地使用的四六级学习系统 API", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["http://127.0.0.1:5173", "http://localhost:5173"],
                   allow_credentials=False, allow_methods=["GET", "POST", "PUT", "DELETE"], allow_headers=["Content-Type"])


@app.get("/api/health")
def health() -> dict[str, str | int]:
    return {"status": "ok", "app": settings.app_name, "api_version": APP_API_VERSION, "pid": os.getpid()}


@app.get("/api/dashboard", response_model=DashboardResponse)
def get_dashboard() -> dict:
    return database.dashboard()


@app.get("/api/words/session", response_model=WordSessionResponse)
def get_word_session(limit: int = 15) -> dict:
    return database.word_session(max(1, min(limit, 50)))


@app.post("/api/words/{word_id}/review", response_model=WordReviewResponse)
def review_word(word_id: int, payload: WordReviewRequest) -> dict:
    try:
        return database.review_word(word_id, payload.result, payload.response_seconds)
    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@app.get("/api/lessons/{lesson_id}", response_model=LessonResponse)
def get_lesson(lesson_id: int) -> dict:
    try:
        return database.lesson(lesson_id)
    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@app.post("/api/lessons/{lesson_id}/complete", response_model=LessonCompleteResponse)
def complete_lesson(lesson_id: int, payload: LessonCompleteRequest) -> dict:
    try:
        return database.complete_lesson(lesson_id, payload.answers)
    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@app.get("/api/ai/status", response_model=AiStatusResponse)
def ai_status(config: Settings = Depends(get_settings)) -> AiStatusResponse:
    return AiStatusResponse(configured=bool(config.deepseek_api_key), default_model=config.deepseek_model,
                            base_url=config.deepseek_base_url)


@app.put("/api/ai/settings", response_model=AiStatusResponse)
def update_ai_settings(payload: AiSettingsUpdate, config: Settings = Depends(get_settings)) -> AiStatusResponse:
    api_key = (payload.api_key or config.deepseek_api_key).strip()
    if "\n" in api_key or "\r" in api_key:
        raise ValueError("API Key 格式无效")
    config.env_file.parent.mkdir(parents=True, exist_ok=True)
    config.env_file.write_text(
        "\n".join([
            f"DEEPSEEK_API_KEY={api_key}",
            f"DEEPSEEK_BASE_URL={config.deepseek_base_url}",
            f"DEEPSEEK_MODEL={payload.model}",
            "",
        ]),
        encoding="utf-8",
    )
    get_settings.cache_clear()
    refreshed = get_settings()
    return AiStatusResponse(configured=bool(refreshed.deepseek_api_key), default_model=refreshed.deepseek_model,
                            base_url=refreshed.deepseek_base_url)


@app.post("/api/ai/explain-mistake", response_model=ExplainMistakeResponse)
async def create_mistake_explanation(payload: ExplainMistakeRequest, config: Settings = Depends(get_settings)):
    explanation, model, cached = await explain_mistake(payload, config, database)
    return ExplainMistakeResponse(explanation=explanation, model=model, cached=cached)


def frontend_dist() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS) / "frontend_dist"  # type: ignore[attr-defined]
    return Path(__file__).resolve().parents[2] / "frontend" / "dist"


dist_dir = frontend_dist()
if dist_dir.exists():
    assets_dir = dist_dir / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=assets_dir), name="frontend-assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    def serve_frontend(full_path: str) -> FileResponse:
        candidate = (dist_dir / full_path).resolve()
        if full_path and candidate.is_relative_to(dist_dir.resolve()) and candidate.is_file():
            return FileResponse(candidate)
        return FileResponse(dist_dir / "index.html")
