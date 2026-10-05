import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

DB_PATH = Path(__file__).parent / "data" / "readiness.db"

app = FastAPI(title="DART Student AI Readiness API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class AssessmentIn(BaseModel):
    student_name: str = "Anonymous"
    q1: int
    q2: int
    verify: int
    tech: int
    score: int
    stage: str
    next_step: str


def get_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS assessments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_name TEXT NOT NULL,
            q1 INTEGER NOT NULL,
            q2 INTEGER NOT NULL,
            verify INTEGER NOT NULL,
            tech INTEGER NOT NULL,
            score INTEGER NOT NULL,
            stage TEXT NOT NULL,
            next_step TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )
    conn.commit()
    conn.close()


init_db()


@app.post("/api/assessments")
def save_assessment(a: AssessmentIn):
    conn = get_db()
    cursor = conn.execute(
        """
        INSERT INTO assessments (student_name, q1, q2, verify, tech, score, stage, next_step, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            a.student_name,
            a.q1,
            a.q2,
            a.verify,
            a.tech,
            a.score,
            a.stage,
            a.next_step,
            datetime.now(timezone.utc).isoformat(),
        ),
    )
    conn.commit()
    row = conn.execute(
        "SELECT * FROM assessments WHERE id = ?", (cursor.lastrowid,)
    ).fetchone()
    conn.close()
    return dict(row)


@app.get("/api/assessments")
def list_assessments():
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM assessments ORDER BY created_at DESC"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


@app.get("/api/health")
def health():
    return {"status": "ok"}
