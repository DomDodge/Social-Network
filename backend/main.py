# ...existing code...
from flask import Flask, request, jsonify
from flask_cors import CORS
from database import DB

app = Flask(__name__)
CORS(app)
db = DB("database.db")

@app.route('/signup', methods=['POST'])
def signup():
    data = request.get_json() or {}
    username = data.get('username')
    email = data.get('email')
    
    if not username or not email:
        return jsonify({'error': 'username and email required'}), 400

    user_id = db.create_user(email)
    if user_id is None:
        return jsonify({'error': 'email already exists'}), 409

    # Check if the username creation succeeded
    account_created = db.create_account(username, email, user_id)
    if not account_created:
        return jsonify({'error': 'username already taken'}), 409

    return jsonify({'status': 'ok', 'user_id': user_id, 'username': username, 'email': email})

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json() or {}
    username = data.get('username')
    if not username:
        return jsonify({'error': 'username required'}), 400

    # look up account by username (DB helper returns dict or None)
    account = db.get_account_by_username(username)
    if not account:
        return jsonify({'error': 'user not found'}), 404

    return jsonify({'status': 'ok', 'account': account})

@app.route('/posts', methods=['GET'])
def list_posts():
    return jsonify(db.get_all_posts())

@app.route('/posts', methods=['POST'])
def create_post():
    data = request.get_json() or {}
    username = data.get('username')
    content = data.get('content')
    if not username or not content:
        return jsonify({'error': 'username and content required'}), 400

    db.post(username, content)
    return jsonify({'status': 'ok'})

@app.route('/posts/<int:post_id>/like', methods=['POST', 'DELETE'])
def like_unlike(post_id):
    data = request.get_json() or {}
    username = data.get('username')
    if not username:
        return jsonify({'error': 'username required'}), 400

    if request.method == 'POST':
        db.like_post(post_id, username)
        return jsonify({'status': 'liked'})
    else:
        db.unlike_post(post_id, username)
        return jsonify({'status': 'unliked'})

@app.route('/feed/<username>', methods=['GET'])
def feed(username):
    return jsonify(db.get_feed(username))

@app.route('/follow', methods=['POST', 'DELETE'])
def follow_unfollow():
    data = request.get_json() or {}
    follower = data.get('follower')
    following = data.get('following')
    if not follower or not following:
        return jsonify({'error': 'follower and following required'}), 400

    if request.method == 'POST':
        db.follow(follower, following)
        return jsonify({'status': 'followed'})
    else:
        db.unfollow(follower, following)
        return jsonify({'status': 'unfollowed'})
    
@app.route('/posts/<int:post_id>/comments', methods=['GET', 'POST'])
def handle_comments(post_id):
    if request.method == 'POST':
        data = request.get_json() or {}
        username = data.get('username')
        content = data.get('content')
        
        if not username or not content:
            return jsonify({'error': 'username and content required'}), 400
            
        db.comment_on_post(post_id, username, content)
        return jsonify({'status': 'ok'})
    else:
        # It's a GET request
        comments = db.get_comments_for_post(post_id)
        return jsonify(comments)

if __name__ == '__main__':
    # Run with: python backend/main.py
    app.run(debug=True)
# ...existing code...