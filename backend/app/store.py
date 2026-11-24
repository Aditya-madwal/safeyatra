"""
Small SQLite database for the things users and admins create:
blockage reports, road closures and admin settings (GSI alert, rain scenario).
"""

import json
import sqlite3
from datetime import date, datetime, timedelta, timezone

from . import config

SCHEMA = """
CREATE TABLE IF NOT EXISTS reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    user_name TEXT,
    type TEXT NOT NULL,            -- landslide / debris / road_blocked / flooding / other
    description TEXT,
    lat REAL NOT NULL, lon REAL NOT NULL,
    segment_id TEXT,               -- nearest road segment
    photo TEXT,                    -- file name in storage/uploads
    status TEXT NOT NULL DEFAULT 'pending',   -- pending / verified / rejected
    created_at TEXT NOT NULL,
    reviewed_by TEXT, reviewed_at TEXT
);
CREATE TABLE IF NOT EXISTS closures (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    reason TEXT,
    segment_ids TEXT NOT NULL,     -- JSON list
    start_date TEXT,               -- YYYY-MM-DD, empty = from now
    end_date TEXT,                 -- YYYY-MM-DD, empty = until removed
    source TEXT NOT NULL DEFAULT 'admin',     -- admin / report / sample
    report_id INTEGER,
    created_by TEXT, created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT);
"""

REPORT_TYPES = ["landslide", "debris", "road_blocked", "flooding", "other"]
UNVERIFIED_REPORT_HOURS = 6     # pending reports add risk for this long


def now_iso():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class Store:
    def __init__(self, path=None):
        config.STORAGE_DIR.mkdir(parents=True, exist_ok=True)
        config.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(path or config.DB_PATH, check_same_thread=False)
        self.db.row_factory = sqlite3.Row
        self.db.executescript(SCHEMA)
        self.db.commit()

    # ---- settings ----
    def get_setting(self, key, default=None):
        row = self.db.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
        return row["value"] if row else default

    def set_setting(self, key, value):
        self.db.execute("INSERT INTO settings(key, value) VALUES(?, ?) "
                        "ON CONFLICT(key) DO UPDATE SET value = excluded.value", (key, value))
        self.db.commit()

    # ---- reports ----
    def add_report(self, **r):
        cur = self.db.execute(
            "INSERT INTO reports(user_id, user_name, type, description, lat, lon, segment_id,"
            " photo, created_at) VALUES(?,?,?,?,?,?,?,?,?)",
            (r["user_id"], r.get("user_name"), r["type"], r.get("description"), r["lat"],
             r["lon"], r.get("segment_id"), r.get("photo"), now_iso()))
        self.db.commit()
        return self.get_report(cur.lastrowid)

    def get_report(self, report_id):
        row = self.db.execute("SELECT * FROM reports WHERE id = ?", (report_id,)).fetchone()
        return dict(row) if row else None

    def list_reports(self, status=None, user_id=None):
        sql, args = "SELECT * FROM reports WHERE 1=1", []
        if status:
            sql, args = sql + " AND status = ?", args + [status]
        if user_id:
            sql, args = sql + " AND user_id = ?", args + [user_id]
        return [dict(r) for r in self.db.execute(sql + " ORDER BY id DESC", args)]

    def set_report_status(self, report_id, status, reviewer):
        self.db.execute("UPDATE reports SET status = ?, reviewed_by = ?, reviewed_at = ? "
                        "WHERE id = ?", (status, reviewer, now_iso(), report_id))
        self.db.commit()
        return self.get_report(report_id)

    def report_penalties(self):
        """{segment_id: penalty} for pending reports younger than 6 hours."""
        since = (datetime.now(timezone.utc) - timedelta(hours=UNVERIFIED_REPORT_HOURS)) \
            .isoformat(timespec="seconds")
        rows = self.db.execute("SELECT segment_id FROM reports WHERE status = 'pending' "
                               "AND created_at >= ? AND segment_id IS NOT NULL", (since,))
        return {r["segment_id"]: 0.3 for r in rows}

    # ---- closures ----
    def add_closure(self, **c):
        cur = self.db.execute(
            "INSERT INTO closures(name, reason, segment_ids, start_date, end_date, source,"
            " report_id, created_by, created_at) VALUES(?,?,?,?,?,?,?,?,?)",
            (c["name"], c.get("reason"), json.dumps(c["segment_ids"]), c.get("start_date"),
             c.get("end_date"), c.get("source", "admin"), c.get("report_id"),
             c.get("created_by"), now_iso()))
        self.db.commit()
        return self.get_closure(cur.lastrowid)

    def get_closure(self, closure_id):
        row = self.db.execute("SELECT * FROM closures WHERE id = ?", (closure_id,)).fetchone()
        return self._closure(row) if row else None

    def list_closures(self):
        rows = self.db.execute("SELECT * FROM closures ORDER BY id DESC")
        return [self._closure(r) for r in rows]

    def delete_closure(self, closure_id):
        self.db.execute("DELETE FROM closures WHERE id = ?", (closure_id,))
        self.db.commit()

    def count_closures(self):
        return self.db.execute("SELECT COUNT(*) FROM closures").fetchone()[0]

    @staticmethod
    def _closure(row):
        c = dict(row)
        c["segment_ids"] = json.loads(c["segment_ids"])
        c["active"] = closure_active(c)
        return c

    def closed_segment_ids(self):
        ids = set()
        for c in self.list_closures():
            if c["active"]:
                ids.update(c["segment_ids"])
        return ids


def closure_active(c, today=None):
    """A closure is active between its start and end dates (both optional).
    Seasonal closures that wrap the new year (e.g. 15 Nov - 30 Apr) work too."""
    today = today or date.today().isoformat()
    start, end = c.get("start_date") or "", c.get("end_date") or ""
    if start and end and start > end:          # wraps over the new year
        return today >= start or today <= end
    return (not start or today >= start) and (not end or today <= end)
