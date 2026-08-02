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
    assert health()["api_version"] == 3
    assert isinstance(health()["pid"], int)


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


def test_word_session_and_review(tmp_path: Path) -> None:
    database = Database(tmp_path / "test.db")
    database.initialize()
    with database.connect() as connection:
        connection.execute(
            "INSERT INTO words(word,meaning,created_at) VALUES('abandon','vt. 放弃','2026-01-01')"
        )

    session = database.word_session(15)
    assert session["new_count"] == 11
    assert [item["word"] for item in session["words"][:3]] == ["plan", "goal", "possible"]
    abandon = next(item for item in session["words"] if item["word"] == "abandon")

    result = database.review_word(abandon["id"], "known", 2)
    assert result["interval_days"] == 3
    with database.connect() as connection:
        progress = connection.execute("SELECT * FROM word_progress").fetchone()
        log = connection.execute("SELECT * FROM word_review_logs").fetchone()
    assert progress["review_count"] == 1
    assert log["result"] == "known"


def test_lesson_can_be_completed(tmp_path: Path) -> None:
    database = Database(tmp_path / "test.db")
    database.initialize()
    lesson = database.lesson(1)
    assert lesson["title"] == "A Small Plan That Works"
    assert len(lesson["sections"]) == 2
    assert [item["word"] for item in lesson["vocabulary"][:3]] == ["plan", "goal", "possible"]

    answers = {str(question["id"]): question["correct_answer"] for question in lesson["questions"]}
    result = database.complete_lesson(1, answers)
    assert result["score"] == 100
    assert database.lesson(1)["completed"] is True
