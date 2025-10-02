# TrendLens - Instagram Analytics Dashboard

A Flask-based web application for tracking and analyzing Instagram profiles, with a sortable dashboard, detailed metrics, and user management.

Live Demo: https://trendlens-insta.onrender.com


## Features

* **Real-time Analytics**: Fetch Instagram profile stats
* **Sortable Dashboard**: Rank profiles by followers, posts, etc.
* **Profile Insights**: Completeness & content strategy scores
* **User Management**: Authentication with MongoDB, SHA256 password hashing
* **Caching**: 5-minute cache to reduce API requests
* **Responsive UI**: HTML/CSS/JS-based dashboard


## Tech Stack

* **Backend**: Python Flask
* **Database**: MongoDB
* **Frontend**: HTML, CSS, JavaScript (Vanilla)
* **Deployment**: Docker containerized, Render.com hosting


## Quick Start

### Option 1: Docker

```bash
docker pull randomcosmos/trendlens:v1
docker run -p 5000:5000 \
  -e MONGO_URI="your_mongo_uri" \
  -e SESSION_ID="your_session_id" \
  -e SECRET_KEY="your_secret_key" \
  randomcosmos/trendlens:v1
```

Access: `http://localhost:5000`

### Option 2: Local Development

```bash
git clone <repository-url>
cd trendlens
pip install -r requirements.txt
# Add .env with required variables
python app.py
```



## Environment Variables

```env
SECRET_KEY=your_secret_key
HASH_KEY=your_hash_key
MONGO_URI=your_mongodb_connection_string
SESSION_ID=your_instagram_session_id
USER_AGENT=Mozilla/5.0 (Windows NT 10.0; Win64; x64)
```



## Project Structure

```
trendlens/
├── app.py
├── templates/
│   ├── base.html
│   ├── landing.html
│   ├── login.html
│   ├── signin.html
│   ├── index.html
│   └── profile.html
├── static/
│   ├── css/
│   └── js/
├── Dockerfile
└── .env
```


## MongoDB Collections

```json
// users
{
  "name": "John Doe",
  "username": "johndoe",
  "password": "hashed_password"
}

// tracking
{
  "user": "johndoe",
  "usernames": ["instagram", "natgeo", "nasa"]
}
```

## API Endpoints

* `GET /` – Landing or dashboard
* `GET /profile/<username>` – Profile detail
* `GET /api/tracking` – User’s tracking list
* `POST /api/tracking/add` – Add username
* `POST /api/tracking/remove` – Remove username
* `GET /proxy-image` – Proxy Instagram images


## Deployment

* **Docker Hub**: `randomcosmos/trendlens:v1`
* **Live Demo**: [trendlens-insta.onrender.com](https://trendlens-insta.onrender.com)
* **Platform**: Render.com
