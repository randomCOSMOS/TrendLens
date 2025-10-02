import os
import json
import requests
import hashlib
from dotenv import load_dotenv
from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash, Response
from pymongo import MongoClient

app = Flask(__name__)
load_dotenv()

app.secret_key = os.environ.get("SECRET_KEY", "your-secret-key-here")

client = MongoClient(os.environ.get("MONGO_URI"))
db = client.TrendLens
users_collection = db.users
tracking_collection = db.tracking

DEFAULT_UA = (os.environ.get("USER_AGENT"))

def hash_password(password):
    secret_key = os.environ.get("HASH_KEY", "default-hash-key")
    return hashlib.sha256((password + secret_key).encode()).hexdigest()

def get_user_tracking_list(username):
    tracking_doc = tracking_collection.find_one({"user": username})
    if tracking_doc and "usernames" in tracking_doc:
        return tracking_doc["usernames"]
    else:
        default_usernames = ["instagram", "natgeo", "nasa", "dominos", "ecell_srmist"]
        tracking_collection.insert_one({
            "user": username,
            "usernames": default_usernames
        })
        return default_usernames

def calculate_profile_metrics(stats):
    profile = stats.copy()
    
    completeness_score = 0
    completeness_details = {}
    
    has_bio = profile.get('biography', '') != '' and profile.get('biography', '') != profile.get('username', '')
    completeness_details['bio'] = has_bio
    if has_bio: completeness_score += 25
    
    has_profile_pic = profile.get('profile_pic_url') is not None
    completeness_details['profile_pic'] = has_profile_pic
    if has_profile_pic: completeness_score += 20
    
    has_external_url = profile.get('external_url') is not None
    completeness_details['external_url'] = has_external_url
    if has_external_url: completeness_score += 15
    
    is_verified = profile.get('is_verified', False)
    completeness_details['verified'] = is_verified
    if is_verified: completeness_score += 20
    
    active_posting = profile.get('total_posts', 0) > 10
    completeness_details['active_posting'] = active_posting
    if active_posting: completeness_score += 20
    
    profile['completeness_score'] = completeness_score
    profile['completeness_details'] = completeness_details
    
    content_score = 0
    content_details = {}
    
    has_clips = profile.get('has_clips', False)
    content_details['reels'] = has_clips
    if has_clips: content_score += 30
    
    highlight_count = profile.get('highlight_reel_count', 0)
    content_details['highlights'] = highlight_count
    if highlight_count > 0: content_score += 25
    
    has_ar_effects = profile.get('has_ar_effects', False)
    content_details['ar_effects'] = has_ar_effects
    if has_ar_effects: content_score += 20
    
    is_professional = profile.get('is_professional_account', False)
    content_details['professional'] = is_professional
    if is_professional: content_score += 25
    
    profile['content_score'] = content_score
    profile['content_details'] = content_details
    
    followers = profile.get('followers', 0)
    following = profile.get('following', 0)
    total_posts = profile.get('total_posts', 0)
    
    if following > 0:
        ff_ratio = followers / following
    else:
        ff_ratio = followers
    
    if followers > 0:
        posts_per_1k_followers = (total_posts / followers) * 1000
    else:
        posts_per_1k_followers = 0
    
    if total_posts > 0 and followers > 0:
        activity_score = min(100, (posts_per_1k_followers / 10) * 100)
    else:
        activity_score = 0
    
    if followers > 0 and ff_ratio > 0:
        import math
        audience_quality = min(100, math.log10(max(1, ff_ratio)) * 25)
    else:
        audience_quality = 0
    
    profile['advanced_metrics'] = {
        'ff_ratio': ff_ratio,
        'posts_per_1k_followers': posts_per_1k_followers,
        'activity_score': activity_score,
        'audience_quality': audience_quality
    }
    return profile

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
            "total_posts": user["edge_owner_to_timeline_media"]["count"],
            "biography": user.get("biography", ""),
            "external_url": user.get("external_url"),
            "is_verified": user.get("is_verified", False),
            "is_private": user.get("is_private", False),
            "is_professional_account": user.get("is_professional_account", False),
            "is_business_account": user.get("is_business_account", False),
            "category_name": user.get("category_name"),
            "profile_pic_url": user.get("profile_pic_url"),
            "profile_pic_url_hd": user.get("profile_pic_url_hd"),
            "highlight_reel_count": user.get("highlight_reel_count", 0),
            "has_clips": user.get("has_clips", False),
            "has_ar_effects": user.get("has_ar_effects", False)
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
                "total_posts": user["edge_owner_to_timeline_media"]["count"],
                "biography": user.get("biography", ""),
                "external_url": user.get("external_url"),
                "is_verified": user.get("is_verified", False),
                "is_private": user.get("is_private", False),
                "is_professional_account": user.get("is_professional_account", False),
                "is_business_account": user.get("is_business_account", False),
                "category_name": user.get("category_name"),
                "profile_pic_url": user.get("profile_pic_url"),
                "profile_pic_url_hd": user.get("profile_pic_url_hd"),
                "highlight_reel_count": user.get("highlight_reel_count", 0),
                "has_clips": user.get("has_clips", False),
                "has_ar_effects": user.get("has_ar_effects", False)
            }
            return stats
        
    except FileNotFoundError:
        print("instagram_data.json not found")
        return None


@app.route('/')
def home():
    user_name = session.get('user_name')
    username = session.get('username')
    sessionid = os.environ.get("SESSION_ID")
    
    if user_name and username:
        usernames = get_user_tracking_list(username)
        profiles_data = []
        
        for username_to_track in usernames:
            stats = get_instagram_stats(username_to_track, sessionid=sessionid)
            # stats = get_instagram_stats_from_local(username_to_track)            
            if stats:
                profiles_data.append(stats)
        
        profiles_data.sort(key=lambda x: x['followers'], reverse=True)
        
        for i, profile in enumerate(profiles_data, 1):
            profile['rank'] = i
        
        return render_template('index.html', profiles=profiles_data, user_name=user_name)
    else:
        return render_template('landing.html')


@app.route('/profile/<username>')
def profile_detail(username):
    if 'user_name' not in session:
        return redirect(url_for('login'))
    
    sessionid = os.environ.get("SESSION_ID")
    stats = get_instagram_stats(username, sessionid=sessionid)
    
    if not stats:
        flash(f'Profile data not found for @{username}', 'error')
        return redirect(url_for('home'))
    
    profile_data = calculate_profile_metrics(stats)
    return render_template('profile.html', profile=profile_data)

@app.route('/api/tracking', methods=['GET'])
def get_tracking():
    if 'username' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    usernames = get_user_tracking_list(session['username'])
    return jsonify({'usernames': usernames})


@app.route('/api/tracking/add', methods=['POST'])
def add_tracking():
    if 'username' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    data = request.get_json()
    new_username = data.get('username', '').strip().lower()
    
    if not new_username:
        return jsonify({'error': 'Username is required'}), 400
    
    if new_username.startswith('@'):
        new_username = new_username[1:]
    
    current_usernames = get_user_tracking_list(session['username'])
    
    if new_username in current_usernames:
        return jsonify({'error': 'Username already being tracked'}), 400
    
    if len(current_usernames) >= 20:  # Limit to 20 usernames
        return jsonify({'error': 'Maximum 20 usernames allowed'}), 400
    
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
        
        hashed_password = hash_password(password)
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
        
        if users_collection.find_one({"username": username}):
            flash('Username already exists!', 'error')
            return render_template('signin.html')
        
        hashed_password = hash_password(password)
        
        user_data = {
            "name": name,
            "username": username,
            "password": hashed_password
        }
        
        users_collection.insert_one(user_data)
        
        get_user_tracking_list(username)
        
        flash('Account created successfully! Please login.', 'success')
        return redirect(url_for('login'))
    return render_template('signin.html')


@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully!', 'success')
    return redirect(url_for('home'))

@app.route('/proxy-image')
def proxy_image():
    """Proxy route to serve Instagram images without CORS issues"""
    image_url = request.args.get('url')
    if not image_url:
        return "No URL provided", 400
    
    try:
        headers = {
            'User-Agent': DEFAULT_UA,
            'Referer': 'https://www.instagram.com/',
            'Accept': 'image/webp,image/apng,image/*,*/*;q=0.8',
        }
        
        response = requests.get(image_url, headers=headers, timeout=10)
        response.raise_for_status()
        
        # Return the image with proper headers
        return Response(
            response.content,
            content_type=response.headers.get('content-type', 'image/jpeg'),
            headers={
                'Cache-Control': 'public, max-age=3600',  # Cache for 1 hour
                'Access-Control-Allow-Origin': '*'
            }
        )
        
    except Exception as e:
        print(f"Error proxying image: {e}")
        return "", 404

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)