import os
import json
import random
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Response
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import httpx
import redis.asyncio as aioredis

load_dotenv()

TMDB_API_KEY = os.getenv("TMDB_API_KEY")
# Use cloud Redis if provided, otherwise default to local Docker Redis
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
CACHE_TTL = 86400  # 24 hours

ALLOWED_CATEGORIES = {"popular", "top_rated", "upcoming", "now_playing"}

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Connect to Redis asynchronously so it doesn't slow down incoming requests
    app.state.redis = aioredis.from_url(
        REDIS_URL,
        decode_responses=True
    )
    yield
    # Safely close the Redis connection when the server stops
    await app.state.redis.close()

app = FastAPI(
    title="TMDB Movie Fetcher & Caching API",
    description="A fast REST API that fetches movies from TMDB and caches them with Redis.",
    version="1.0.0",
    lifespan=lifespan
)

# Allow Swagger UI to make requests without being blocked by the browser.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)
# Define the exact fields we want to return for each movie
class Movie(BaseModel):
    id: int
    title: str
    vote_average: float
    release_date: str | None = None
    overview: str

class HealthResponse(BaseModel):
    status: str
    redis_connected: bool
    environment: str

# Redirect root URL directly to Swagger docs
@app.get("/", include_in_schema=False)
async def root():
    return RedirectResponse(url="/docs")

@app.get("/movies", response_model=list[Movie])
async def get_movies(user_input: str, response: Response):
    user_input = user_input.strip().lower()
    if user_input not in ALLOWED_CATEGORIES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid Category '{user_input}'. Allowed categories are {sorted(list(ALLOWED_CATEGORIES))}"
        )

    cache_key = f"movies:{user_input}"

    # Check Redis first (Cache Hit)
    try:
        cached_data = await app.state.redis.get(cache_key)
        if cached_data is not None:
            response.headers["X-Cache"] = "HIT"
            return json.loads(cached_data)
    except Exception:
        # If Redis is temporarily down, ignore the error and keep going
        pass

    # Fetch from TMDB on Cache Miss
    url = f"https://api.themoviedb.org/3/movie/{user_input}?api_key={TMDB_API_KEY}"
    async with httpx.AsyncClient(timeout=10.0) as client:
        res = await client.get(url)

    if res.status_code != 200:
        raise HTTPException(status_code=res.status_code, detail="Failed to fetch data from TMDB.")

    data = res.json()
    movies = data["results"]

    # Store in Redis asynchronously
    try:
        await app.state.redis.set(cache_key, json.dumps(movies), ex=CACHE_TTL)
    except Exception:
        pass

    response.headers["X-Cache"] = "MISS"
    return movies

@app.get("/search", response_model=list[Movie])
async def search_movies(query: str, response: Response):
    clean_query = query.strip().lower()
    if not clean_query:
        raise HTTPException(status_code=400, detail="Search query cannot be empty.")

    cache_key = f"search:{clean_query}"

    try:
        cached = await app.state.redis.get(cache_key)
        if cached is not None:
            response.headers["X-Cache"] = "HIT"
            return json.loads(cached)
    except Exception:
        pass

    url = f"https://api.themoviedb.org/3/search/movie?api_key={TMDB_API_KEY}&query={clean_query}"
    async with httpx.AsyncClient(timeout=10.0) as client:
        res = await client.get(url)

    if res.status_code != 200:
        raise HTTPException(status_code=res.status_code, detail="Failed to fetch search results from TMDB.")

    data = res.json()
    movies = data["results"]

    try:
        await app.state.redis.set(cache_key, json.dumps(movies), ex=CACHE_TTL)
    except Exception:
        pass

    response.headers["X-Cache"] = "MISS"
    return movies

@app.get("/random-movie", response_model=Movie)
async def get_random_movie(user_input: str, response: Response):
    movies = await get_movies(user_input, response)
    if not movies:
        raise HTTPException(status_code=404, detail="No movies found.")
    return random.choice(movies)

@app.get("/health", response_model=HealthResponse)
async def health_check():
    try:
        redis_alive = await app.state.redis.ping()
    except Exception:
        redis_alive = False

    return {
        "status": "healthy" if redis_alive else "degraded",
        "redis_connected": bool(redis_alive),
        "environment": "cloud" if os.getenv("RENDER") else "local"
    }

@app.delete("/cache")
async def clear_cache():
    try:
        await app.state.redis.flushdb()
        return {"message": "Redis cache cleared successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to clear cache: {str(e)}")