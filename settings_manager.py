import sqlite3
import json
import os

DB_PATH = "cloudstrike_settings.db"

def init_settings_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    """)
    conn.commit()
    conn.close()

def save_setting(key, value):
    init_settings_db()
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
        (key, json.dumps(value))
    )
    conn.commit()
    conn.close()

def get_setting(key, default=None):
    init_settings_db()
    try:
        conn = sqlite3.connect(DB_PATH)
        row = conn.execute(
            "SELECT value FROM settings WHERE key=?", (key,)
        ).fetchone()
        conn.close()
        if row:
            return json.loads(row[0])
        return default
    except:
        return default

def get_all_settings():
    return {
        'scan_depth':        get_setting('scan_depth', 'Standard (15 min)'),
        'regions':           get_setting('regions', ['us-east-1','eu-west-1','ap-south-1','us-west-2']),
        'notify_critical':   get_setting('notify_critical', True),
        'notify_high':       get_setting('notify_high', True),
        'notify_scan_done':  get_setting('notify_scan_done', True),
        'auto_pdf':          get_setting('auto_pdf', False),
        'include_low':       get_setting('include_low', False),
    }
