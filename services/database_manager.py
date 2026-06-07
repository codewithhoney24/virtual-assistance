import sqlite3
import json
import os

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'nexushealth.db')

def init_db():
    """Initializes the SQLite database schema."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS appointments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_name TEXT NOT NULL,
            patient_age INTEGER,
            patient_email TEXT,
            patient_phone TEXT,
            doctor_name TEXT NOT NULL,
            specialization TEXT,
            appointment_date TEXT NOT NULL,
            appointment_time TEXT NOT NULL,
            symptoms TEXT,
            triage_json TEXT,
            completed BOOLEAN DEFAULT 0,
            prescription_json TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def add_appointment(data: dict):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO appointments 
        (patient_name, patient_age, patient_email, patient_phone, doctor_name, specialization, appointment_date, appointment_time, symptoms, triage_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        data['patient_name'], data.get('patient_age'), data.get('patient_email'), data.get('patient_phone'),
        data['doctor_name'], data.get('specialization'), data['appointment_date'], data['appointment_time'],
        data.get('symptoms'), json.dumps(data.get('triage_result'))
    ))
    conn.commit()
    conn.close()

def get_all_appointments():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM appointments ORDER BY created_at DESC')
    rows = cursor.fetchall()
    
    # Convert to list of dicts for Streamlit compatibility
    appointments = []
    for row in rows:
        d = dict(row)
        d['triage_result'] = json.loads(d['triage_json']) if d['triage_json'] else {}
        d['prescription'] = json.loads(d['prescription_json']) if d['prescription_json'] else None
        appointments.append(d)
    
    conn.close()
    return appointments

def update_appointment_status(appt_id: int, completed: bool, prescription: dict = None):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    if prescription:
        cursor.execute('UPDATE appointments SET completed = ?, prescription_json = ? WHERE id = ?', 
                       (1 if completed else 0, json.dumps(prescription), appt_id))
    else:
        cursor.execute('UPDATE appointments SET completed = ? WHERE id = ?', (1 if completed else 0, appt_id))
    conn.commit()
    conn.close()

def delete_appointment(appt_id: int):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM appointments WHERE id = ?', (appt_id,))
    conn.commit()
    conn.close()

def check_availability(doctor_name: str, date: str) -> bool:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM appointments WHERE doctor_name = ? AND appointment_date = ?', (doctor_name, date))
    count = cursor.fetchone()[0]
    conn.close()
    return count == 0 # True if free