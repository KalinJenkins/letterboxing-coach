import requests
import json
import os
import time
from dotenv import load_dotenv

load_dotenv()

TMDB_API_KEY = os.getenv("TMDB_API_KEY")
BASE_URL = "https://api.themoviedb.org/3"
CACHE_DIR = "cache"

def _ensure_cache():
    os.makedirs(CACHE_DIR, exist_ok=True)

def _cache_path(tmdb_id: int) -> str:
    return os.path.join(CACHE_DIR, f"{tmdb_id}.json")

def _load_cache(tmdb_id: int) -> dict | None:
    path = _cache_path(tmdb_id)
    if os.path.exists(path):
        with open(path, "r") as f:
            return json.load(f)
    return None

def _save_cache(tmdb_id: int, data: dict):
    _ensure_cache()
    with open(_cache_path(tmdb_id), "w") as f:
        json.dump(data, f)

def search_film(title: str, year: str) -> int | None:
    """
    Searches TMDB for a film by title and year.
    Returns the TMDB ID or None if not found.
    """
    params = {
        "api_key": TMDB_API_KEY,
        "query": title,
        "year": year,
        "include_adult": False
    }

    response = requests.get(f"{BASE_URL}/search/movie", params=params)

    if response.status_code != 200:
        print(f"TMDB search failed for '{title}' ({year}): {response.status_code}")
        return None

    results = response.json().get("results", [])

    if not results:
        # Retry without year in case of mismatch
        params.pop("year")
        response = requests.get(f"{BASE_URL}/search/movie", params=params)
        results = response.json().get("results", [])

    if not results:
        print(f"No TMDB match found for '{title}' ({year})")
        return None

    return results[0]["id"]

def get_film_metadata(tmdb_id: int) -> dict | None:
    """
    Fetches full metadata for a film by TMDB ID.
    Uses local cache to avoid repeat API calls.
    """
    cached = _load_cache(tmdb_id)
    if cached:
        return cached

    params = {
        "api_key": TMDB_API_KEY,
        "append_to_response": "credits,keywords"
    }

    response = requests.get(f"{BASE_URL}/movie/{tmdb_id}", params=params)

    if response.status_code != 200:
        print(f"TMDB metadata fetch failed for ID {tmdb_id}: {response.status_code}")
        return None

    raw = response.json()

    metadata = {
        "tmdb_id": tmdb_id,
        "title": raw.get("title"),
        "year": raw.get("release_date", "")[:4],
        "genres": [g["name"] for g in raw.get("genres", [])],
        "keywords": [k["name"] for k in raw.get("keywords", {}).get("keywords", [])],
        "cast": [c["name"] for c in raw.get("credits", {}).get("cast", [])[:10]],
        "director": next(
            (c["name"] for c in raw.get("credits", {}).get("crew", []) if c["job"] == "Director"),
            None
        ),
        "runtime": raw.get("runtime"),
        "language": raw.get("original_language"),
        "popularity": raw.get("popularity"),
        "poster_path": raw.get("poster_path"),
    }

    _save_cache(tmdb_id, metadata)
    time.sleep(0.25)  # polite delay

    return metadata

def enrich_films(films: list[dict]) -> list[dict]:
    """
    Takes a list of films from the parser and adds TMDB metadata to each.
    Skips films that can't be matched.
    """
    enriched = []
    total = len(films)

    for i, film in enumerate(films):
        print(f"Enriching {i+1}/{total}: {film['title']}")
        tmdb_id = search_film(film["title"], film["year"])

        if not tmdb_id:
            continue

        metadata = get_film_metadata(tmdb_id)

        if not metadata:
            continue

        enriched.append({**film, **metadata})

    print(f"Successfully enriched {len(enriched)}/{total} films")
    return enriched


if __name__ == "__main__":
    # Quick test against a single known film
    tmdb_id = search_film("The Godfather", "1972")
    print(f"The Godfather TMDB ID: {tmdb_id}")
    if tmdb_id:
        meta = get_film_metadata(tmdb_id)
        print(json.dumps(meta, indent=2))
