"""
Database operations module for Student Attendance System
Handles all SQLite database interactions, schema management, and data operations
"""

import sqlite3
import os
from datetime import datetime, date
from typing import Optional, List, Tuple, Dict

# Database configuration
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_FILE = os.path.join(BASE_DIR, 'attendance.db')


def get_connection():
    """Get a connection to the SQLite database."""
    return sqlite3.connect(DB_FILE)


def init_db():
    """Create core tables if they don't exist."""
    conn = get_connection()
    c = conn.cursor()

    # Students table
    c.execute('''
    CREATE TABLE IF NOT EXISTS students (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_code TEXT UNIQUE,
        name TEXT,
        created_at TEXT
    )
    ''')

    # Attendance table with lecture support
    c.execute('''
    CREATE TABLE IF NOT EXISTS attendance (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER,
        student_code TEXT,
        name TEXT,
        date TEXT,
        time TEXT,
        method TEXT,
        lecture_id INTEGER,
        UNIQUE(student_id, date, lecture_id)
    )
    ''')

    # Lectures table (optional for future use)
    c.execute('''
    CREATE TABLE IF NOT EXISTS lectures (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        date TEXT,
        created_at TEXT
    )
    ''')

    conn.commit()
    conn.close()


def upgrade_db():
    """Safe database migration helper for schema updates."""
    conn = get_connection()
    c = conn.cursor()
    try:
        c.execute("PRAGMA table_info(attendance)")
        columns = [col[1] for col in c.fetchall()]
        if 'lecture_id' not in columns:
            c.execute('ALTER TABLE attendance ADD COLUMN lecture_id INTEGER')
            conn.commit()
    except Exception:
        pass
    finally:
        conn.close()


# ==================== Student Operations ====================

def add_student(student_code: str, name: str) -> Tuple[bool, str]:
    """
    Add a new student to the database.
    Returns: (success: bool, message: str)
    """
    conn = get_connection()
    c = conn.cursor()
    now = datetime.now().isoformat()
    
    try:
        c.execute('INSERT INTO students (student_code, name, created_at) VALUES (?, ?, ?)',
                  (student_code, name, now))
        conn.commit()
        return True, f"Student {name} registered successfully"
    except sqlite3.IntegrityError:
        return False, f"Student code '{student_code}' already exists"
    except Exception as e:
        return False, f"Failed to register student: {str(e)}"
    finally:
        conn.close()


def get_student_by_code(student_code: str) -> Optional[Tuple[int, str, str]]:
    """
    Get student information by student code.
    Returns: (id, student_code, name) or None if not found
    """
    conn = get_connection()
    c = conn.cursor()
    c.execute('SELECT id, student_code, name FROM students WHERE student_code = ?', 
              (student_code,))
    result = c.fetchone()
    conn.close()
    return result


def get_student_by_id(student_id: int) -> Optional[Dict[str, str]]:
    """
    Get student information by ID.
    Returns: {'code': str, 'name': str} or None
    """
    conn = get_connection()
    c = conn.cursor()
    c.execute('SELECT student_code, name FROM students WHERE id = ?', (student_id,))
    row = c.fetchone()
    conn.close()
    
    if row:
        return {'code': row[0], 'name': row[1]}
    return None


def get_all_students() -> List[Tuple[str, str, str]]:
    """
    Get all students from database.
    Returns: List of (student_code, name, created_at)
    """
    conn = get_connection()
    c = conn.cursor()
    c.execute('SELECT student_code, name, created_at FROM students')
    results = c.fetchall()
    conn.close()
    return results


def get_students_dict() -> Dict[int, Dict[str, str]]:
    """
    Get all students as a dictionary keyed by student ID.
    Returns: {student_id: {'code': str, 'name': str}}
    """
    conn = get_connection()
    c = conn.cursor()
    c.execute('SELECT id, student_code, name FROM students')
    students = {row[0]: {'code': row[1], 'name': row[2]} for row in c.fetchall()}
    conn.close()
    return students


def get_total_students() -> int:
    """Get total count of registered students."""
    conn = get_connection()
    c = conn.cursor()
    c.execute('SELECT COUNT(*) FROM students')
    count = c.fetchone()[0]
    conn.close()
    return count


# ==================== Attendance Operations ====================

def mark_attendance(student_id: int, student_code: str, name: str, 
                   method: str = 'recognition', lecture_id: Optional[int] = None) -> Tuple[bool, str]:
    """
    Mark attendance for a student.
    Returns: (success: bool, message: str)
    """
    today = date.today().isoformat()
    now = datetime.now().time().strftime('%H:%M:%S')
    
    conn = get_connection()
    c = conn.cursor()
    
    try:
        c.execute('''INSERT INTO attendance 
                     (student_id, student_code, name, date, time, method, lecture_id) 
                     VALUES (?, ?, ?, ?, ?, ?, ?)''',
                  (student_id, student_code, name, today, now, method, lecture_id))
        conn.commit()
        return True, f'Attendance recorded for {name}'
    except sqlite3.IntegrityError:
        return False, f'Attendance already recorded for {name} today'
    except Exception as e:
        return False, f'Attendance failed: {str(e)}'
    finally:
        conn.close()


def get_all_attendance() -> List[Tuple[str, str, str, str, str]]:
    """
    Get all attendance records ordered by date and time (descending).
    Returns: List of (student_code, name, date, time, method)
    """
    conn = get_connection()
    c = conn.cursor()
    c.execute('''SELECT student_code, name, date, time, method 
                 FROM attendance 
                 ORDER BY date DESC, time DESC''')
    results = c.fetchall()
    conn.close()
    return results


def get_attendance_by_date() -> List[Tuple[str, int]]:
    """
    Get attendance counts grouped by date.
    Returns: List of (date, count)
    """
    conn = get_connection()
    c = conn.cursor()
    c.execute('''
        SELECT date, COUNT(DISTINCT student_id) as count
        FROM attendance
        GROUP BY date
        ORDER BY date
    ''')
    results = c.fetchall()
    conn.close()
    return results


def get_attendance_summary() -> Dict:
    """
    Get overall attendance summary statistics.
    Returns: {'total_students': int, 'attendance_by_date': List[Tuple]}
    """
    conn = get_connection()
    c = conn.cursor()

    c.execute('SELECT COUNT(*) FROM students')
    total_students = c.fetchone()[0]

    c.execute('''
        SELECT date, COUNT(DISTINCT student_id) as count
        FROM attendance
        GROUP BY date
        ORDER BY date
    ''')
    attendance_data = c.fetchall()
    
    conn.close()

    return {
        'total_students': total_students,
        'attendance_by_date': attendance_data
    }


# ==================== Lecture Operations ====================

def create_lecture(title: str, lecture_date: Optional[str] = None) -> int:
    """
    Create a new lecture entry.
    Returns: lecture_id
    """
    if lecture_date is None:
        lecture_date = date.today().isoformat()
    
    conn = get_connection()
    c = conn.cursor()
    now = datetime.now().isoformat()
    
    c.execute('INSERT INTO lectures (title, date, created_at) VALUES (?, ?, ?)',
              (title, lecture_date, now))
    lecture_id = c.lastrowid
    conn.commit()
    conn.close()
    
    return lecture_id


def get_all_lectures() -> List[Tuple[int, str, str, str]]:
    """
    Get all lectures.
    Returns: List of (id, title, date, created_at)
    """
    conn = get_connection()
    c = conn.cursor()
    c.execute('SELECT id, title, date, created_at FROM lectures ORDER BY date DESC')
    results = c.fetchall()
    conn.close()
    return results