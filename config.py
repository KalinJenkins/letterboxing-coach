import os
from dotenv import load_dotenv

load_dotenv()

# TMDB
TMDB_API_KEY = os.getenv("TMDB_API_KEY")
TMDB_ACCESS_TOKEN = os.getenv("TMDB_ACCESS_TOKEN")
TMDB_IMAGE_BASE = "https://image.tmdb.org/t/p/w300"
TMDB_ATTRIBUTION = "This application uses TMDB and the TMDB APIs but is not endorsed, certified, or otherwise approved by TMDB."

# MovieLens
MOVIELENS_DIR = "data/ml-25m"
MIN_USER_RATINGS = 50
N_NEIGHBORS = 20
N_CANDIDATES = 100

# Scorer
TASTE_THRESHOLD = 3.5
WEIGHTS = {
    "genre": 2.0,
    "director": 3.0,
    "keyword": 1.0,
    "cast": 0.5,
    "language": 1.5,
}

# Reporter
TOP_N_RESULTS = 25

# Flask
UPLOAD_FOLDER = "uploads"
ALLOWED_EXTENSIONS = {"csv"}
SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key")
