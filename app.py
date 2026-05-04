import os
import uuid
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for
from config import (
    TMDB_ATTRIBUTION,
    UPLOAD_FOLDER,
    ALLOWED_EXTENSIONS,
    SECRET_KEY,
    TOP_N_RESULTS
)
from parser import parse_letterboxd_csv
from tmdb_client import enrich_films
from movielens import get_candidates
from scorer import rank_candidates
from tmdb_client import get_film_metadata, search_film

app = Flask(__name__)
app.secret_key = SECRET_KEY
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def ensure_upload_folder():
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)


@app.route("/")
def index():
    return render_template("index.html", tmdb_attribution=TMDB_ATTRIBUTION)


@app.route("/upload", methods=["POST"])
def upload():
    ensure_upload_folder()

    # Validate file was included
    if "csv_file" not in request.files:
        return render_template("index.html",
                               error="No file selected.",
                               tmdb_attribution=TMDB_ATTRIBUTION)

    file = request.files["csv_file"]

    if file.filename == "":
        return render_template("index.html",
                               error="No file selected.",
                               tmdb_attribution=TMDB_ATTRIBUTION)

    if not allowed_file(file.filename):
        return render_template("index.html",
                               error="Please upload a CSV file.",
                               tmdb_attribution=TMDB_ATTRIBUTION)

    # Save uploaded file temporarily with unique name
    temp_filename = f"{uuid.uuid4().hex}.csv"
    temp_path = os.path.join(UPLOAD_FOLDER, temp_filename)
    file.save(temp_path)

    try:
        # Step 1 — Parse the CSV
        print("Step 1: Parsing CSV...")
        user_films = parse_letterboxd_csv(temp_path)

        if not user_films:
            return render_template("index.html",
                                   error="No rated films found in your CSV. Make sure you uploaded ratings.csv.",
                                   tmdb_attribution=TMDB_ATTRIBUTION)

        # Step 2 — Enrich with TMDB metadata
        print("Step 2: Enriching with TMDB metadata...")
        enriched_films = enrich_films(user_films)

        # Step 3 — Get collaborative filtering candidates
        print("Step 3: Finding collaborative filtering candidates...")
        candidates = get_candidates(user_films)

        if not candidates:
            return render_template("index.html",
                                   error="Could not find enough matching films in MovieLens. Try again with a larger export.",
                                   tmdb_attribution=TMDB_ATTRIBUTION)

        # Step 4 — Enrich candidates with TMDB metadata
        print("Step 4: Enriching candidates with TMDB metadata...")
        candidate_metadata = []
        for candidate in candidates:
            tmdb_id = search_film(candidate["title"], candidate.get("year", ""))
            if tmdb_id:
                meta = get_film_metadata(tmdb_id)
                if meta:
                    candidate_metadata.append(meta)

        # Step 5 — Score and rank
        print("Step 5: Scoring and ranking...")
        ranked = rank_candidates(candidates, enriched_films, candidate_metadata)

        # Step 6 — Render results
        return render_template(
            "results.html",
            films=ranked[:TOP_N_RESULTS],
            film_count=len(user_films),
            generated_at=datetime.now().strftime("%B %d, %Y at %I:%M %p"),
            tmdb_attribution=TMDB_ATTRIBUTION
        )

    except Exception as e:
        print(f"Pipeline error: {e}")
        return render_template("index.html",
                               error=f"Something went wrong processing your file: {str(e)}",
                               tmdb_attribution=TMDB_ATTRIBUTION)

    finally:
        # Always clean up the temp file
        if os.path.exists(temp_path):
            os.remove(temp_path)


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
