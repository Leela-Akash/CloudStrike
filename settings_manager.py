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
    conn.execute("""
        CREATE TABLE IF NOT EXISTS scan_history (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            scan_date TEXT,
            total     INTEGER,
            critical  INTEGER,
            high      INTEGER,
            medium    INTEGER,
            low       INTEGER
        )
    """)
    conn.commit()
    conn.close()

def record_scan(findings_count, critical, high, medium, low):
    """Called after every scan to record results"""
    init_settings_db()
    conn = sqlite3.connect(DB_PATH)
    from datetime import datetime
    conn.execute(
        "INSERT INTO scan_history (scan_date, total, critical, high, medium, low) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (
            datetime.now().strftime('%Y-%m-%d'),
            findings_count, critical, high, medium, low
        )
    )
    conn.commit()
    conn.close()

def get_scan_history_7days():
    """Returns last 7 days of scan data for chart"""
    init_settings_db()
    from datetime import datetime, timedelta
    try:
        conn = sqlite3.connect(DB_PATH)
        rows = conn.execute("""
            SELECT scan_date, 
                   SUM(total)    as total,
                   SUM(critical) as critical,
                   SUM(high)     as high,
                   SUM(medium)   as medium
            FROM scan_history
            WHERE scan_date >= date('now', '-7 days')
            GROUP BY scan_date
            ORDER BY scan_date ASC
        """).fetchall()
        conn.close()

        # Build 7 day structure
        result = {}
        for i in range(7):
            day = (datetime.now() - timedelta(days=6-i)).strftime('%Y-%m-%d')
            result[day] = {
                'total': 0, 'critical': 0,
                'high': 0, 'medium': 0
            }
        for row in rows:
            if row[0] in result:
                result[row[0]] = {
                    'total':    row[1] or 0,
                    'critical': row[2] or 0,
                    'high':     row[3] or 0,
                    'medium':   row[4] or 0
                }
        return result
    except:
        return {}

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
