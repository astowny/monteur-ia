from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from ai_service.models.schemas import CloudJob


class SqliteRepository:
    def __init__(self, db_path: str) -> None:
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def _init_schema(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS jobs (
                    id TEXT PRIMARY KEY,
                    operation TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    status TEXT NOT NULL,
                    result TEXT
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS analytics_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    properties TEXT NOT NULL
                )
                """
            )

    def save_job(self, job: CloudJob) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO jobs(id, operation, payload, status, result)
                VALUES(?,?,?,?,?)
                ON CONFLICT(id) DO UPDATE SET
                  operation=excluded.operation,
                  payload=excluded.payload,
                  status=excluded.status,
                  result=excluded.result
                """,
                (
                    job.id,
                    job.operation,
                    json.dumps(job.payload, ensure_ascii=False),
                    job.status,
                    json.dumps(job.result, ensure_ascii=False) if job.result is not None else None,
                ),
            )

    def get_job(self, job_id: str) -> CloudJob:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT id, operation, payload, status, result FROM jobs WHERE id=?", (job_id,)
            ).fetchone()
        if row is None:
            raise KeyError(job_id)
        return CloudJob(
            id=row[0],
            operation=row[1],
            payload=json.loads(row[2]),
            status=row[3],
            result=json.loads(row[4]) if row[4] else None,
        )

    def store_event(self, name: str, properties: dict) -> None:
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO analytics_events(name, properties) VALUES(?, ?)",
                (name, json.dumps(properties, ensure_ascii=False)),
            )

    def list_events(self) -> list[dict]:
        with self._connect() as conn:
            rows = conn.execute("SELECT name, properties FROM analytics_events ORDER BY id ASC").fetchall()
        return [{"name": name, "properties": json.loads(props)} for name, props in rows]
