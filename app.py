import os
import json
import requests
import hashlib
from dotenv import load_dotenv
from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash
from pymongo import MongoClient

app = Flask(__name__)
load_dotenv()

app.secret_key = os.environ.get("SECRET_KEY", "your-secret-key-here")

# MongoDB connection
client = MongoClient(os.environ.get("MONGO_URI"))
db = client.TrendLens
users_collection = db.users
tracking_collection = db.tracking

DEFAULT_UA = (os.environ.get("USER_AGENT"))

def hash_password(password):
    """Hash password with SHA256"""
    secret_key = os.environ.get("HASH_KEY", "default-hash-key")
    return hashlib.sha256((password + secret_key).encode()).hexdigest()

def get_user_tracking_list(username):
    """Get list of usernames a user is tracking"""
    tracking_doc = tracking_collection.find_one({"user": username})
    if tracking_doc and "usernames" in tracking_doc:
        return tracking_doc["usernames"]
    else:
        # Create default tracking list for new users
        default_usernames = ["instagram", "natgeo", "nasa", "marvel", "ecell_srmist"]
        tracking_collection.insert_one({
            "user": username,
            "usernames": default_usernames
        })
        return default_usernames

def get_instagram_stats(username: str, user_agent: str = DEFAULT_UA, sessionid: str | None = None, timeout: int = 10) -> dict | None:
    url = f"https://i.instagram.com/api/v1/users/web_profile_info/?username={username}"
    headers = {
        "User-Agent": user_agent,
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Referer": "https://www.instagram.com/",
        "Origin": "https://www.instagram.com",
        "X-Requested-With": "XMLHttpRequest",
    }

    cookies = {}
    if sessionid:
        cookies["sessionid"] = sessionid

    try:
        resp = requests.get(url, headers=headers, cookies=cookies, timeout=timeout)
        resp.raise_for_status()
        j = resp.json()
    except Exception as e:
        print(f"Request or JSON parsing failed: {e}")
        return None

    try:
        user = j["data"]["user"]
        stats = {
            "username": username,
            "profile_name": user.get("full_name", username),
            "followers": user["edge_followed_by"]["count"],
            "following": user["edge_follow"]["count"],
            "total_posts": user["edge_owner_to_timeline_media"]["count"]
        }
        return stats
    except KeyError as e:
        print(f"Could not extract stats from JSON: {e}")
        return None

def get_instagram_stats_from_local(username: str) -> dict | None:
    try:
        with open("instagram_data.json", "r", encoding="utf-8") as f:
            all_data = json.load(f)

            if username not in all_data:
                print(f"{username} not found in local cache")
                return None

            user = all_data[username]["data"]["user"] 
            stats = {
                "username": username,
                "profile_name": user.get("full_name", username),
                "followers": user["edge_followed_by"]["count"],
                "following": user["edge_follow"]["count"],
                "total_posts": user["edge_owner_to_timeline_media"]["count"]
            }
            return stats
    except FileNotFoundError:
        print("instagram_data.json not found")
        return None

@app.route('/')
def home():
    # Check if user is logged in
    user_name = session.get('user_name')
    username = session.get('username')
    sessionid = os.environ.get("SESSION_ID")
    
    if user_name and username:
        # User is logged in, get their tracking list
        usernames = get_user_tracking_list(username)
        profiles_data = []
        
        for username_to_track in usernames:
            # Try live API first, fallback to local data
            stats = get_instagram_stats(username_to_track, sessionid=sessionid)
            # stats = get_instagram_stats_from_local(username_to_track)
            
            if stats:
                profiles_data.append(stats)
        
        profiles_data.sort(key=lambda x: x['followers'], reverse=True)
        
        for i, profile in enumerate(profiles_data, 1):
            profile['rank'] = i
        
        return render_template('index.html', profiles=profiles_data, user_name=user_name)
    else:
        # User not logged in, show landing page
        return render_template('landing.html')

@app.route('/api/tracking', methods=['GET'])
def get_tracking():
    """API endpoint to get user's tracking list"""
    if 'username' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    usernames = get_user_tracking_list(session['username'])
    return jsonify({'usernames': usernames})

@app.route('/api/tracking/add', methods=['POST'])
def add_tracking():
    """API endpoint to add a username to tracking list"""
    if 'username' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    data = request.get_json()
    new_username = data.get('username', '').strip().lower()
    
    if not new_username:
        return jsonify({'error': 'Username is required'}), 400
    
    # Remove @ if provided
    if new_username.startswith('@'):
        new_username = new_username[1:]
    
    current_usernames = get_user_tracking_list(session['username'])
    
    if new_username in current_usernames:
        return jsonify({'error': 'Username already being tracked'}), 400
    
    if len(current_usernames) >= 20:  # Limit to 20 usernames
        return jsonify({'error': 'Maximum 20 usernames allowed'}), 400
    
    # Add the new username
    current_usernames.append(new_username)
    
    tracking_collection.update_one(
        {"user": session['username']},
        {"$set": {"usernames": current_usernames}},
        upsert=True
    )
    
    return jsonify({'message': 'Username added successfully', 'usernames': current_usernames})

@app.route('/api/tracking/remove', methods=['POST'])
def remove_tracking():
    """API endpoint to remove a username from tracking list"""
    if 'username' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    data = request.get_json()
    username_to_remove = data.get('username', '').strip().lower()
    
    if not username_to_remove:
        return jsonify({'error': 'Username is required'}), 400
    
    current_usernames = get_user_tracking_list(session['username'])
    
    if username_to_remove not in current_usernames:
        return jsonify({'error': 'Username not found in tracking list'}), 400
    
    # Remove the username
    current_usernames.remove(username_to_remove)
    
    tracking_collection.update_one(
        {"user": session['username']},
        {"$set": {"usernames": current_usernames}}
    )
    
    return jsonify({'message': 'Username removed successfully', 'usernames': current_usernames})

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # Hash the password
        hashed_password = hash_password(password)
        
        # Check if user exists in database
        user = users_collection.find_one({"username": username, "password": hashed_password})
        
        if user:
            session['user_name'] = user['name']
            session['username'] = user['username']
            flash('Login successful!', 'success')
            return redirect(url_for('home'))
        else:
            flash('Invalid username or password!', 'error')
    
    return render_template('login.html')

@app.route('/signin', methods=['GET', 'POST'])
def signin():
    if request.method == 'POST':
        name = request.form['name']
        username = request.form['username']
        password = request.form['password']
        
        # Check if username already exists
        if users_collection.find_one({"username": username}):
            flash('Username already exists!', 'error')
            return render_template('signin.html')
        
        # Hash the password
        hashed_password = hash_password(password)
        
        # Insert new user
        user_data = {
            "name": name,
            "username": username,
            "password": hashed_password
        }
        
        users_collection.insert_one(user_data)
        
        # Initialize default tracking list for new user
        get_user_tracking_list(username)
        
        flash('Account created successfully! Please login.', 'success')
        return redirect(url_for('login'))
    
    return render_template('signin.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully!', 'success')
    return redirect(url_for('home'))

if __name__ == "__main__":
    app.run(debug=True)
