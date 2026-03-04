import sqlite3
from datetime import datetime

class DB:
    def __init__(self, dbfilename):
        self.dbfilename = dbfilename
        self.connection = sqlite3.connect(dbfilename)
        self.connection.row_factory = sqlite3.Row
        self.cursor = self.connection.cursor()
    
    def create_user(self, email):
        try:
            self.cursor.execute("INSERT INTO users (email) VALUES (?)", [email])
            self.connection.commit()
        except sqlite3.IntegrityError:
            print(f"Email {email} already exists")
            return None
        
    def create_account(self, username, email, user_id):
        self.cursor.execute("INSERT INTO accounts (username, email, user_id) VALUES (?, ?, ?)", [username, email, user_id])
        self.connection.commit()
        
    def post(self, username, content):
        timestamp = datetime.now().isoformat()
        self.cursor.execute("INSERT INTO post (username, timestamp, content) VALUES (?, ?, ?)", [username, timestamp, content])
        self.connection.commit()
        
    def delete_post(self, id, username):
        self.cursor.execute("DELETE FROM likes WHERE post_id=?", [id])
        self.cursor.execute("DELETE FROM post WHERE id=? AND username=?", [id, username])
        self.connection.commit()
        
    def like_post(self, id, username):
        self.cursor.execute("INSERT OR IGNORE INTO likes (username, post_id) VALUES (?, ?)", [username, id])
        self.connection.commit()
        
    def unlike_post(self, id, username):
        self.cursor.execute("DELETE FROM likes WHERE post_id=? AND username=?", [id, username])
        self.connection.commit()
        
    def get_all_posts(self):
        self.cursor.execute("SELECT * FROM post")
        return [dict(row) for row in self.cursor.fetchall()]
    
    def get_feed(self, username):
        self.cursor.execute("SELECT post.id, post.username, post.timestamp, post.content FROM post JOIN follows ON post.username = follows.following WHERE follows.follower=?", [username])
        return [dict(row) for row in self.cursor.fetchall()]
    
    def follow(self, user_follower, user_following):
        if user_follower == user_following:
            return None
        self.cursor.execute("INSERT INTO follows (follower, following) VALUES (?, ?)", [user_follower, user_following])
        self.connection.commit()
        
    def unfollow(self, user_follower, user_following):
        self.cursor.execute("DELETE FROM follows WHERE follower=? AND following=?", [user_follower, user_following])
        self.connection.commit()

    def close(self):
        self.connection.close()
        