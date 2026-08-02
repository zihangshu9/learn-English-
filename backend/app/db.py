from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Iterator


SCHEMA = """
PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS schema_meta (key TEXT PRIMARY KEY, value TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS study_plans (
 id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, level TEXT NOT NULL DEFAULT 'CET4',
 foundation_level TEXT NOT NULL DEFAULT 'weak', start_date TEXT NOT NULL,
 target_completion_date TEXT NOT NULL, daily_minutes INTEGER NOT NULL DEFAULT 30 CHECK(daily_minutes > 0),
 weekly_days INTEGER NOT NULL DEFAULT 6 CHECK(weekly_days BETWEEN 1 AND 7),
 new_words_limit INTEGER NOT NULL DEFAULT 15 CHECK(new_words_limit > 0),
 progress_percent REAL NOT NULL DEFAULT 0, status TEXT NOT NULL DEFAULT 'active',
 created_at TEXT NOT NULL, updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS daily_tasks (
 id INTEGER PRIMARY KEY AUTOINCREMENT, plan_id INTEGER NOT NULL REFERENCES study_plans(id) ON DELETE CASCADE,
 task_date TEXT NOT NULL, title TEXT NOT NULL, task_type TEXT NOT NULL, target_count INTEGER NOT NULL DEFAULT 0,
 completed_count INTEGER NOT NULL DEFAULT 0, estimated_minutes INTEGER NOT NULL DEFAULT 0,
 status TEXT NOT NULL DEFAULT 'pending', created_at TEXT NOT NULL, completed_at TEXT,
 UNIQUE(plan_id, task_date, task_type)
);
CREATE TABLE IF NOT EXISTS words (
 id INTEGER PRIMARY KEY AUTOINCREMENT, word TEXT NOT NULL UNIQUE, phonetic TEXT, meaning TEXT NOT NULL,
 part_of_speech TEXT, example TEXT, example_translation TEXT, frequency INTEGER NOT NULL DEFAULT 0,
 level TEXT NOT NULL DEFAULT 'CET4', source TEXT, audio_path TEXT, created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS word_progress (
 id INTEGER PRIMARY KEY AUTOINCREMENT, word_id INTEGER NOT NULL UNIQUE REFERENCES words(id) ON DELETE CASCADE,
 status TEXT NOT NULL DEFAULT 'unlearned', familiarity REAL NOT NULL DEFAULT 0, first_learned_at TEXT,
 last_reviewed_at TEXT, next_review_at TEXT, review_count INTEGER NOT NULL DEFAULT 0,
 correct_count INTEGER NOT NULL DEFAULT 0, wrong_count INTEGER NOT NULL DEFAULT 0,
 interval_days INTEGER NOT NULL DEFAULT 0, is_favorite INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS word_review_logs (
 id INTEGER PRIMARY KEY AUTOINCREMENT, word_id INTEGER NOT NULL REFERENCES words(id) ON DELETE CASCADE,
 result TEXT NOT NULL, review_mode TEXT NOT NULL DEFAULT 'card', response_seconds INTEGER, reviewed_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS papers (
 id INTEGER PRIMARY KEY AUTOINCREMENT, level TEXT NOT NULL DEFAULT 'CET4', year INTEGER NOT NULL,
 month INTEGER NOT NULL, set_number INTEGER NOT NULL, title TEXT NOT NULL, paper_path TEXT, answer_path TEXT,
 audio_path TEXT, source TEXT, import_status TEXT NOT NULL DEFAULT 'pending', UNIQUE(level,year,month,set_number)
);
CREATE TABLE IF NOT EXISTS paper_sections (
 id INTEGER PRIMARY KEY AUTOINCREMENT, paper_id INTEGER NOT NULL REFERENCES papers(id) ON DELETE CASCADE,
 section_type TEXT NOT NULL, title TEXT NOT NULL, instructions TEXT, sort_order INTEGER NOT NULL DEFAULT 0,
 time_limit_seconds INTEGER
);
CREATE TABLE IF NOT EXISTS questions (
 id INTEGER PRIMARY KEY AUTOINCREMENT, section_id INTEGER NOT NULL REFERENCES paper_sections(id) ON DELETE CASCADE,
 question_number TEXT NOT NULL, question_type TEXT NOT NULL, passage TEXT, question_text TEXT NOT NULL,
 options_json TEXT, correct_answer TEXT NOT NULL, official_explanation TEXT, evidence_text TEXT,
 audio_start_ms INTEGER, audio_end_ms INTEGER, difficulty INTEGER, sort_order INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS question_attempts (
 id INTEGER PRIMARY KEY AUTOINCREMENT, question_id INTEGER NOT NULL REFERENCES questions(id) ON DELETE CASCADE,
 user_answer TEXT NOT NULL, correct_answer_snapshot TEXT NOT NULL, is_correct INTEGER NOT NULL,
 response_seconds INTEGER, attempt_mode TEXT NOT NULL DEFAULT 'practice', attempted_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS mistakes (
 id INTEGER PRIMARY KEY AUTOINCREMENT, question_id INTEGER NOT NULL UNIQUE REFERENCES questions(id) ON DELETE CASCADE,
 first_attempt_id INTEGER REFERENCES question_attempts(id), error_reason TEXT, user_note TEXT,
 wrong_count INTEGER NOT NULL DEFAULT 1, review_correct_streak INTEGER NOT NULL DEFAULT 0,
 status TEXT NOT NULL DEFAULT 'pending', next_review_at TEXT, created_at TEXT NOT NULL, mastered_at TEXT
);
CREATE TABLE IF NOT EXISTS ai_explanations (
 id INTEGER PRIMARY KEY AUTOINCREMENT, question_id INTEGER, attempt_id INTEGER, model_name TEXT NOT NULL,
 prompt_version TEXT NOT NULL, input_hash TEXT NOT NULL UNIQUE, explanation_json TEXT,
 status TEXT NOT NULL DEFAULT 'generating', error_message TEXT, created_at TEXT NOT NULL, updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS ai_usage_logs (
 id INTEGER PRIMARY KEY AUTOINCREMENT, feature TEXT NOT NULL, model_name TEXT NOT NULL,
 prompt_tokens INTEGER NOT NULL DEFAULT 0, completion_tokens INTEGER NOT NULL DEFAULT 0,
 total_tokens INTEGER NOT NULL DEFAULT 0, duration_ms INTEGER NOT NULL DEFAULT 0,
 success INTEGER NOT NULL, error_message TEXT, created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS study_sessions (
 id INTEGER PRIMARY KEY AUTOINCREMENT, task_type TEXT NOT NULL, reference_id INTEGER,
 started_at TEXT NOT NULL, ended_at TEXT, active_seconds INTEGER NOT NULL DEFAULT 0,
 completed_count INTEGER NOT NULL DEFAULT 0, correct_count INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS app_settings (key TEXT PRIMARY KEY, value_json TEXT NOT NULL, updated_at TEXT NOT NULL);
CREATE INDEX IF NOT EXISTS idx_tasks_plan_date ON daily_tasks(plan_id,task_date);
CREATE INDEX IF NOT EXISTS idx_word_progress_review ON word_progress(next_review_at);
CREATE INDEX IF NOT EXISTS idx_attempts_question ON question_attempts(question_id);
CREATE INDEX IF NOT EXISTS idx_mistakes_review ON mistakes(status,next_review_at);
"""


class Database:
    def __init__(self, path: Path):
        self.path = path

    @contextmanager
    def connect(self) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        try:
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def initialize(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as connection:
            connection.executescript(SCHEMA)
            connection.execute("INSERT OR REPLACE INTO schema_meta(key,value) VALUES('version','1')")
            self._seed_default_plan(connection)
            connection.execute("PRAGMA optimize")

    def _seed_default_plan(self, connection: sqlite3.Connection) -> None:
        now = datetime.now().isoformat(timespec="seconds")
        today = date.today()
        existing = connection.execute(
            "SELECT id FROM study_plans WHERE status='active' ORDER BY id LIMIT 1"
        ).fetchone()
        if existing:
            plan_id = existing["id"]
        else:
            target = today + timedelta(days=304)
            cursor = connection.execute(
                "INSERT INTO study_plans(name,start_date,target_completion_date,created_at,updated_at) VALUES(?,?,?,?,?)",
                ("四级基础提升计划", today.isoformat(), target.isoformat(), now, now),
            )
            plan_id = cursor.lastrowid
        defaults = [
            ("复习旧单词", "word_review", 20, 8), ("学习新单词", "new_words", 15, 12),
            ("基础阅读", "reading", 1, 15), ("复习错题", "mistake_review", 5, 8),
        ]
        for title, task_type, count, minutes in defaults:
            connection.execute(
                """INSERT OR IGNORE INTO daily_tasks(
                plan_id,task_date,title,task_type,target_count,estimated_minutes,created_at
                ) VALUES(?,?,?,?,?,?,?)""",
                (plan_id, today.isoformat(), title, task_type, count, minutes, now),
            )

    def dashboard(self) -> dict:
        today = date.today()
        now = datetime.now().isoformat(timespec="seconds")
        with self.connect() as connection:
            plan = connection.execute(
                "SELECT * FROM study_plans WHERE status='active' ORDER BY id LIMIT 1"
            ).fetchone()
            if not plan:
                raise RuntimeError("没有可用的学习计划")
            total_words = connection.execute("SELECT COUNT(*) FROM words WHERE level='CET4'").fetchone()[0]
            learned_words = connection.execute(
                "SELECT COUNT(*) FROM word_progress WHERE status!='unlearned'"
            ).fetchone()[0]
            due_words = connection.execute(
                "SELECT COUNT(*) FROM word_progress WHERE status!='unlearned' AND next_review_at<=?", (now,)
            ).fetchone()[0]
            word_task_progress = {
                row["task_type"]: row["completed_count"] for row in connection.execute(
                    """SELECT task_type,completed_count FROM daily_tasks
                    WHERE plan_id=? AND task_date=? AND task_type IN ('word_review','new_words')""",
                    (plan["id"], today.isoformat()),
                ).fetchall()
            }
            review_target = min(20, due_words + word_task_progress.get("word_review", 0))
            new_limit = min(plan["new_words_limit"], max(total_words - learned_words, 0)
                            + word_task_progress.get("new_words", 0))
            connection.execute(
                """UPDATE daily_tasks SET target_count=?, status=CASE
                WHEN completed_count>=? THEN 'completed'
                WHEN completed_count>0 THEN 'in_progress' ELSE 'pending' END
                WHERE plan_id=? AND task_date=? AND task_type='word_review'""",
                (review_target, review_target, plan["id"], today.isoformat()),
            )
            connection.execute(
                """UPDATE daily_tasks SET target_count=?, status=CASE
                WHEN completed_count>=? THEN 'completed'
                WHEN completed_count>0 THEN 'in_progress' ELSE 'pending' END
                WHERE plan_id=? AND task_date=? AND task_type='new_words'""",
                (new_limit, new_limit, plan["id"], today.isoformat()),
            )
            progress_percent = round(learned_words * 100 / total_words, 1) if total_words else 0
            connection.execute(
                "UPDATE study_plans SET progress_percent=?,updated_at=? WHERE id=?",
                (progress_percent, now, plan["id"]),
            )
            tasks = connection.execute(
                "SELECT * FROM daily_tasks WHERE plan_id=? AND task_date=? ORDER BY id",
                (plan["id"], today.isoformat()),
            ).fetchall()
            target = date.fromisoformat(plan["target_completion_date"])
            return {
                "plan_name": plan["name"], "target_completion_date": plan["target_completion_date"],
                "days_remaining": max((target - today).days, 0), "progress_percent": progress_percent,
                "streak_days": self._study_streak(connection, today), "tasks": [dict(task) for task in tasks],
            }

    def word_session(self, limit: int) -> dict:
        now = datetime.now().isoformat(timespec="seconds")
        with self.connect() as connection:
            due = connection.execute(
                """SELECT w.*, p.status, p.review_count FROM words w
                JOIN word_progress p ON p.word_id=w.id
                WHERE p.status!='unlearned' AND p.next_review_at<=?
                ORDER BY p.next_review_at, w.id LIMIT ?""",
                (now, limit),
            ).fetchall()
            remaining = limit - len(due)
            new = connection.execute(
                """SELECT w.*, COALESCE(p.status,'unlearned') status,
                COALESCE(p.review_count,0) review_count FROM words w
                LEFT JOIN word_progress p ON p.word_id=w.id
                WHERE p.word_id IS NULL OR p.status='unlearned'
                ORDER BY w.frequency DESC, w.id LIMIT ?""",
                (remaining,),
            ).fetchall() if remaining else []
        rows = [*due, *new]
        fields = ("id", "word", "phonetic", "meaning", "part_of_speech", "example",
                  "example_translation", "status", "review_count")
        return {
            "words": [{field: row[field] for field in fields} for row in rows],
            "review_count": len(due),
            "new_count": len(new),
        }

    def review_word(self, word_id: int, result: str, response_seconds: int | None) -> dict:
        now = datetime.now()
        now_text = now.isoformat(timespec="seconds")
        with self.connect() as connection:
            word = connection.execute("SELECT id FROM words WHERE id=?", (word_id,)).fetchone()
            if not word:
                raise ValueError("单词不存在")
            progress = connection.execute(
                "SELECT * FROM word_progress WHERE word_id=?", (word_id,)
            ).fetchone()
            was_new = not progress or progress["status"] == "unlearned"
            old_interval = progress["interval_days"] if progress else 0
            if result == "known":
                interval = 3 if old_interval == 0 else min(max(old_interval * 2, 3), 90)
                familiarity, status, correct, wrong = 1.0, "learning", 1, 0
            elif result == "fuzzy":
                interval = 1
                familiarity, status, correct, wrong = 0.55, "learning", 0, 1
            else:
                interval = 0
                familiarity, status, correct, wrong = 0.2, "learning", 0, 1
            next_review = now + (timedelta(minutes=10) if interval == 0 else timedelta(days=interval))
            connection.execute(
                """INSERT INTO word_progress(word_id,status,familiarity,first_learned_at,last_reviewed_at,
                next_review_at,review_count,correct_count,wrong_count,interval_days)
                VALUES(?,?,?,?,?,?,1,?,?,?) ON CONFLICT(word_id) DO UPDATE SET
                status=excluded.status,familiarity=excluded.familiarity,last_reviewed_at=excluded.last_reviewed_at,
                next_review_at=excluded.next_review_at,review_count=word_progress.review_count+1,
                correct_count=word_progress.correct_count+excluded.correct_count,
                wrong_count=word_progress.wrong_count+excluded.wrong_count,interval_days=excluded.interval_days""",
                (word_id, status, familiarity, now_text, now_text,
                 next_review.isoformat(timespec="seconds"), correct, wrong, interval),
            )
            connection.execute(
                "INSERT INTO word_review_logs(word_id,result,response_seconds,reviewed_at) VALUES(?,?,?,?)",
                (word_id, result, response_seconds, now_text),
            )
            task_type = "new_words" if was_new else "word_review"
            connection.execute(
                """UPDATE daily_tasks SET completed_count=MIN(completed_count+1,target_count),
                status=CASE WHEN completed_count+1>=target_count THEN 'completed' ELSE 'in_progress' END
                WHERE task_date=? AND task_type=?""",
                (date.today().isoformat(), task_type),
            )
        return {"word_id": word_id, "status": status, "familiarity": familiarity,
                "interval_days": interval, "next_review_at": next_review.isoformat(timespec="seconds")}

    @staticmethod
    def _study_streak(connection: sqlite3.Connection, today: date) -> int:
        rows = connection.execute(
            "SELECT DISTINCT substr(started_at,1,10) AS study_date FROM study_sessions WHERE active_seconds>0"
        ).fetchall()
        dates = {date.fromisoformat(row["study_date"]) for row in rows}
        cursor = today if today in dates else today - timedelta(days=1)
        streak = 0
        while cursor in dates:
            streak += 1
            cursor -= timedelta(days=1)
        return streak

    def cached_explanation(self, input_hash: str) -> dict | None:
        with self.connect() as connection:
            row = connection.execute(
                "SELECT explanation_json FROM ai_explanations WHERE input_hash=? AND status='success'",
                (input_hash,),
            ).fetchone()
        return json.loads(row["explanation_json"]) if row else None

    def save_explanation(self, input_hash: str, model: str, explanation: dict) -> None:
        now = datetime.now().isoformat(timespec="seconds")
        with self.connect() as connection:
            connection.execute(
                """INSERT INTO ai_explanations(model_name,prompt_version,input_hash,explanation_json,status,created_at,updated_at)
                VALUES(?,'v1',?,?,'success',?,?) ON CONFLICT(input_hash) DO UPDATE SET
                explanation_json=excluded.explanation_json,status='success',updated_at=excluded.updated_at""",
                (model, input_hash, json.dumps(explanation, ensure_ascii=False), now, now),
            )

    def log_ai_usage(self, **values: object) -> None:
        with self.connect() as connection:
            connection.execute(
                """INSERT INTO ai_usage_logs(feature,model_name,prompt_tokens,completion_tokens,total_tokens,
                duration_ms,success,error_message,created_at) VALUES(?,?,?,?,?,?,?,?,?)""",
                (values["feature"], values["model_name"], values.get("prompt_tokens", 0),
                 values.get("completion_tokens", 0), values.get("total_tokens", 0), values.get("duration_ms", 0),
                 int(bool(values["success"])), values.get("error_message"), datetime.now().isoformat(timespec="seconds")),
            )
