import sqlite3


def create_db():
    conn = sqlite3.connect('interface/database/students_feedback.db')
    cursor = conn.cursor()

    cursor.execute("""CREATE TABLE IF NOT EXISTS teachers (
    user_id INTEGER,
    first_name TEXT,
    last_name TEXT,
    educational_institution TEXT
    )""")
    conn.commit()

    cursor.execute("""CREATE TABLE IF NOT EXISTS students (
        user_id INTEGER,
        first_name TEXT,
        last_name TEXT,
        educational_institution TEXT,
        group_name TEXT
        )""")
    conn.commit()

    cursor.execute("""CREATE TABLE IF NOT EXISTS lectures (
            lecture_id INTEGER PRIMARY KEY AUTOINCREMENT,
            lecture_name TEXT,
            teacher_id INTEGER,
            group_name TEXT,
            lecture_form TEXT,
            evaluation_lecture_sum INTEGER,
            evaluation_lecture_count INTEGER,
            reviews TEXT
            )""")
    conn.commit()

    conn.close()
