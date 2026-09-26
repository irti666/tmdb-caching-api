# TMDB Movie Fetcher

A simple Python command-line tool that fetches and displays movie data directly from [The Movie Database (TMDB)](https://www.themoviedb.org/) API.

## Features

- Fetch movies across multiple categories:
  - `popular`
  - `top_rated`
  - `upcoming`
  - `now_playing`
- Clean terminal output showing title, rating, and release date for each movie.

## Requirements

- Python 3.x
- `requests` library

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/your-username/tmdb-movie-fetcher.git
   cd tmdb-movie-fetcher
   ```

2. Install the required dependency:
   ```bash
   pip install requests
   ```

## Setup & Configuration

1. Get a free API key by creating an account at [themoviedb.org](https://www.themoviedb.org/) and navigating to **Settings > API**.
2. Open `app.py` and replace `"YOUR_API_KEY"` with your actual TMDB API key:
   ```python
   api_key = "YOUR_API_KEY"
   ```

## Usage

Run the script:

```bash
python app.py
```

When prompted, enter one of the available categories:
- `popular`
- `top_rated`
- `upcoming`
- `now_playing`

### Example Output

```text
Enter movie category (popular, top_rated, upcoming, now_playing): popular

--- Popular Movies ---
- Spider-Man: Brand New Day | Rating: 7.9/10 | Released: 2026-07-29
- The Odyssey | Rating: 8.0/10 | Released: 2026-07-15
- Mutiny | Rating: 6.4/10 | Released: 2026-08-19
```
