from collections import Counter
from config import WEIGHTS, TASTE_THRESHOLD

# How much each attribute contributes to the final score
WEIGHTS = {
    "genre": 2.0,
    "director": 3.0,
    "keyword": 1.0,
    "cast": 0.5,
    "language": 1.5,
}

# Only consider films rated this high when building taste profile
TASTE_THRESHOLD = 3.5


def build_taste_profile(enriched_films: list[dict]) -> dict:
    genres = Counter()
    directors = Counter()
    keywords = Counter()
    cast = Counter()
    languages = Counter()

    for film in enriched_films:
        if film.get("rating", 0) < TASTE_THRESHOLD:
            continue

        weight = film["rating"] / 5.0  # normalize to 0-1

        for genre in film.get("genres", []):
            genres[genre] += weight

        director = film.get("director")
        if director:
            directors[director] += weight

        for keyword in film.get("keywords", []):
            keywords[keyword] += weight

        for actor in film.get("cast", []):
            cast[actor] += weight

        language = film.get("language")
        if language:
            languages[language] += weight

    return {
        "genres": genres,
        "directors": directors,
        "keywords": keywords,
        "cast": cast,
        "languages": languages,
    }


def score_candidate(candidate_metadata: dict, taste_profile: dict) -> float:
    score = 0.0

    # Genre match
    for genre in candidate_metadata.get("genres", []):
        score += taste_profile["genres"].get(genre, 0) * WEIGHTS["genre"]

    # Director match
    director = candidate_metadata.get("director")
    if director:
        score += taste_profile["directors"].get(director, 0) * WEIGHTS["director"]

    # Keyword match
    for keyword in candidate_metadata.get("keywords", []):
        score += taste_profile["keywords"].get(keyword, 0) * WEIGHTS["keyword"]

    # Cast match
    for actor in candidate_metadata.get("cast", []):
        score += taste_profile["cast"].get(actor, 0) * WEIGHTS["cast"]

    # Language match
    language = candidate_metadata.get("language")
    if language:
        score += taste_profile["languages"].get(language, 0) * WEIGHTS["language"]

    return score


def rank_candidates(
    candidates: list[dict],
    enriched_user_films: list[dict],
    candidate_metadata: list[dict]
) -> list[dict]:
    taste_profile = build_taste_profile(enriched_user_films)

    # Build a lookup of metadata by title for quick access
    metadata_lookup = {m["title"].lower(): m for m in candidate_metadata}

    scored = []

    for candidate in candidates:
        title = candidate["title"].lower()
        meta = metadata_lookup.get(title)

        if not meta:
            continue

        score = score_candidate(meta, taste_profile)

        # Boost score by neighbor agreement from collaborative filter
        neighbor_boost = candidate.get("neighbor_count", 1) * 0.5
        avg_rating_boost = candidate.get("avg_neighbor_rating", 3.0) * 0.3

        final_score = score + neighbor_boost + avg_rating_boost

        scored.append({
            **meta,
            "neighbor_count": candidate.get("neighbor_count"),
            "avg_neighbor_rating": candidate.get("avg_neighbor_rating"),
            "affinity_score": round(final_score, 2),
        })

    scored.sort(key=lambda x: x["affinity_score"], reverse=True)

    print(f"Scored and ranked {len(scored)} candidates")
    return scored


if __name__ == "__main__":
    # Quick test with mock data
    mock_user_films = [
        {"title": "The Godfather", "year": "1972", "rating": 5.0,
         "genres": ["Drama", "Crime"], "director": "Francis Ford Coppola",
         "keywords": ["mafia", "organized crime"], "cast": ["Al Pacino", "Marlon Brando"],
         "language": "en"},
        {"title": "No Country for Old Men", "year": "2007", "rating": 5.0,
         "genres": ["Drama", "Crime", "Thriller"], "director": "Joel Coen",
         "keywords": ["violence", "chase", "bounty hunter"], "cast": ["Josh Brolin", "Javier Bardem"],
         "language": "en"},
    ]

    mock_candidates = [
        {"movieId": 1, "title": "Fargo", "year": "1996",
         "neighbor_count": 15, "avg_neighbor_rating": 4.5},
        {"movieId": 2, "title": "Chinatown", "year": "1974",
         "neighbor_count": 12, "avg_neighbor_rating": 4.3},
    ]

    mock_candidate_metadata = [
        {"title": "Fargo", "year": "1996", "genres": ["Crime", "Drama"],
         "director": "Joel Coen", "keywords": ["violence", "minnesota"],
         "cast": ["Frances McDormand", "William H. Macy"], "language": "en",
         "poster_path": None},
        {"title": "Chinatown", "year": "1974", "genres": ["Drama", "Crime", "Mystery"],
         "director": "Roman Polanski", "keywords": ["corruption", "mystery"],
         "cast": ["Jack Nicholson", "Faye Dunaway"], "language": "en",
         "poster_path": None},
    ]

    results = rank_candidates(mock_candidates, mock_user_films, mock_candidate_metadata)
    for r in results:
        print(f"{r['title']} ({r['year']}) — score: {r['affinity_score']}")
