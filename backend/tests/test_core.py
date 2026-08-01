from datetime import date
from pathlib import Path

from app.ai import request_hash
from app.db import Database
from app.main import health
from app.schemas import ExplainMistakeRequest


def test_database_initializes_dashboard(tmp_path: Path) -> None:
    database = Database(tmp_path / "test.db")
    database.initialize()

    dashboard = database.dashboard()
    assert dashboard["plan_name"] == "四级基础提升计划"
    assert dashboard["target_completion_date"] > date.today().isoformat()
    assert len(dashboard["tasks"]) == 4


def test_health_response() -> None:
    assert health()["status"] == "ok"


def test_ai_cache_hash_is_stable() -> None:
    payload = ExplainMistakeRequest(
        question_type="reading",
        question="What does the author mean?",
        options={"A": "One", "B": "Two"},
        user_answer="A",
        correct_answer="B",
    )
    assert request_hash(payload, "deepseek-v4-flash") == request_hash(payload, "deepseek-v4-flash")
    assert request_hash(payload, "deepseek-v4-flash") != request_hash(payload, "deepseek-v4-pro")
