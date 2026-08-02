from __future__ import annotations

import argparse
import json
import re
import sqlite3
import sys
import unicodedata
from datetime import datetime
from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))

from app.config import get_settings  # noqa: E402
from app.db import Database  # noqa: E402


WORD_RE = re.compile(r"^[a-z]+(?:[-'][a-z]+)*$")
PART_OF_SPEECH_RE = re.compile(r"^((?:n|v[ti]?|a|ad|adv|prep|conj|pron|num|int)\.)")


def clean_entry(raw: dict) -> tuple[dict | None, bool]:
    original_word = unicodedata.normalize("NFKC", str(raw.get("word", ""))).lstrip("\ufeff").strip().lower()
    # The source contains a small, systematic OCR substitution of IPA glyphs in words.
    word = original_word.translate(str.maketrans({"ɔ": "o", "ʃ": "f", "ŋ": "n"}))
    word = re.sub(r"\([a-z]+\)$", "", word)
    meaning = unicodedata.normalize("NFKC", str(raw.get("mean", ""))).strip()
    phonetic = unicodedata.normalize("NFKC", str(raw.get("phonetic_symbol", ""))).strip() or None
    if not word or not meaning or not WORD_RE.fullmatch(word):
        return None, word != original_word
    match = PART_OF_SPEECH_RE.match(meaning)
    return ({"word": word, "meaning": meaning, "phonetic": phonetic,
             "part_of_speech": match.group(1) if match else None}, word != original_word)


def load_entries(source_dir: Path) -> tuple[list[dict], dict[str, int]]:
    unique: dict[str, dict] = {}
    stats = {"files": 0, "raw": 0, "repaired": 0, "invalid": 0, "duplicates": 0}
    for path in sorted(source_dir.glob("*.json")):
        stats["files"] += 1
        records = json.loads(path.read_text(encoding="utf-8-sig"))
        for raw in records:
            stats["raw"] += 1
            entry, repaired = clean_entry(raw)
            stats["repaired"] += int(repaired)
            if entry is None:
                stats["invalid"] += 1
            elif entry["word"] in unique:
                stats["duplicates"] += 1
            else:
                unique[entry["word"]] = entry
    return list(unique.values()), stats


def import_entries(database_path: Path, entries: list[dict], source: str) -> int:
    Database(database_path).initialize()
    now = datetime.now().isoformat(timespec="seconds")
    with sqlite3.connect(database_path) as connection:
        before = connection.total_changes
        connection.executemany(
            """INSERT INTO words(word,phonetic,meaning,part_of_speech,level,source,created_at)
            VALUES(:word,:phonetic,:meaning,:part_of_speech,'CET4',:source,:created_at)
            ON CONFLICT(word) DO UPDATE SET phonetic=excluded.phonetic,meaning=excluded.meaning,
            part_of_speech=excluded.part_of_speech,source=excluded.source""",
            [{**entry, "source": source, "created_at": now} for entry in entries],
        )
        return connection.total_changes - before


def main() -> None:
    parser = argparse.ArgumentParser(description="清洗并导入四级 JSON 词库")
    parser.add_argument("source", type=Path, help="包含 A.json 到 Z.json 的目录")
    parser.add_argument("--database", type=Path, default=get_settings().database_file)
    args = parser.parse_args()
    entries, stats = load_entries(args.source)
    changed = import_entries(args.database, entries, "Vocabulary-of-CET-4")
    print(json.dumps({**stats, "valid_unique": len(entries), "database_changes": changed,
                      "database": str(args.database)}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
