from __future__ import annotations

import base64
import json
import re
import sqlite3
from datetime import datetime
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from flask import Flask, jsonify, render_template, request

from academic_data import COLLEGE_INFO, SUBJECT_BY_CODE, SUBJECTS, TIMETABLE, timetable_for_template

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "database.db"
FACE_DIR = BASE_DIR / "face_data"

app = Flask(__name__, template_folder="templates", static_folder="static")
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")


def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    FACE_DIR.mkdir(exist_ok=True)
    conn = get_db_connection()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            roll_number TEXT NOT NULL UNIQUE,
            enrollment_number TEXT NOT NULL UNIQUE,
            branch TEXT NOT NULL,
            year TEXT NOT NULL,
            section TEXT NOT NULL,
            photo TEXT,
            face_vector TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            date TEXT NOT NULL,
            time TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'Present',
            recognition_method TEXT NOT NULL DEFAULT 'Face Recognition',
            FOREIGN KEY(student_id) REFERENCES students(id),
            UNIQUE(student_id, date)
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS attendance_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            date TEXT NOT NULL,
            time TEXT NOT NULL,
            sign_out_time TEXT,
            status TEXT NOT NULL DEFAULT 'Present',
            recognition_method TEXT NOT NULL DEFAULT 'Face Recognition',
            subject_code TEXT,
            FOREIGN KEY(student_id) REFERENCES students(id)
        )
        """
    )
    attendance_columns = {
        row[1] for row in conn.execute("PRAGMA table_info(attendance)").fetchall()
    }
    if "subject_code" not in attendance_columns:
        conn.execute("ALTER TABLE attendance ADD COLUMN subject_code TEXT")
    if "sign_out_time" not in attendance_columns:
        conn.execute("ALTER TABLE attendance ADD COLUMN sign_out_time TEXT")
    conn.execute(
        "UPDATE students SET face_vector = NULL WHERE photo LIKE '%demo_student_%'"
    )
    conn.commit()
    conn.close()


def create_default_face_vector(length: int = 16384):
    rng = np.random.default_rng(42)
    return rng.normal(0.0, 1.0, size=length).astype(np.float32)


def ensure_demo_data():
    conn = get_db_connection()
    student_count = conn.execute("SELECT COUNT(*) AS count FROM students").fetchone()["count"]
    if student_count > 0:
        conn.close()
        return

    demo_students = [
        {
            "name": "Shreya Singh",
            "roll_number": "23",
            "enrollment_number": "25010023",
            "branch": "CSE",
            "year": "2nd Year",
            "section": "L",
        },
        {
            "name": "Aman Verma",
            "roll_number": "41",
            "enrollment_number": "2501041",
            "branch": "ECE",
            "year": "2nd Year",
            "section": "A",
        },
        {
            "name": "Priya Sharma",
            "roll_number": "12",
            "enrollment_number": "2501012",
            "branch": "IT",
            "year": "2nd Year",
            "section": "B",
        },
        {
            "name": "Rahul Gupta",
            "roll_number": "07",
            "enrollment_number": "2501007",
            "branch": "ME",
            "year": "2nd Year",
            "section": "C",
        },
        {
            "name": "Neha Kapoor",
            "roll_number": "58",
            "enrollment_number": "2501058",
            "branch": "CSE",
            "year": "2nd Year",
            "section": "L",
        },
    ]

    for idx, student in enumerate(demo_students, start=1):
        student_photo_path = FACE_DIR / f"demo_student_{idx}.png"
        generate_demo_face_image(student_photo_path, student["name"])
        try:
            student_vector = extract_face_vector_from_path(student_photo_path)
        except ValueError:
            student_vector = None
        conn.execute(
            """
            INSERT INTO students (name, roll_number, enrollment_number, branch, year, section, photo, face_vector)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                student["name"],
                student["roll_number"],
                student["enrollment_number"],
                student["branch"],
                student["year"],
                student["section"],
                str(student_photo_path),
                json.dumps(student_vector.tolist()) if student_vector is not None else None,
            ),
        )

    conn.commit()
    conn.close()


def generate_demo_face_image(path: Path, student_name: str):
    if path.exists():
        return
    width, height = 280, 320
    image = Image.new("RGB", (width, height), (245, 248, 252))
    draw = ImageDraw.Draw(image)
    draw.ellipse((60, 40, 220, 240), fill=(230, 190, 160))
    draw.ellipse((90, 100, 120, 130), fill=(20, 20, 20))
    draw.ellipse((160, 100, 190, 130), fill=(20, 20, 20))
    draw.arc((100, 130, 180, 180), start=180, end=0, fill=(110, 70, 50), width=4)
    draw.rounded_rectangle((80, 200, 200, 260), radius=20, fill=(90, 130, 180))
    draw.text((50, 270), student_name[:18], fill=(34, 45, 72), font=None)
    image = image.filter(ImageFilter.GaussianBlur(0.3))
    image.save(path)


def normalize_vector(vector):
    vector = np.asarray(vector, dtype=np.float32)
    norm = np.linalg.norm(vector)
    if norm == 0:
        return vector
    return vector / norm


def extract_face_vector_from_path(path: str | Path):
    image = cv2.imread(str(path))
    if image is None:
        raise ValueError("Unable to read the face image.")
    return extract_face_vector_from_image(image)


def extract_face_vector_from_image(image):
    if image is None:
        raise ValueError("No image data provided.")
    if image.ndim == 2:
        gray = image
    else:
        if image.shape[-1] == 4:
            image = cv2.cvtColor(image, cv2.COLOR_BGRA2BGR)
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    gray = cv2.equalizeHist(gray)
    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(60, 60))
    if len(faces) == 0:
        raise ValueError("No face detected.")
    if len(faces) > 1:
        raise ValueError("Multiple faces detected.")

    x, y, w, h = faces[0]
    face = gray[y : y + h, x : x + w]
    face = cv2.resize(face, (128, 128))
    vector = normalize_vector(face.flatten() / 255.0)
    return vector


def decode_image_data(image_data: str):
    if not image_data:
        raise ValueError("Image is required.")
    if image_data.startswith("data:image"):
        image_data = image_data.split(",", 1)[1]
    try:
        image_bytes = base64.b64decode(image_data)
    except Exception as exc:  # pragma: no cover
        raise ValueError("Invalid image data.") from exc
    np_array = np.frombuffer(image_bytes, dtype=np.uint8)
    image = cv2.imdecode(np_array, cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError("Unable to process the uploaded image.")
    return image


def student_row_to_dict(row):
    return {
        "id": row["id"],
        "name": row["name"],
        "roll_number": row["roll_number"],
        "enrollment_number": row["enrollment_number"],
        "branch": row["branch"],
        "year": row["year"],
        "section": row["section"],
        "photo": row["photo"],
    }


def get_student(student_id):
    conn = get_db_connection()
    row = conn.execute("SELECT * FROM students WHERE id = ?", (student_id,)).fetchone()
    conn.close()
    if row is None:
        return None
    return student_row_to_dict(row)


def get_all_students():
    conn = get_db_connection()
    rows = conn.execute("SELECT * FROM students ORDER BY id ASC").fetchall()
    conn.close()
    return [student_row_to_dict(row) for row in rows]


def format_display_date(date_value):
    if not date_value:
        return "—"
    for pattern in ("%Y-%m-%d", "%d-%m-%Y"):
        try:
            return datetime.strptime(str(date_value), pattern).strftime("%d-%m-%Y")
        except ValueError:
            continue
    return str(date_value)


def format_display_time(time_value):
    if not time_value:
        return "—"
    raw_value = str(time_value).strip()
    for pattern in ("%I:%M %p", "%H:%M"):
        try:
            return datetime.strptime(raw_value, pattern).strftime("%I:%M %p")
        except ValueError:
            continue
    return raw_value


def get_student_attendance(student_id):
    conn = get_db_connection()
    legacy_rows = conn.execute(
        "SELECT * FROM attendance WHERE student_id = ? ORDER BY date DESC, time DESC",
        (student_id,),
    ).fetchall()
    session_rows = conn.execute(
        "SELECT * FROM attendance_sessions WHERE student_id = ? ORDER BY date DESC, time DESC",
        (student_id,),
    ).fetchall()
    conn.close()
    records = []
    for row in [*legacy_rows, *session_rows]:
        subject_code = row["subject_code"]
        subject_name = subject_name_for_codes(subject_code) if subject_code else "Unassigned"
        code_value = subject_code or "N/A"

        if not subject_code or subject_name in {"Unassigned", "None", ""}:
            fallback_details = resolve_subject_details_from_timetable(row["date"], row["time"])
            subject_name = fallback_details["name"]
            code_value = fallback_details["code"]

        records.append(
            {
                "id": row["id"],
                "student_id": row["student_id"],
                "date": row["date"],
                "date_display": format_display_date(row["date"]),
                "time": row["time"],
                "time_display": format_display_time(row["time"]),
                "status": row["status"],
                "recognition_method": row["recognition_method"],
                "subject_code": code_value,
                "subject_name": subject_name,
                "sign_out_time": row["sign_out_time"],
                "sign_out_time_display": format_display_time(row["sign_out_time"]) if row["sign_out_time"] else "Active",
            }
        )
    return sorted(records, key=lambda record: (record["date"], record["time"]), reverse=True)


def subject_name_for_codes(subject_code):
    if not subject_code:
        return "Unassigned"

    raw_codes = str(subject_code).strip()
    tokens = re.split(r"\s*\+\s*|\s*/\s*|\s*,\s*", raw_codes)
    names = []
    for token in tokens:
        cleaned = re.sub(r"\s*\(.*?\)", "", token).strip()
        cleaned = cleaned.strip("()[]{} ")
        if not cleaned:
            continue
        if cleaned in SUBJECT_BY_CODE:
            names.append(SUBJECT_BY_CODE[cleaned]["name"])
        elif cleaned.upper() in SUBJECT_BY_CODE:
            names.append(SUBJECT_BY_CODE[cleaned.upper()]["name"])

    if names:
        return " + ".join(names)

    return raw_codes


def resolve_subject_details_from_timetable(date_value, time_value):
    if not date_value or not time_value:
        return {"name": "Subject Not Identified", "code": "N/A"}

    try:
        day_name = datetime.strptime(str(date_value), "%Y-%m-%d").strftime("%A")
    except ValueError:
        return {"name": "Subject Not Identified", "code": "N/A"}

    timetable_entries = TIMETABLE.get(day_name, [])
    if not timetable_entries:
        return {"name": "Subject Not Identified", "code": "N/A"}

    raw_time = str(time_value).strip()
    candidate_times = [raw_time]
    if raw_time.endswith(" AM") or raw_time.endswith(" PM"):
        candidate_times.append(raw_time.rsplit(" ", 1)[0])

    for candidate in candidate_times:
        current_minutes = schedule_time_to_minutes(candidate)
        if current_minutes is None:
            continue

        for time_range, label, code, kind in timetable_entries:
            if kind != "class":
                continue
            start, end = [part.strip() for part in time_range.split("-")]
            start_minutes = schedule_time_to_minutes(start)
            end_minutes = schedule_time_to_minutes(end)
            if start_minutes is None or end_minutes is None:
                continue
            if start_minutes <= current_minutes < end_minutes:
                code_value = code or "N/A"
                subject_name = subject_name_for_codes(code_value)
                if not subject_name or subject_name == "Unassigned":
                    subject_name = "Subject Not Identified"
                return {"name": subject_name, "code": code_value}

    return {"name": "Subject Not Identified", "code": "N/A"}


def resolve_subject_name_from_timetable(date_value, time_value):
    return resolve_subject_details_from_timetable(date_value, time_value)["name"]


def compute_summary(student_id, records):
    total_classes = 40
    present = len([record for record in records if record["status"] == "Present"])
    absent = total_classes - present
    percentage = round((present / total_classes) * 100, 1) if total_classes else 0.0
    student = get_student(student_id)
    return {
        "student": student,
        "total_classes": total_classes,
        "present": present,
        "absent": absent,
        "attendance": percentage,
    }


def get_admin_summary():
    conn = get_db_connection()
    total_students = conn.execute("SELECT COUNT(*) AS count FROM students").fetchone()["count"]
    today = datetime.now().strftime("%Y-%m-%d")
    legacy_present_today = conn.execute(
        "SELECT COUNT(*) AS count FROM attendance WHERE date = ? AND status = 'Present'",
        (today,),
    ).fetchone()["count"]
    session_present_today = conn.execute(
        "SELECT COUNT(*) AS count FROM attendance_sessions WHERE date = ? AND status = 'Present'",
        (today,),
    ).fetchone()["count"]
    present_today = legacy_present_today + session_present_today
    absent_today = max(total_students - min(present_today, total_students), 0)
    legacy_total_records = conn.execute("SELECT COUNT(*) AS count FROM attendance").fetchone()["count"]
    session_total_records = conn.execute("SELECT COUNT(*) AS count FROM attendance_sessions").fetchone()["count"]
    total_records = legacy_total_records + session_total_records
    percentage = round((present_today / total_students) * 100, 1) if total_students else 0.0
    conn.close()
    return {
        "total_students": total_students,
        "present_today": present_today,
        "absent_today": absent_today,
        "attendance_percentage": percentage,
        "total_records": total_records,
    }


def get_admin_records():
    conn = get_db_connection()
    legacy_rows = conn.execute(
        """
        SELECT a.id, s.name, s.roll_number, s.branch, a.date, a.time, a.sign_out_time, a.status, a.subject_code
        FROM attendance a
        JOIN students s ON s.id = a.student_id
        ORDER BY a.date DESC, a.time DESC
        """
    ).fetchall()
    session_rows = conn.execute(
        """
        SELECT a.id, s.name, s.roll_number, s.branch, a.date, a.time, a.sign_out_time, a.status, a.subject_code
        FROM attendance_sessions a
        JOIN students s ON s.id = a.student_id
        ORDER BY a.date DESC, a.time DESC
        """
    ).fetchall()
    conn.close()
    records = []
    for row in [*legacy_rows, *session_rows]:
        records.append(
            {
                "id": row["id"],
                "student": row["name"],
                "roll_number": row["roll_number"],
                "branch": row["branch"],
                "date": row["date"],
                "time": row["time"],
                "sign_out_time": row["sign_out_time"],
                "status": row["status"],
                "subject_code": row["subject_code"],
                "subject_name": subject_name_for_codes(row["subject_code"]),
            }
        )
    return sorted(records, key=lambda record: (record["date"], record["time"]), reverse=True)


def schedule_time_to_minutes(value):
    if value is None:
        return None

    raw_value = str(value).strip()
    for pattern in ("%I:%M %p", "%H:%M", "%I:%M"):
        try:
            parsed = datetime.strptime(raw_value, pattern)
            return parsed.hour * 60 + parsed.minute
        except ValueError:
            continue
    return None


def get_current_timetable_entry(now=None):
    now = now or datetime.now()
    day_entries = TIMETABLE.get(now.strftime("%A"), [])
    current_minutes = now.hour * 60 + now.minute
    for time_range, label, code, kind in day_entries:
        start, end = [part.strip() for part in time_range.split("-")]
        if schedule_time_to_minutes(start) <= current_minutes < schedule_time_to_minutes(end):
            return {
                "time": time_range,
                "label": label,
                "code": code or None,
                "kind": kind,
            }
    return None


def record_attendance(student_id, action, subject_code=None):
    conn = get_db_connection()
    today = datetime.now().strftime("%Y-%m-%d")
    current_time = datetime.now().strftime("%I:%M %p")
    active_session = conn.execute(
        "SELECT id, time, sign_out_time, subject_code FROM attendance_sessions WHERE student_id = ? AND date = ? AND sign_out_time IS NULL ORDER BY id DESC LIMIT 1",
        (student_id, today),
    ).fetchone()

    if action == "sign_out":
        if not active_session:
            legacy_session = conn.execute(
                "SELECT id, time, subject_code FROM attendance WHERE student_id = ? AND date = ? AND sign_out_time IS NULL ORDER BY id DESC LIMIT 1",
                (student_id, today),
            ).fetchone()
            if not legacy_session:
                conn.close()
                return {"success": False, "message": "Sign in before signing out."}
            conn.execute(
                "UPDATE attendance SET sign_out_time = ? WHERE id = ?",
                (current_time, legacy_session["id"]),
            )
            conn.commit()
            conn.close()
            return {
                "success": True,
                "message": "Signed out successfully.",
                "attendance_time": legacy_session["time"],
                "sign_out_time": current_time,
                "subject_code": legacy_session["subject_code"],
            }
        conn.execute(
            "UPDATE attendance_sessions SET sign_out_time = ? WHERE id = ?",
            (current_time, active_session["id"]),
        )
        conn.commit()
        conn.close()
        return {
            "success": True,
            "message": "Signed out successfully.",
            "attendance_time": active_session["time"],
            "sign_out_time": current_time,
            "subject_code": active_session["subject_code"],
        }

    conn.execute(
        """
        INSERT INTO attendance_sessions (student_id, date, time, status, recognition_method, subject_code)
        VALUES (?, ?, ?, 'Present', 'Face Recognition', ?)
        """,
        (student_id, today, current_time, subject_code),
    )
    conn.commit()
    conn.close()
    return {
        "success": True,
        "message": "Signed in successfully.",
        "action": "sign_in",
        "attendance_time": current_time,
        "sign_out_time": None,
        "subject_code": subject_code,
    }


@app.route("/")
def index():
    return render_template("login.html")


@app.route("/login")
def login():
    return render_template("login.html")


@app.route("/dashboard")
def dashboard_page():
    student_id = request.args.get("student_id", default=1, type=int)
    student = get_student(student_id)
    if not student:
        return render_template("login.html")
    records = get_student_attendance(student_id)
    summary = compute_summary(student_id, records)
    return render_template(
        "dashboard.html",
        student=student,
        attendance=records,
        summary=summary,
        college=COLLEGE_INFO,
        subjects=SUBJECTS,
        timetable=timetable_for_template(),
    )


@app.route("/student")
gdef student_page():
    student_id = request.args.get("student_id", default=1, type=int)
    student = get_student(student_id)
    if not student:
        return render_template("login.html")
    records = get_student_attendance(student_id)
    summary = compute_summary(student_id, records)
    return render_template(
        "student.html",
        student=student,
        attendance=records,
        summary=summary,
        college=COLLEGE_INFO,
    )


@app.route("/admin")
def admin_page():
    summary = get_admin_summary()
    records = get_admin_records()
    return render_template("admin.html", summary=summary, records=records)


@app.route("/register-student")
def register_student_page():
    return render_template("register_student.html")


@app.route("/api/register-student", methods=["POST"])
def api_register_student():
    try:
        data = request.get_json(force=True, silent=True) or {}
        name = (data.get("name") or "").strip()
        roll_number = (data.get("roll_number") or "").strip()
        enrollment_number = (data.get("enrollment_number") or "").strip()
        branch = (data.get("branch") or "").strip()
        year = (data.get("year") or "").strip()
        section = (data.get("section") or "").strip()

        if not all([name, roll_number, enrollment_number, branch, year, section]):
            return jsonify({"success": False, "message": "All student fields are required."}), 400

        conn = get_db_connection()
        existing = conn.execute(
            "SELECT id FROM students WHERE roll_number = ? OR enrollment_number = ?",
            (roll_number, enrollment_number),
        ).fetchone()
        if existing:
            conn.close()
            return jsonify({"success": False, "message": "Student with the same roll number or enrollment number already exists."}), 409

        cursor = conn.execute(
            """
            INSERT INTO students (name, roll_number, enrollment_number, branch, year, section, photo)
            VALUES (?, ?, ?, ?, ?, ?, '')
            """,
            (name, roll_number, enrollment_number, branch, year, section),
        )
        student_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return jsonify({"success": True, "student_id": student_id, "message": "Student registered successfully."}), 201
    except Exception:
        return jsonify({"success": False, "message": "Failed to register the student."}), 500


@app.route("/api/register-face", methods=["POST"])
def api_register_face():
    try:
        data = request.get_json(force=True, silent=True) or {}
        student_id = data.get("student_id")
        image_data = data.get("image_data")
        if not student_id:
            return jsonify({"success": False, "message": "Student ID is required."}), 400
        if not image_data:
            return jsonify({"success": False, "message": "Face image is required."}), 400

        image = decode_image_data(image_data)
        face_vector = extract_face_vector_from_image(image)
        vector_json = json.dumps(face_vector.tolist())

        conn = get_db_connection()
        student = conn.execute("SELECT id FROM students WHERE id = ?", (student_id,)).fetchone()
        if student is None:
            conn.close()
            return jsonify({"success": False, "message": "Student not found."}), 404

        saved_path = FACE_DIR / f"student_{student_id}.png"
        cv2.imwrite(str(saved_path), image)
        conn.execute(
            "UPDATE students SET photo = ?, face_vector = ? WHERE id = ?",
            (str(saved_path), vector_json, student_id),
        )
        conn.commit()
        conn.close()
        return jsonify({"success": True, "message": "Face Registration Successful."}), 200
    except ValueError as exc:
        return jsonify({"success": False, "message": str(exc)}), 400
    except Exception:
        return jsonify({"success": False, "message": "Face registration failed due to a server error."}), 500


@app.route("/api/recognize-face", methods=["POST"])
def api_recognize_face():
    try:
        data = request.get_json(force=True, silent=True) or {}
        image_data = data.get("image_data")
        action = data.get("action", "sign_in")
        if not image_data:
            return jsonify({"success": False, "message": "Face image is required."}), 400
        if action not in {"sign_in", "sign_out"}:
            return jsonify({"success": False, "message": "Invalid attendance action."}), 400

        image = decode_image_data(image_data)
        current_vector = extract_face_vector_from_image(image)
        conn = get_db_connection()
        students = conn.execute(
            "SELECT * FROM students WHERE face_vector IS NOT NULL AND face_vector != ''"
        ).fetchall()
        conn.close()

        if not students:
            return jsonify(
                {
                    "success": False,
                    "message": "No face is registered yet. Register the student face first.",
                }
            ), 404

        best_match = None
        best_distance = float("inf")
        for student in students:
            stored_vector = np.asarray(json.loads(student["face_vector"]), dtype=np.float32)
            distance = float(np.linalg.norm(current_vector - stored_vector))
            if distance < best_distance:
                best_distance = distance
                best_match = student

        if best_match is None or best_distance > 0.95:
            return jsonify(
                {
                    "success": False,
                    "message": "Student not recognized. Register this face first, then try again.",
                }
            ), 404

        student = student_row_to_dict(best_match)
        current_entry = get_current_timetable_entry()
        attendance_result = record_attendance(
            student["id"],
            action,
            current_entry["code"]
            if current_entry and current_entry["kind"] == "class"
            else None,
        )
        if not attendance_result["success"]:
            return jsonify(
                {
                    "success": False,
                    "message": attendance_result["message"],
                    "attendance_time": attendance_result.get("attendance_time"),
                    "sign_out_time": attendance_result.get("sign_out_time"),
                    "subject_code": attendance_result.get("subject_code"),
                    "student": student,
                }
            ), 409

        return jsonify(
            {
                "success": True,
                "message": attendance_result["message"],
                "student": student,
                "attendance": action,
                "action": action,
                "attendance_time": attendance_result["attendance_time"],
                "sign_out_time": attendance_result.get("sign_out_time"),
                "subject_code": attendance_result.get("subject_code"),
            }
        )
    except ValueError as exc:
        return jsonify({"success": False, "message": str(exc)}), 400
    except Exception:
        return jsonify({"success": False, "message": "Face recognition failed due to a server error."}), 500


@app.route("/api/student/<int:student_id>", methods=["GET"])
def api_student(student_id):
    student = get_student(student_id)
    if not student:
        return jsonify({"success": False, "message": "Student not found."}), 404
    attendance = get_student_attendance(student_id)
    summary = compute_summary(student_id, attendance)
    return jsonify({"success": True, "student": student, "attendance": attendance, "summary": summary})


@app.route("/api/attendance/<int:student_id>", methods=["GET"])
def api_attendance(student_id):
    records = get_student_attendance(student_id)
    return jsonify({"success": True, "attendance": records})


@app.route("/api/admin/attendance", methods=["GET"])
def api_admin_attendance():
    records = get_admin_records()
    summary = get_admin_summary()
    return jsonify({"success": True, "summary": summary, "attendance": records})


if __name__ == "__main__":
    init_db()
    ensure_demo_data()
    app.run(host="0.0.0.0", port=5001, debug=True)
