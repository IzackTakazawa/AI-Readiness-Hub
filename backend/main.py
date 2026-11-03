import hashlib
import secrets
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from fastapi import Depends, FastAPI, Header, HTTPException
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


class SignUpIn(BaseModel):
    username: str
    password: str


class SignInIn(BaseModel):
    username: str
    password: str


class AssessmentIn(BaseModel):
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


def hash_password(password: str, salt: str) -> str:
    return hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), 100_000).hex()


def init_db():
    conn = get_db()
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            salt TEXT NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS sessions (
            token TEXT PRIMARY KEY,
            student_id INTEGER NOT NULL,
            created_at TEXT NOT NULL
        );
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
        );
        """
    )
    columns = [row["name"] for row in conn.execute("PRAGMA table_info(assessments)")]
    if "student_id" not in columns:
        conn.execute("ALTER TABLE assessments ADD COLUMN student_id INTEGER")
    conn.commit()
    conn.close()


init_db()


def get_current_student(authorization: str = Header(None)) -> sqlite3.Row:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Sign in required")
    token = authorization.split(" ", 1)[1]
    conn = get_db()
    student = conn.execute(
        "SELECT s.* FROM sessions se JOIN students s ON s.id = se.student_id WHERE se.token = ?",
        (token,),
    ).fetchone()
    conn.close()
    if not student:
        raise HTTPException(status_code=401, detail="Invalid or expired session")
    return student


@app.post("/api/auth/signup")
def sign_up(data: SignUpIn):
    username = data.username.strip()
    if not username or len(data.password) < 4:
        raise HTTPException(status_code=400, detail="Enter a username and a password of at least 4 characters")
    salt = secrets.token_hex(16)
    conn = get_db()
    try:
        conn.execute(
            "INSERT INTO students (username, salt, password_hash, created_at) VALUES (?, ?, ?, ?)",
            (username, salt, hash_password(data.password, salt), datetime.now(timezone.utc).isoformat()),
        )
        conn.commit()
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail="That username is already taken")
    finally:
        conn.close()
    return {"ok": True}


@app.post("/api/auth/signin")
def sign_in(data: SignInIn):
    conn = get_db()
    student = conn.execute(
        "SELECT * FROM students WHERE username = ?", (data.username.strip(),)
    ).fetchone()
    conn.close()
    if not student or hash_password(data.password, student["salt"]) != student["password_hash"]:
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    token = secrets.token_hex(32)
    conn = get_db()
    conn.execute(
        "INSERT INTO sessions (token, student_id, created_at) VALUES (?, ?, ?)",
        (token, student["id"], datetime.now(timezone.utc).isoformat()),
    )
    conn.commit()
    conn.close()
    return {"token": token, "username": student["username"]}


@app.get("/api/me")
def me(student: sqlite3.Row = Depends(get_current_student)):
    return {"username": student["username"]}


@app.post("/api/assessments")
def save_assessment(a: AssessmentIn, student: sqlite3.Row = Depends(get_current_student)):
    conn = get_db()
    cursor = conn.execute(
        """
        INSERT INTO assessments (student_name, q1, q2, verify, tech, score, stage, next_step, created_at, student_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            student["username"],
            a.q1,
            a.q2,
            a.verify,
            a.tech,
            a.score,
            a.stage,
            a.next_step,
            datetime.now(timezone.utc).isoformat(),
            student["id"],
        ),
    )
    conn.commit()
    row = conn.execute("SELECT * FROM assessments WHERE id = ?", (cursor.lastrowid,)).fetchone()
    conn.close()
    return dict(row)


@app.get("/api/assessments")
def list_assessments(student: sqlite3.Row = Depends(get_current_student)):
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM assessments WHERE student_id = ? ORDER BY created_at DESC",
        (student["id"],),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


@app.get("/api/health")
def health():
    return {"status": "ok"}
