import sqlite3
import os
import json

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "scans.db")

def get_connection():
    return sqlite3.connect(DB_PATH)

def init_db():
    """
    Initializes the scans database and creates the scans table if it does not exist.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS scans (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        filename TEXT,
        candidate_name TEXT,
        overall_score INTEGER,
        summary TEXT,
        strengths TEXT,
        weaknesses TEXT,
        improvements TEXT,
        raw_text TEXT,
        is_resume INTEGER,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)
    conn.commit()
    conn.close()
    print(f"[INFO] SQL Database initialized successfully at: {DB_PATH}")

def save_scan(data: dict) -> int:
    """
    Saves a resume scan result to the SQLite database.
    Serializes strengths, weaknesses, and improvements lists into JSON strings.
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    filename = data.get("filename", "unknown.pdf")
    candidate_name = data.get("candidate_name", "Candidate")
    overall_score = int(data.get("overall_score", 0))
    summary = data.get("summary", "")
    
    # Serialize complex lists/dicts to JSON strings
    strengths = json.dumps(data.get("strengths", []))
    weaknesses = json.dumps(data.get("weaknesses", []))
    improvements = json.dumps(data.get("improvements", []))
    
    raw_text = data.get("raw_text", "")
    is_resume = 1 if data.get("is_resume", True) else 0
    
    cursor.execute("""
    INSERT INTO scans (filename, candidate_name, overall_score, summary, strengths, weaknesses, improvements, raw_text, is_resume)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (filename, candidate_name, overall_score, summary, strengths, weaknesses, improvements, raw_text, is_resume))
    
    scan_id = cursor.lastrowid
    conn.commit()
    conn.close()
    print(f"[SUCCESS] Saved scan to SQL Database with ID: {scan_id}")
    return scan_id

def get_all_scans() -> list:
    """
    Retrieves summary parameters for all past scans, ordered by latest.
    """
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("""
    SELECT id, filename, candidate_name, overall_score, is_resume, timestamp 
    FROM scans 
    ORDER BY timestamp DESC
    """)
    rows = cursor.fetchall()
    
    scans = []
    for r in rows:
        scans.append({
            "id": r["id"],
            "filename": r["filename"],
            "candidate_name": r["candidate_name"],
            "overall_score": r["overall_score"],
            "is_resume": bool(r["is_resume"]),
            "timestamp": r["timestamp"]
        })
    conn.close()
    return scans

def get_scan_by_id(scan_id: int) -> dict:
    """
    Retrieves a single scan details by its primary key ID, deserializing complex fields.
    """
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("""
    SELECT id, filename, candidate_name, overall_score, summary, strengths, weaknesses, improvements, raw_text, is_resume, timestamp
    FROM scans
    WHERE id = ?
    """, (scan_id,))
    r = cursor.fetchone()
    
    if not r:
        conn.close()
        return None
        
    scan_data = {
        "id": r["id"],
        "filename": r["filename"],
        "candidate_name": r["candidate_name"],
        "overall_score": r["overall_score"],
        "summary": r["summary"],
        "strengths": json.loads(r["strengths"] or "[]"),
        "weaknesses": json.loads(r["weaknesses"] or "[]"),
        "improvements": json.loads(r["improvements"] or "[]"),
        "raw_text": r["raw_text"],
        "is_resume": bool(r["is_resume"]),
        "timestamp": r["timestamp"]
    }
    conn.close()
    return scan_data

def clear_all_scans():
    """
    Truncates the scans table, deleting all persistent scan records.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM scans")
    conn.commit()
    conn.close()
    print("[SUCCESS] Cleared all scans from SQL Database.")
