import os
from datetime import datetime

TMDB_IMAGE_BASE = "https://image.tmdb.org/t/p/w300"
TMDB_ATTRIBUTION = "This application uses TMDB and the TMDB APIs but is not endorsed, certified, or otherwise approved by TMDB."


def generate_report(ranked_films: list[dict], username: str = "you", top_n: int = 25) -> str:
    """
    Generates a self-contained HTML report of film recommendations.
    Returns the HTML as a string.
    """
    films = ranked_films[:top_n]
    generated_at = datetime.now().strftime("%B %d, %Y at %I:%M %p")

    cards = ""
    for i, film in enumerate(films):
        poster_path = film.get("poster_path")
        poster_url = f"{TMDB_IMAGE_BASE}{poster_path}" if poster_path else ""
        poster_html = (
            f'<img src="{poster_url}" alt="{film["title"]} poster" class="poster">'
            if poster_url else
            '<div class="poster no-poster">No Poster</div>'
        )

        genres = ", ".join(film.get("genres", []))
        director = film.get("director", "Unknown")
        year = film.get("year", "")
        runtime = film.get("runtime")
        runtime_str = f"{runtime} min" if runtime else "N/A"
        language = film.get("language", "").upper()
        neighbor_count = film.get("neighbor_count", 0)
        avg_rating = film.get("avg_neighbor_rating", 0)
        score = film.get("affinity_score", 0)

        cards += f"""
        <div class="card">
            <div class="rank">#{i + 1}</div>
            {poster_html}
            <div class="info">
                <h2>{film["title"]} <span class="year">({year})</span></h2>
                <div class="meta">
                    <span>🎬 {director}</span>
                    <span>🎭 {genres}</span>
                    <span>⏱ {runtime_str}</span>
                    <span>🌐 {language}</span>
                </div>
                <div class="stats">
                    <div class="stat">
                        <div class="stat-value">{neighbor_count}</div>
                        <div class="stat-label">neighbors loved it</div>
                    </div>
                    <div class="stat">
                        <div class="stat-value">{avg_rating:.2f}</div>
                        <div class="stat-label">avg neighbor rating</div>
                    </div>
                    <div class="stat">
                        <div class="stat-value">{score}</div>
                        <div class="stat-label">affinity score</div>
                    </div>
                </div>
            </div>
        </div>
        """

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Letterboxing Coach — Recommendations</title>
    <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            background: #1a1a2e;
            color: #eee;
            min-height: 100vh;
        }}

        header {{
            background: #16213e;
            padding: 2rem;
            text-align: center;
            border-bottom: 3px solid #e94560;
        }}

        header h1 {{
            font-size: 2rem;
            color: #e94560;
            letter-spacing: 2px;
            text-transform: uppercase;
        }}

        header p {{
            color: #aaa;
            margin-top: 0.5rem;
            font-size: 0.9rem;
        }}

        .container {{
            max-width: 900px;
            margin: 2rem auto;
            padding: 0 1rem;
        }}

        .card {{
            display: flex;
            gap: 1.5rem;
            background: #16213e;
            border-radius: 12px;
            padding: 1.5rem;
            margin-bottom: 1.5rem;
            position: relative;
            border: 1px solid #0f3460;
            transition: border-color 0.2s;
        }}

        .card:hover {{
            border-color: #e94560;
        }}

        .rank {{
            position: absolute;
            top: 1rem;
            right: 1rem;
            font-size: 1.5rem;
            font-weight: bold;
            color: #e94560;
            opacity: 0.6;
        }}

        .poster {{
            width: 100px;
            min-width: 100px;
            border-radius: 8px;
            object-fit: cover;
        }}

        .no-poster {{
            width: 100px;
            min-width: 100px;
            height: 150px;
            border-radius: 8px;
            background: #0f3460;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 0.75rem;
            color: #666;
        }}

        .info {{
            flex: 1;
        }}

        .info h2 {{
            font-size: 1.2rem;
            margin-bottom: 0.5rem;
        }}

        .year {{
            color: #aaa;
            font-weight: normal;
            font-size: 1rem;
        }}

        .meta {{
            display: flex;
            flex-wrap: wrap;
            gap: 0.75rem;
            margin-bottom: 1rem;
            font-size: 0.85rem;
            color: #aaa;
        }}

        .stats {{
            display: flex;
            gap: 1.5rem;
        }}

        .stat {{
            text-align: center;
        }}

        .stat-value {{
            font-size: 1.3rem;
            font-weight: bold;
            color: #e94560;
        }}

        .stat-label {{
            font-size: 0.7rem;
            color: #aaa;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}

        footer {{
            text-align: center;
            padding: 2rem;
            color: #555;
            font-size: 0.8rem;
            border-top: 1px solid #0f3460;
            margin-top: 2rem;
        }}

        footer img {{
            height: 20px;
            vertical-align: middle;
            margin-right: 0.5rem;
        }}
    </style>
</head>
<body>
    <header>
        <h1>🎬 Letterboxing Coach</h1>
        <p>Recommendations based on your Letterboxd ratings &mdash; generated {generated_at}</p>
    </header>

    <div class="container">
        {cards}
    </div>

    <footer>
        <p>{TMDB_ATTRIBUTION}</p>
    </footer>
</body>
</html>"""

    return html


def save_report(html: str, output_path: str = "report.html"):
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Report saved to {output_path}")


if __name__ == "__main__":
    # Mock test data
    mock_films = [
        {
            "title": "Fargo",
            "year": "1996",
            "director": "Joel Coen",
            "genres": ["Crime", "Drama"],
            "runtime": 98,
            "language": "en",
            "poster_path": "/lMrFbVEMNnTKP7SJm5cxhkCOqaF.jpg",
            "neighbor_count": 15,
            "avg_neighbor_rating": 4.5,
            "affinity_score": 23.85
        },
        {
            "title": "Chinatown",
            "year": "1974",
            "director": "Roman Polanski",
            "genres": ["Drama", "Crime", "Mystery"],
            "runtime": 130,
            "language": "en",
            "poster_path": "/jLMCLbMDZeiknXY5apDcGMOpOBA.jpg",
            "neighbor_count": 12,
            "avg_neighbor_rating": 4.3,
            "affinity_score": 18.29
        },
    ]

    html = generate_report(mock_films, username="shoebacca")
    save_report(html)
