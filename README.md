# TMDB Movie Fetcher & Caching API

A high-performance REST API built with FastAPI that fetches, searches, and caches movie catalog data directly from [The Movie Database (TMDB)](https://www.themoviedb.org/) API, backed by an in-memory Redis cache-aside architecture.

## Features

- **FastAPI Endpoints:**
  - Query movies across categories: `popular`, `top_rated`, `upcoming`, `now_playing`
  - Search movies by title with input sanitization
  - Pick a single random recommendation from any supported category
  - Health check endpoint monitoring live Redis connectivity
  - Administrative cache invalidation endpoint
- **Redis Caching (Cache-Aside):** Stores TMDB responses with a 24-hour TTL (86,400s) to minimize API latency and prevent rate-limiting.
- **Asynchronous Requests:** Non-blocking external HTTP calls handled via `httpx.AsyncClient`.
- **Data Validation:** Strict response serialization and filtering powered by Pydantic models.

## Requirements

- Python 3.10+
- Docker (to run local Redis container)
- TMDB API key

## Dependencies

- `fastapi`
- `uvicorn[standard]`
- `redis`
- `httpx`
- `pydantic`
- `python-dotenv`

## Installation

1. Clone the repository:
   ```bash
   git clone [https://github.com/irti666/tmdb-movie-fetcher.git](https://github.com/irti666/tmdb-movie-fetcher.git)
   cd tmdb-movie-fetcher
   ```

2. Create and activate a virtual environment:
   ```bash
   # Windows (PowerShell):
   python -m venv venv
   .\venv\Scripts\Activate.ps1

   # macOS / Linux:
   python3 -m venv venv
   source venv/bin/activate
   ```

3. Install required dependencies:
   ```bash
   pip install fastapi "uvicorn[standard]" redis httpx pydantic python-dotenv
   ```
   *(or `pip install -r requirements.txt` if you have saved the file)*

## Setup & Configuration

1. Get a free API key by creating an account at [themoviedb.org](https://www.themoviedb.org/) and navigating to **Settings > API**.
2. Create a `.env` file in the project root directory:
   ```env
   TMDB_API_KEY=your_actual_tmdb_api_key_here
   ```
3. Start the Redis cache container using Docker:
   ```bash
   docker run -d --name redis-cache -p 6379:6379 redis:alpine
   ```

## Usage

1. Start the FastAPI development server:
   ```bash
   uvicorn main:app --reload
   ```
   *(Note: If your file is named `app.py`, run `uvicorn app:app --reload` instead)*

2. Open your browser to access the interactive API docs:
   - **Swagger UI:** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
   - **ReDoc:** [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

## API Endpoints

- `GET /movies?user_input={category}` — Fetch movies by category (`popular`, `top_rated`, `upcoming`, `now_playing`).
- `GET /search?query={title}` — Search movies by title.
- `GET /random-movie?user_input={category}` — Get a random movie from a category.
- `GET /health` — Check server status and Redis connection health.
- `DELETE /cache` — Flush all keys from the Redis cache.

### Example Output

Request to `GET http://127.0.0.1:8000/movies?user_input=popular`:

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