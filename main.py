import psutil
import sqlite3
import time
from datetime import datetime
from pathlib import Path

# =========================
# ✅ Threshold constants (can be adjusted)
# =========================
CPU_THRESHOLD = 1.0      # > 80% on real mode (1.0 for auto alert test mode)
MEM_THRESHOLD = 1.0      # > 85% on real mode
DISK_THRESHOLD = 1.0     # > 90% on real mode

DB_PATH = Path("log.db")

# =========================
# ✅ Database Initialization
# =========================
def init_db(db_path: Path) -> sqlite3.Connection:
    """Create DB and tables if not exist, then return connection."""
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    # Week 7 table (system logs)
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

    # Week 8 Bonus table (alert history)
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

# =========================
# ✅ Insert records into tables
# =========================
def insert_system_log(conn, ts, cpu, mem, disk, status):
    conn.execute(
        "INSERT INTO system_log (ts, cpu, memory, disk, status) VALUES (?, ?, ?, ?, ?)",
        (ts, cpu, mem, disk, status),
    )
    conn.commit()

def insert_alert(conn, ts, level, message):
    conn.execute(
        "INSERT INTO alerts_log (ts, level, message) VALUES (?, ?, ?)",
        (ts, level, message),
    )
    conn.commit()

# =========================
# ✅ System metric reader
# =========================
def read_system_metrics():
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cpu = psutil.cpu_percent(interval=1)          # 1 sec sampling
    mem = psutil.virtual_memory().percent
    disk = psutil.disk_usage("/").percent
    status = "UP"
    return ts, cpu, mem, disk, status

# =========================
# ✅ Alert checker
# =========================
def check_alerts(cpu, mem, disk):
    alerts = []
    if cpu > CPU_THRESHOLD:
        alerts.append(f"High CPU usage! ({cpu:.1f}%)")
    if mem > MEM_THRESHOLD:
        alerts.append(f"High Memory usage! ({mem:.1f}%)")
    if disk > DISK_THRESHOLD:
        alerts.append(f"Low Disk Space! ({disk:.1f}%)")
    return alerts

# =========================
# ✅ Main loop
# =========================
def main():
    conn = init_db(DB_PATH)
    entries = 5                       # Log 5 entries (as required)
    interval_sec = 10                 # 10 seconds interval

    print("Starting Week 8 monitor (threshold alerts). Press Ctrl+C to stop.\n")
    try:
        for i in range(1, entries + 1):
            ts, cpu, mem, disk, status = read_system_metrics()
            insert_system_log(conn, ts, cpu, mem, disk, status)

            print(f"Logged: ('{ts}', {cpu:.1f}, {mem:.1f}, {disk:.1f}, '{status}')", end="")

            alerts = check_alerts(cpu, mem, disk)
            if alerts:
                for msg in alerts:
                    print(f" ⚠️ ALERT: {msg}", end="")
                    insert_alert(conn, ts, "WARNING", msg)  # save alert in table

            print()

            if i < entries:
                time.sleep(interval_sec)

    except KeyboardInterrupt:
        print("\nInterrupted by user.")

    finally:
        conn.close()
        print("\nDone. Records saved to log.db ✅")

if __name__ == "__main__":
    main()
