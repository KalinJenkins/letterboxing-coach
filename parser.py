import csv
import io

REQUIRED_COLUMNS = {"Name", "Year", "Rating"}

def parse_letterboxd_csv(file) -> list[dict]:
    films = []

    if isinstance(file, str):
        f = open(file, "r", encoding="utf-8")
    else:
        f = io.TextIOWrapper(file, encoding="utf-8")

    try:
        reader = csv.DictReader(f)

        if not REQUIRED_COLUMNS.issubset(set(reader.fieldnames or [])):
            raise ValueError(f"CSV missing required columns. Expected: {REQUIRED_COLUMNS}")

        for row in reader:
            title = row["Name"].strip()
            year = row["Year"].strip()
            rating_raw = row["Rating"].strip()

            if not title or not rating_raw:
                continue

            try:
                rating = float(rating_raw)
            except ValueError:
                continue

            films.append({
                "title": title,
                "year": year,
                "rating": rating
            })

    finally:
        if isinstance(file, str):
            f.close()

    print(f"Parsed {len(films)} rated films from CSV")
    return films


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python parser.py ratings.csv")
        sys.exit(1)

    films = parse_letterboxd_csv(sys.argv[1])
    for f in films[:10]:
        print(f)
