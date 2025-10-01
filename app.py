import requests

DEFAULT_UA = (
    "Instagram 76.0.0.15.395 Android (24/7.0; 640dpi; 1440x2560; samsung; "
    "SM-G930F; herolte; samsungexynos8890; en_US; 138226743)"
)

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
            "followers": user["edge_followed_by"]["count"],
            "following": user["edge_follow"]["count"],
            "total_posts": user["edge_owner_to_timeline_media"]["count"]
        }
        return stats
    except KeyError as e:
        print(f"Could not extract stats from JSON: {e}")
        # Uncomment below to debug JSON structure
        # import json; print(json.dumps(j, indent=2)[:2000])
        return None


if __name__ == "__main__":
    username = "instagram"  # target username
    sessionid = None        # optional: your sessionid cookie

    stats = get_instagram_stats(username, sessionid=sessionid)
    if stats:
        print(f"{username} stats:")
        print(f"Followers: {stats['followers']:,}")
        print(f"Following: {stats['following']:,}")
        print(f"Total Posts: {stats['total_posts']:,}")
    else:
        print("Could not retrieve stats.")
