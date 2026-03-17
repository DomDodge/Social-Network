import sqlite3
from datetime import datetime

class DB:
    def __init__(self, dbfilename):
        self.dbfilename = dbfilename
        # ensure schema + unique indexes; remove duplicates if present
        with self._conn() as conn:
            cur = conn.cursor()

            # create tables if they don't exist (no-op if they do)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY,
                    email TEXT UNIQUE NOT NULL
                )""")
            cur.execute("""
                CREATE TABLE IF NOT EXISTS accounts (
                    id INTEGER PRIMARY KEY,
                    username TEXT UNIQUE NOT NULL,
                    email TEXT NOT NULL,
                    user_id INTEGER
                )""")
            cur.execute("""
                CREATE TABLE IF NOT EXISTS post (
                    id INTEGER PRIMARY KEY,
                    username TEXT NOT NULL,
                    timestamp TEXT,
                    content TEXT
                )""")
            cur.execute("""
                CREATE TABLE IF NOT EXISTS likes (
                    id INTEGER PRIMARY KEY,
                    username TEXT NOT NULL,
                    post_id INTEGER NOT NULL
                )""")
            cur.execute("""
                CREATE TABLE IF NOT EXISTS follows (
                    id INTEGER PRIMARY KEY,
                    follower TEXT NOT NULL,
                    following TEXT NOT NULL
                )""")
            conn.commit()

            # helper to choose primary key column (id if present, otherwise rowid)
            def primary_key_column(cur, table):
                cur.execute(f"PRAGMA table_info({table})")
                cols = [r[1] for r in cur.fetchall()]
                return "id" if "id" in cols else "rowid"

            # remove duplicates (keep the lowest pk / rowid) before creating unique indexes
            try:
                for table, group_cols in [
                    ("likes", "username, post_id"),
                    ("follows", "follower, following"),
                    ("accounts", "username")
                ]:
                    pk = primary_key_column(cur, table)
                    cur.execute(f"""
                        DELETE FROM {table}
                        WHERE {pk} NOT IN (
                            SELECT MIN({pk}) FROM {table} GROUP BY {group_cols}
                        )
                    """)
                conn.commit()
            except Exception:
                # if table doesn't exist or other issue, continue to index creation attempt
                conn.rollback()

            # create unique indexes (duplicates should be gone); wrap to handle any remaining integrity issues
            try:
                cur.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_accounts_username ON accounts(username)")
                cur.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_likes_unique ON likes(username, post_id)")
                cur.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_follows_unique ON follows(follower, following)")
                conn.commit()
            except sqlite3.IntegrityError:
                # last-resort: try dedupe again then retry creating indexes
                conn.rollback()
                for table, group_cols in [
                    ("likes", "username, post_id"),
                    ("follows", "follower, following"),
                    ("accounts", "username")
                ]:
                    pk = primary_key_column(cur, table)
                    cur.execute(f"""
                        DELETE FROM {table}
                        WHERE {pk} NOT IN (
                            SELECT MIN({pk}) FROM {table} GROUP BY {group_cols}
                        )
                    """)
                conn.commit()
                cur.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_accounts_username ON accounts(username)")
                cur.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_likes_unique ON likes(username, post_id)")
                cur.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_follows_unique ON follows(follower, following)")
                conn.commit()

    def _conn(self):
        conn = sqlite3.connect(self.dbfilename)
        conn.row_factory = sqlite3.Row
        return conn

    def create_user(self, email):
        try:
            with self._conn() as conn:
                cur = conn.cursor()
                cur.execute("INSERT INTO users (email) VALUES (?)", (email,))
                return cur.lastrowid
        except sqlite3.IntegrityError:
            return None

    def create_account(self, username, email, user_id):
        # return True if created, False if username already exists
        with self._conn() as conn:
            cur = conn.cursor()
            cur.execute("SELECT 1 FROM accounts WHERE username=?", (username,))
            if cur.fetchone():
                return False
            try:
                cur.execute("INSERT INTO accounts (username, email, user_id) VALUES (?, ?, ?)",
                            (username, email, user_id))
                return True
            except sqlite3.IntegrityError:
                return False

    def post(self, username, content):
        timestamp = datetime.now().isoformat()
        with self._conn() as conn:
            cur = conn.cursor()
            cur.execute("INSERT INTO post (username, timestamp, content) VALUES (?, ?, ?)",
                        (username, timestamp, content))

    def like_post(self, id, username):
        # return True if like added, False if already liked
        with self._conn() as conn:
            cur = conn.cursor()
            cur.execute("SELECT 1 FROM likes WHERE username=? AND post_id=?", (username, id))
            if cur.fetchone():
                return False
            try:
                cur.execute("INSERT INTO likes (username, post_id) VALUES (?, ?)", (username, id))
                return True
            except sqlite3.IntegrityError:
                return False

    def unlike_post(self, id, username):
        with self._conn() as conn:
            cur = conn.cursor()
            cur.execute("DELETE FROM likes WHERE post_id=? AND username=?", (id, username))

    def get_most_liked_posts_from_following(self, username):
        with self._conn() as conn:
            cur = conn.cursor()
            cur.execute("SELECT p.id, p.timestamp, p.username, content, COUNT(l.username) AS likes FROM follows AS f JOIN likes AS l ON l.username = f.following JOIN post AS p ON p.id = l.post_id WHERE follower=? AND p.username NOT IN (SELECT following FROM follows WHERE follower=?) AND follower != p.username GROUP BY content", (username, username))
            posts = [dict(row) for row in cur.fetchall()]
            
            for post in posts:
                cur.execute("SELECT username FROM likes WHERE post_id=?", (post['id'],))
                post['likes'] = [row['username'] for row in cur.fetchall()]
                
            return posts

    def get_all_posts(self):
        with self._conn() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM post ORDER BY timestamp DESC")
            rows = [dict(r) for r in cur.fetchall()]
            # attach likes to each post for frontend convenience
            for p in rows:
                cur.execute("SELECT username FROM likes WHERE post_id=?", (p['id'],))
                p['likes'] = [r['username'] for r in cur.fetchall()]
            return rows

    def get_feed(self, username):
        with self._conn() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT post.id, post.username, post.timestamp, post.content "
                "FROM post JOIN follows ON post.username = follows.following "
                "WHERE follows.follower=? ORDER BY post.timestamp DESC",
                (username,)
            )
            rows = [dict(r) for r in cur.fetchall()]
            for p in rows:
                cur.execute("SELECT username FROM likes WHERE post_id=?", (p['id'],))
                p['likes'] = [r['username'] for r in cur.fetchall()]
            return rows

    def follow(self, user_follower, user_following):
        # return True if followed, False if already following or same user
        if user_follower == user_following:
            return False
        with self._conn() as conn:
            cur = conn.cursor()
            cur.execute("SELECT 1 FROM follows WHERE follower=? AND following=?", (user_follower, user_following))
            if cur.fetchone():
                return False
            try:
                cur.execute("INSERT INTO follows (follower, following) VALUES (?, ?)",
                            (user_follower, user_following))
                return True
            except sqlite3.IntegrityError:
                return False

    def unfollow(self, user_follower, user_following):
        with self._conn() as conn:
            cur = conn.cursor()
            cur.execute("DELETE FROM follows WHERE follower=? AND following=?", (user_follower, user_following))

    # helper methods
    def get_user_by_email(self, email):
        with self._conn() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM users WHERE email=?", (email,))
            row = cur.fetchone()
            return dict(row) if row else None

    def get_account_by_username(self, username):
        with self._conn() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM accounts WHERE username=?", (username,))
            row = cur.fetchone()
            return dict(row) if row else None

    def get_post_by_id(self, post_id):
        with self._conn() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM post WHERE id=?", (post_id,))
            row = cur.fetchone()
            return dict(row) if row else None

    def get_likes_for_post(self, post_id):
        with self._conn() as conn:
            cur = conn.cursor()
            cur.execute("SELECT username FROM likes WHERE post_id=?", (post_id,))
            return [r['username'] for r in cur.fetchall()]
        
    def get_comments_for_post(self, post_id):
        with self._conn() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM comments WHERE post_id=? ORDER BY timestamp ASC", (post_id,))
            return [dict(row) for row in cur.fetchall()]