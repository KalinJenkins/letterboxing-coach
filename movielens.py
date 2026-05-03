import pandas as pd
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import os

MOVIELENS_DIR = "data/ml-25m"
MOVIES_PATH = os.path.join(MOVIELENS_DIR, "movies.csv")
RATINGS_PATH = os.path.join(MOVIELENS_DIR, "ratings.csv")

# Only consider users who have rated at least this many films
MIN_USER_RATINGS = 50
# Number of nearest neighbors to find
N_NEIGHBORS = 20
# Number of candidate films to return
N_CANDIDATES = 100


def load_movielens():
    print("Loading MovieLens dataset...")
    movies = pd.read_csv(MOVIES_PATH)
    ratings = pd.read_csv(RATINGS_PATH, usecols=["userId", "movieId", "rating"])
    print(f"Loaded {len(movies)} movies and {len(ratings)} ratings")
    return movies, ratings


def match_films_to_movielens(user_films: list[dict], movies_df: pd.DataFrame) -> dict:
    matched = {}
    unmatched = []

    for film in user_films:
        title = film["title"].strip().lower()
        year = str(film["year"]).strip()

        # Extract year from MovieLens title format "Movie Title (1999)"
        movies_df["parsed_year"] = movies_df["title"].str.extract(r'\((\d{4})\)$')
        movies_df["parsed_title"] = movies_df["title"].str.replace(r'\s*\(\d{4}\)$', '', regex=True).str.strip().str.lower()

        # Try matching on title + year first
        match = movies_df[
            (movies_df["parsed_title"] == title) &
            (movies_df["parsed_year"] == year)
        ]

        # Fall back to title only
        if match.empty:
            match = movies_df[movies_df["parsed_title"] == title]

        if not match.empty:
            movie_id = match.iloc[0]["movieId"]
            matched[movie_id] = film["rating"]
        else:
            unmatched.append(film["title"])

    print(f"Matched {len(matched)} films to MovieLens ({len(unmatched)} unmatched)")
    return matched


def get_candidates(user_films: list[dict]) -> list[dict]:
    movies_df, ratings_df = load_movielens()

    # Match user films to MovieLens IDs
    user_matched = match_films_to_movielens(user_films, movies_df)

    if len(user_matched) < 10:
        print("Warning: fewer than 10 films matched to MovieLens — recommendations may be weak")

    watched_ids = set(user_matched.keys())

    # Filter to users who have rated at least MIN_USER_RATINGS films
    print("Filtering active users...")
    user_counts = ratings_df["userId"].value_counts()
    active_users = user_counts[user_counts >= MIN_USER_RATINGS].index
    ratings_df = ratings_df[ratings_df["userId"].isin(active_users)]

    # Filter to only films the user has seen to build similarity matrix
    print("Building user similarity matrix...")
    overlap_ratings = ratings_df[ratings_df["movieId"].isin(watched_ids)]

    if overlap_ratings.empty:
        print("No overlap found with MovieLens users")
        return []

    # Pivot to user x movie matrix
    pivot = overlap_ratings.pivot_table(
        index="userId",
        columns="movieId",
        values="rating"
    ).fillna(0)

    # Build the user's own rating vector aligned to the same columns
    user_vector = pd.Series(user_matched).reindex(pivot.columns, fill_value=0).values.reshape(1, -1)

    # Compute cosine similarity between user and all MovieLens users
    similarities = cosine_similarity(user_vector, pivot.values)[0]
    top_indices = np.argsort(similarities)[::-1][:N_NEIGHBORS]
    neighbor_ids = pivot.index[top_indices].tolist()

    print(f"Found {len(neighbor_ids)} nearest neighbors")

    # Get films rated highly by neighbors that user hasn't seen
    neighbor_ratings = ratings_df[
        (ratings_df["userId"].isin(neighbor_ids)) &
        (~ratings_df["movieId"].isin(watched_ids)) &
        (ratings_df["rating"] >= 4.0)
    ]

    # Score candidates by how many neighbors rated them highly
    candidate_scores = neighbor_ratings.groupby("movieId").agg(
        neighbor_count=("userId", "count"),
        avg_neighbor_rating=("rating", "mean")
    ).reset_index()

    candidate_scores = candidate_scores.sort_values(
        ["neighbor_count", "avg_neighbor_rating"],
        ascending=False
    ).head(N_CANDIDATES)

    # Merge in titles
    candidates = candidate_scores.merge(movies_df[["movieId", "title"]], on="movieId")

    # Clean up title format — extract year and strip it from title
    candidates["year"] = candidates["title"].str.extract(r'\((\d{4})\)$')
    candidates["title"] = candidates["title"].str.replace(r'\s*\(\d{4}\)$', '', regex=True).str.strip()

    print(f"Returning {len(candidates)} candidate films")
    return candidates.to_dict(orient="records")


if __name__ == "__main__":
    # Quick test with a handful of well-known films
    test_films = [
        {"title": "The Godfather", "year": "1972", "rating": 5.0},
        {"title": "Goodfellas", "year": "1990", "rating": 5.0},
        {"title": "The Shawshank Redemption", "year": "1994", "rating": 4.5},
        {"title": "Pulp Fiction", "year": "1994", "rating": 4.5},
        {"title": "No Country for Old Men", "year": "2007", "rating": 4.5},
        {"title": "There Will Be Blood", "year": "2007", "rating": 4.0},
        {"title": "Fargo", "year": "1996", "rating": 4.0},
        {"title": "The Silence of the Lambs", "year": "1991", "rating": 4.0},
        {"title": "Se7en", "year": "1995", "rating": 4.0},
        {"title": "Blood Simple", "year": "1984", "rating": 3.5},
    ]

    candidates = get_candidates(test_films)
    for c in candidates[:10]:
        print(c)
