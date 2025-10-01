import os
import json
import requests
from dotenv import load_dotenv
from flask import Flask, render_template, request, jsonify


app = Flask(__name__)
load_dotenv()


DEFAULT_UA = (os.environ.get("USER_AGENT"))


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


# if __name__ == "__main__":
#     # usernames = ["instagram", "natgeo", "nasa", "marvel", "ecell_srmist", "mcdonalds", "dominos", "starbucks", "earthpix", "iss"]
#     usernames = ["instagram"]
#     sessionid = os.environ.get("SESSION_ID") 


#     for username in usernames:
#         # stats = get_instagram_stats(username, sessionid=sessionid)
#         stats = get_instagram_stats_from_local(username)
#         if stats:
#             print(f"{username} stats:")
#             print(f"Followers: {stats['followers']:,}")
#             print(f"Following: {stats['following']:,}")
#             print(f"Total Posts: {stats['total_posts']:,}")
#         else:
#             print("Could not retrieve stats.")


@app.route('/')
def home():
    sessionid = os.environ.get("SESSION_ID")
    usernames = ["instagram", "natgeo", "nasa", "marvel", "ecell_srmist", "mcdonalds", "dominos", "starbucks", "earthpix", "iss"]
    profiles_data = []
    
    for username in usernames:
        # stats = get_instagram_stats(username, sessionid=sessionid)
        stats = get_instagram_stats_from_local(username)
        if stats:
            profiles_data.append(stats)
    
    profiles_data.sort(key=lambda x: x['followers'], reverse=True)
    
    for i, profile in enumerate(profiles_data, 1):
        profile['rank'] = i
    
    return render_template('index.html', profiles=profiles_data)


if __name__ == "__main__":
    app.run(debug=True)
