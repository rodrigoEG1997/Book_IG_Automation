from .endpoints import search_author as endpoint_search_author
import math

def search_author(client, name):

    paramSearchAuthor= endpoint_search_author(name)
    response = client.get(
            endpoint=paramSearchAuthor["endpoint"],
            params = paramSearchAuthor["params"]
        )

    if response is None:
        return None

    docs = response.get("docs", [])

    if not docs:
        return None

    # Try exact match
    for author in docs:
        if author["name"].lower() == name.lower():
            return author['key']

    # if not, take the most similar words one
    best_match = sorted(
        docs,
        key=lambda x: x.get("work_count", 0),
        reverse=True
    )[0]

    return best_match['key']

def extract_bio(bio):
    if isinstance(bio, dict):
        return bio.get("value")
    return bio

def top_books(response, num):
    import math

    docs = response.get("docs", [])
    if not docs:
        return []

    # ── Deduplicar por título y filtrar sin portada ───────────
    seen_titles = set()
    candidates = []

    for book in docs:
        title = book.get("title")
        if not title or title.lower() in seen_titles:
            continue
        if not book.get("cover_i"):
            continue
        seen_titles.add(title.lower())
        candidates.append(book)

    # ── Score de popularidad combinado ────────────────────────
    def safe_log(val):
        return math.log(max(val or 0, 1) + 1)

    max_log_ratings = max((safe_log(b.get("ratings_count",      0)) for b in candidates), default=1) or 1
    max_log_want    = max((safe_log(b.get("want_to_read_count", 0)) for b in candidates), default=1) or 1

    def popularity_score(book):
        avg   = book.get("ratings_average")    or 0
        count = book.get("ratings_count")       or 0
        want  = book.get("want_to_read_count")  or 0
        return (
            (avg / 5.0)                            * 0.40 +
            (safe_log(count) / max_log_ratings)    * 0.35 +
            (safe_log(want)  / max_log_want)       * 0.25
        )

    # ── Ordenar y devolver top 5 ──────────────────────────────
    candidates.sort(key=popularity_score, reverse=True)

    results = []
    for book in candidates[:5]:
        results.append({
            "title":              book.get("title"),
            "work_key":           book.get("key"),
            "first_publish_year": book.get("first_publish_year"),
            "edition_count":      book.get("edition_count"),
            "cover_id":           book.get("cover_i"),
            "cover_url":          f"https://covers.openlibrary.org/b/id/{book['cover_i']}-L.jpg",
            "ratings_average":    book.get("ratings_average"),
            "ratings_count":      book.get("ratings_count"),
            "want_to_read_count": book.get("want_to_read_count"),
            "first_sentence":     book.get("first_sentence"),
        })

    return results

def merge_book(book, book_details):

    description = book_details.get("description", "")
    if isinstance(description, dict):
        description = description.get("value", "")

    return {
        "title":              book.get("title"),
        "work_key":           book.get("work_key"),
        "first_publish_year": book.get("first_publish_year"),
        "edition_count":      book.get("edition_count"),
        "cover_id":           book.get("cover_id"),
        "cover_url":          book.get("cover_url"),
        "ratings_average":    book.get("ratings_average"),
        "ratings_count":      book.get("ratings_count"),
        "want_to_read_count": book.get("want_to_read_count"),
        "first_sentence":     book.get("first_sentence"),
        "description":        description,
        "subjects":           book_details.get("subjects", []),
        "links":              book_details.get("links", []),
    }
