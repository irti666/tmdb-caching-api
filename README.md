# TMDB Movie Fetcher & Caching API

A fast backend API built with FastAPI that fetches and searches movie data from [The Movie Database (TMDB)](https://www.themoviedb.org/). It uses Redis to store recent responses in memory so repeated requests load instantly without hitting TMDB's rate limits.

[![Live Demo](https://img.shields.io/badge/Render-Live%20Demo-brightgreen?style=flat&logo=render)](https://tmdb-caching-api.onrender.com/docs)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/Framework-FastAPI-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Redis](https://img.shields.io/badge/Cache-Redis-DC382D.svg?logo=redis&logoColor=white)](https://redis.io/)

## Live Demo

- **Interactive API Docs (Swagger UI):** <https://tmdb-caching-api.onrender.com/docs>
- **Health Check Endpoint:** <https://tmdb-caching-api.onrender.com/health>

⚠️ Please Note: The app is hosted on Render's free tier. If no requests are made for a while, the server goes to sleep to save resources. When you first open the link or execute an endpoint, it might take 30 to 50 seconds to wake back up. Once awake, all requests will respond normally and fast!</span>

## How It Works

When a client queries an endpoint, the API checks Redis first before making an external call:

```text
User Request
     │
     ▼
┌──────────────┐      Found in Cache (HIT)     ┌────────────────┐
│   FastAPI    │ ────────────────────────────► │  Redis Cache   │
│   Backend    │ ◄──────────────────────────── │   (In-Memory)  │
└──────┬───────┘   Returns saved data instantly└────────────────┘
       │
       │ Not in Cache (MISS)
       ▼
┌──────────────┐
│   TMDB API   │
│ (External)   │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│  Pydantic    │ ──► Keeps only needed fields (ID, title, rating, etc.)
│  Validation  │ ──► Saves result in Redis for 24 hours
└──────┬───────┘ ──► Adds 'X-Cache: MISS' header
       │
       ▼
User Receives Response
```

- **Cache Hit:** If data exists in Redis, the API returns it immediately with the header `X-Cache: HIT`.
- **Cache Miss:** If not cached, the API fetches the payload from TMDB via `httpx`, stores the filtered output in Redis with a 24-hour TTL (86,400s), and returns it with `X-Cache: MISS`.
- **Safety Fallback:** If the Redis instance is unreachable, queries bypass the cache and fetch directly from TMDB without throwing an unhandled exception.

## What It Does

- **Category Browsing:** Query movies across categories (`popular`, `top_rated`, `upcoming`, `now_playing`).
- **Search:** Search movies by title with clean input sanitization.
- **Random Picker:** Select a random movie from any supported category.
- **Health Check:** Monitor service status and live Redis connectivity at `/health`.
- **Cache Invalidation:** Administrative `DELETE /cache` route to flush keys on demand.
- **Output Trimming:** Pydantic schemas filter out TMDB's unused attributes to serve minimal, typed payloads.

## Tech Stack

- **Framework:** FastAPI
- **ASGI Server:** Uvicorn
- **Cache Store:** Redis (`redis.asyncio`)
- **HTTP Client:** HTTPX
- **Data Serialization:** Pydantic v2
- **Deployment:** Render + Cloud Redis

## API Endpoints

| Method | Endpoint | Description | Query Parameters |
| :--- | :--- | :--- | :--- |
| `GET` | `/` | Redirects automatically to `/docs` | None |
| `GET` | `/movies` | Get movies by category | `user_input` (`popular`, `top_rated`, `upcoming`, `now_playing`) |
| `GET` | `/search` | Search movies by title | `query` (string) |
| `GET` | `/random-movie` | Return one random movie from a category | `user_input` (`popular`, `top_rated`, etc.) |
| `GET` | `/health` | Check API and Redis connection status | None |
| `DELETE` | `/cache` | Clear all cached keys in Redis | None |

## Local Setup

### 1. Clone the Repository

```bash
git clone https://github.com/irti666/tmdb-movie-fetcher.git
cd tmdb-movie-fetcher
```

### 2. Set Up a Virtual Environment

**Windows (PowerShell):**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

**macOS / Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install fastapi "uvicorn[standard]" redis httpx pydantic python-dotenv
```

### 4. Configure Environment Variables

Create a `.env` file in the root directory:

```env
TMDB_API_KEY=your_tmdb_api_key_here
REDIS_URL=redis://localhost:6379/0
```

> Obtain an API key at [themoviedb.org](https://www.themoviedb.org/) under **Settings > API**.

### 5. Run Redis with Docker

```bash
docker run -d --name redis-cache -p 6379:6379 redis:alpine
```

### 6. Run the Application

```bash
uvicorn main:app --reload
```

Open <http://127.0.0.1:8000/docs> in your browser to interact with the API via Swagger UI.

## Example Response

`GET /movies?user_input=popular`

```json
[
  {
    "id": 933260,
    "title": "The Odyssey",
    "vote_average": 8.0,
    "release_date": "2026-07-15",
    "overview": "A contemporary retelling of Homer's epic voyage across perilous seas."
  },
  {
    "id": 1053544,
    "title": "Mutiny",
    "vote_average": 6.4,
    "release_date": "2026-08-19",
    "overview": "After his billionaire boss is murdered, an undercover agent is framed and forced on the run."
  }
]
```