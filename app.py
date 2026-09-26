import requests

api_key = "YOUR_API_KEY"

user_input = input("Enter movie category (popular, top_rated, upcoming, now_playing): ")

url = f"https://api.themoviedb.org/3/movie/{user_input}?api_key={api_key}"

# Send a GET request to the TMDB API
response = requests.get(url)
data = response.json()
movies = data["results"]
# Loop through and print the movie details
print(f"\n--- {user_input.replace('_', ' ').title()} Movies ---")
for movie in movies:
    title = movie["title"]
    rating = movie["vote_average"]
    release_date = movie["release_date"]
    
    print(f"- {title} | Rating: {rating}/10 | Released: {release_date}")
