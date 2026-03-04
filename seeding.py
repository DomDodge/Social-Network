import random
from backend.database import DB

def seed_database(db):
    print("Starting to seed database...")

    # 1. Create Users and Accounts
    # List of tuples containing (username, email)
    mock_users = [
        ("alice_wonder", "alice@example.com"),
        ("bob_builder", "bob@example.com"),
        ("charlie_chap", "charlie@example.com"),
        ("diana_prince", "diana@example.com"),
        ("edward_teach", "edward@example.com")
    ]

    usernames = []
    # Enumerate gives us an index (i) starting at 0 to use for the user_id
    for i, (username, email) in enumerate(mock_users):
        user_id = i + 1 
        db.create_user(email)
        db.create_account(username, email, user_id)
        usernames.append(username)
        
    print(f"Created {len(usernames)} accounts.")

    # 2. Create Posts
    mock_content = [
        "Just had the best coffee of my life! ☕",
        "Learning SQLite today, feeling like a hacker.",
        "What a beautiful day outside.",
        "Can anyone recommend a good sci-fi book?",
        "Just finished a huge coding project! Time to sleep.",
        "Hello world!",
        "Who else is excited for the weekend?",
        "Python is the absolute best language.",
        "Just hit 10k steps today!",
        "Thinking about getting a cat. Thoughts?"
    ]

    for username in usernames:
        # Give each user 2 random posts
        for _ in range(2):
            content = random.choice(mock_content)
            db.post(username, content)
            
    print("Populated posts.")

    # 3. Create Follows
    for follower in usernames:
        # Make each user follow 2 to 3 random people (excluding themselves)
        num_follows = random.randint(2, 3)
        possible_follows = [u for u in usernames if u != follower]
        following_list = random.sample(possible_follows, num_follows)
        
        for following in following_list:
            db.follow(follower, following)
            
    print("Created follow relationships.")

    # 4. Create Likes
    all_posts = db.get_all_posts()
    for post in all_posts:
        # Have 1 to 4 random users like each post
        num_likes = random.randint(1, 4)
        likers = random.sample(usernames, num_likes)
        
        for liker in likers:
            db.like_post(post['id'], liker)
            
    print("Added likes to posts. Database seeding complete!")
    
if __name__ == "__main__":
    # If you want a fresh start every time you run the script, 
    # you can delete 'database.db' from your folder before running this.
    db = DB("database.db")
    
    # Run the seeding function
    seed_database(db)
    
    # Let's test it by getting Diana's feed!
    print("\n--- Diana's Feed ---")
    dianas_feed = db.get_feed("diana_prince")
    
    for item in dianas_feed:
        print(f"[{item['timestamp'][:16]}] {item['username']}: {item['content']}")
        
    db.close()