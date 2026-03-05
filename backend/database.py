# ...existing code...
import sqlite3
from datetime import datetime

class DB:
    def __init__(self, dbfilename):
        self.dbfilename = dbfilename

    def _conn(self):
        # create a new connection for each call so SQLite objects aren't shared across threads
        conn = sqlite3.connect(self.dbfilename, check_same_thread=False)
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
        with self._conn() as conn:
            cur = conn.cursor()
            cur.execute("INSERT INTO accounts (username, email, user_id) VALUES (?, ?, ?)",
                        (username, email, user_id))

    def post(self, username, content):
        timestamp = datetime.now().isoformat()
        with self._conn() as conn:
            cur = conn.cursor()
            cur.execute("INSERT INTO post (username, timestamp, content) VALUES (?, ?, ?)",
                        (username, timestamp, content))

    def delete_post(self, id, username):
        with self._conn() as conn:
            cur = conn.cursor()
            cur.execute("DELETE FROM likes WHERE post_id=?", (id,))
            cur.execute("DELETE FROM post WHERE id=? AND username=?", (id, username))

    def like_post(self, id, username):
        with self._conn() as conn:
            cur = conn.cursor()
            cur.execute("INSERT OR IGNORE INTO likes (username, post_id) VALUES (?, ?)", (username, id))

    def unlike_post(self, id, username):
        with self._conn() as conn:
            cur = conn.cursor()
            cur.execute("DELETE FROM likes WHERE post_id=? AND username=?", (id, username))

    def get_all_posts(self):
        with self._conn() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM post")
            return [dict(row) for row in cur.fetchall()]

    def get_feed(self, username):
        with self._conn() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT post.id, post.username, post.timestamp, post.content "
                "FROM post JOIN follows ON post.username = follows.following "
                "WHERE follows.follower=? ORDER BY post.timestamp DESC",
                (username,)
            )
            return [dict(row) for row in cur.fetchall()]

    def follow(self, user_follower, user_following):
        if user_follower == user_following:
            return None
        with self._conn() as conn:
            cur = conn.cursor()
            cur.execute("INSERT OR IGNORE INTO follows (follower, following) VALUES (?, ?)",
                        (user_follower, user_following))

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
# ...existing code...