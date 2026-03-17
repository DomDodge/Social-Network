import shutil
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "database.db"
BACKUP = DB_PATH.with_suffix(".db.bak")

print("Backing up", DB_PATH, "->", BACKUP)
shutil.copy2(DB_PATH, BACKUP)

def primary_key_column(cur, table):
    cur.execute(f"PRAGMA table_info({table})")
    cols = [r[1] for r in cur.fetchall()]  # PRAGMA returns rows where name is at index 1
    return "id" if "id" in cols else "rowid"

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

try:
    # Likes
    pk = primary_key_column(cur, "likes")
    print(f"Cleaning duplicate likes using {pk} (keep lowest)...")
    cur.execute(f"""
        DELETE FROM likes
        WHERE {pk} NOT IN (
            SELECT MIN({pk}) FROM likes GROUP BY username, post_id
        )
    """)

    # Follows
    pk = primary_key_column(cur, "follows")
    print(f"Cleaning duplicate follows using {pk} (keep lowest)...")
    cur.execute(f"""
        DELETE FROM follows
        WHERE {pk} NOT IN (
            SELECT MIN({pk}) FROM follows GROUP BY follower, following
        )
    """)

    # Accounts
    pk = primary_key_column(cur, "accounts")
    print(f"Cleaning duplicate accounts using {pk} (keep lowest)...")
    cur.execute(f"""
        DELETE FROM accounts
        WHERE {pk} NOT IN (
            SELECT MIN({pk}) FROM accounts GROUP BY username
        )
    """)

    conn.commit()

    print("Creating unique indexes (if not exists)...")
    cur.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_accounts_username ON accounts(username)")
    cur.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_likes_unique ON likes(username, post_id)")
    cur.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_follows_unique ON follows(follower, following)")
    conn.commit()

    print("Migration completed successfully.")
except Exception as e:
    conn.rollback()
    print("ERROR during migration:", e)
finally:
    conn.close()