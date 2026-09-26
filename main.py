import os
import json
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import httpx
import random

import redis
# Load variables from .env file into environment
load_dotenv()

app = FastAPI(title="TMDB Movie Fetcher")

api_key = os.getenv("TMDB_API_KEY")

ALLOWED_CATEGORIES = {"popular", "top_rated", "upcoming", "now_playing"}

#Redis Lifecycle
@app.on_event("startup")
def startup_event():
    # Connects to the running Docker Redis container on localhost:6379
    app.state.redis = redis.Redis(
        host="localhost",
        port=6379,
        db=0,
        decode_responses=True
    )
    print("Connected to Redis successfully.")

@app.on_event("shutdown")
def shutdown_event():
    app.state.redis.close()
    print("Redis connection closed.")

# Define the exact structure of data returned to the client
class Movie(BaseModel):
    id: int
    title: str
    vote_average: float
    release_date: str | None = None
    overview: str

@app.get("/movies", response_model=list[Movie])
async def get_movies(user_input: str):
    # Validate the user input before making the API request
    if user_input not in ALLOWED_CATEGORIES:
        raise HTTPException(status_code=400,detail=f"Invalid Category {user_input}. Allowed categories are {ALLOWED_CATEGORIES}")

    cache_key = f"movies:{user_input}"

    # Check Redis first (Cache Hit)
    cached_data = app.state.redis.get(cache_key)
    if cached_data is not None:
        print(f"Serving '{user_input}' from Redis cache")
        return json.loads(cached_data)

    # Fetch from TMDB on Cache Miss
    print(f"Fetching '{user_input}' from TMDB API")
    url = f"https://api.themoviedb.org/3/movie/{user_input}?api_key={api_key}"
    # Asynchronous GET request
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
    # Ensure TMDB itself didn't return an error
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail= "Failed to fetch data from TMDB")
    
    data = response.json()
    movies = data["results"]

    # Store in Redis with a 24-hour TTL (86400 seconds)
    app.state.redis.set(cache_key, json.dumps(movies), ex=86400)

    return movies

@app.get("/search", response_model=list[Movie])
async def search_movies(query: str):
    clean_query = query.strip().lower()
    if not clean_query:
        raise HTTPException(status_code=400, detail="Search query cannot be empty.")

    cache_key = f"search:{clean_query}"

    # 1. Check Redis first
    cached = app.state.redis.get(cache_key)
    if cached:
        print(f"Serving search '{clean_query}' from Redis cache")
        return json.loads(cached)

    # 2. Query TMDB API
    print(f"Fetching search '{clean_query}' from TMDB API")
    url = f"https://api.themoviedb.org/3/search/movie?api_key={api_key}&query={clean_query}"
    
    async with httpx.AsyncClient() as client:
        res = await client.get(url)

    if res.status_code != 200:
        raise HTTPException(
            status_code=res.status_code,
            detail="Failed to fetch search results from TMDB"
        )
        
    data = res.json()
    movies = data["results"]
    app.state.redis.set(cache_key, json.dumps(movies), ex=86400)
    return movies

# Pick a single random movie from a category
@app.get("/random-movie", response_model=Movie)
async def get_random_movie(user_input: str):
    # Reuses get_movies to automatically check and use the Redis cache
    movies = await get_movies(user_input)
    if not movies:
        raise HTTPException(status_code=404, detail="No movies found.")
    
    return random.choice(movies)

@app.get("/health")
async def health_check():
    try:
        # Check if Redis is reachable
        redis_alive = app.state.redis.ping()
    except Exception:
        redis_alive = False

    return {
        "status": "healthy" if redis_alive else "degraded",
        "redis_connected": redis_alive,
        "environment": "local"
    }

@app.delete("/cache")
async def clear_cache():
    app.state.redis.flushdb()
    return {"message": "Redis cache cleared successfully."}