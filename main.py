import psutil
import sqlite3
import time
from datetime import datetime
from pathlib import Path

# =========================
# Threshold constants (spec)
# =========================
CPU_THRESHOLD = 1.0
MEM_THRESHOLD = 1.0
DISK_THRESHOLD = 1.0

DB_PATH = Path("log.db")

# =========================
# Database helpers
# =========================
def init_db(db_path: Path) -> sqlite3.Connection:
    """Create DB and tables if not exist, then return connection."""
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    # Week 7 system_log table (re-use)
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS system_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ts TEXT NOT NULL,
            cpu REAL NOT NULL,
            memory REAL NOT NULL,
            disk REAL NOT NULL,
            status TEXT NOT NULL
        )
        """
    )
    # Bonus: separate table for alerts history
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS alerts_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ts TEXT NOT NULL,
            level TEXT NOT NULL,
            message TEXT NOT NULL
        )
        """
    )
    conn.commit()
    return conn

def insert_system_log(conn: sqlite3.Connection, ts: str, cpu: float, mem: float, disk: float, status: str):
    conn.execute(
        "INSERT INTO system_log (ts, cpu, memory, disk, status) VALUES (?, ?, ?, ?, ?)",
        (ts, cpu, mem, disk, status),
    )
    conn.commit()

def insert_alert(conn: sqlite3.Connection, ts: str, level: str, message: str):
    conn.execute(
        "INSERT INTO alerts_log (ts, level, message) VALUES (?, ?, ?)",
        (ts, level, message),
    )
    conn.commit()

# =========================
# Monitoring helpers
# =========================
def read_system_metrics():
    """
    Read current CPU, Memory, Disk in percent.
    cpu_percent(interval=1) blocks 1s for accurate CPU sample.
    """
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cpu = float(psutil.cpu_percent(interval=1))
    mem = float(psutil.virtual_memory().percent)
    disk = float(psutil.disk_usage("/").percent)
    status = "UP"  # simple heartbeat flag
    return ts, cpu, mem, disk, status

def check_alerts(cpu: float, mem: float, disk: float):
    """
    Return list of alert messages if any threshold is exceeded.
    """
    alerts = []
    if cpu > CPU_THRESHOLD:
        alerts.append(f"High CPU usage! ({cpu:.1f}%)")
    if mem > MEM_THRESHOLD:
        alerts.append(f"High Memory usage! ({mem:.1f}%)")
    if disk > DISK_THRESHOLD:
        alerts.append(f"Low Disk Space! ({disk:.1f}%)")
    return alerts

# =========================
# Main loop
# =========================
def main():
    conn = init_db(DB_PATH)

    entries = 5          # spec: log 5 entries
    interval_sec = 10    # spec: 10 seconds between records

    print("Starting Week 8 monitor (threshold alerts). Press Ctrl+C to stop.\n")
    try:
        for i in range(1, entries + 1):
            ts, cpu, mem, disk, status = read_system_metrics()
            insert_system_log(conn, ts, cpu, mem, disk, status)

            # Print the logged line (similar to spec example)
            print(f"Logged: ('{ts}', {cpu:.1f}, {mem:.1f}, {disk:.1f}, '{status}')", end="")

            # Check & print alerts (only when exceeded)
            alerts = check_alerts(cpu, mem, disk)
            if alerts:
                for msg in alerts:
                    print(f" ⚠️ ALERT: {msg}", end="")
                    # bonus: store alerts to a separate table
                    insert_alert(conn, ts, "WARNING", msg)
            print()  # newline

            # sleep between records except after the last one
            if i < entries:
                time.sleep(interval_sec)

    except KeyboardInterrupt:
        print("\nInterrupted by user.")
    finally:
        conn.close()
        print("\nDone. Records saved to log.db")

if __name__ == "__main__":
    main()