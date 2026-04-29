# IG Quotes Automation

Automated pipeline that collects data about authors and their books, extracts quotes, and generates ready-to-post Instagram images — all running inside Docker.

## What it does

1. **Data collection** — fetches author bios and photos (Wikipedia), book metadata and cover images (OpenLibrary), and up to 5 quotes per book (Goodreads). Stores everything in a MySQL database.
2. **Post generation** — picks a random available book from the database and produces three types of Instagram images:
   - **Author card** — full-bleed author photo with name and description overlaid
   - **Book cover card** — book cover centered on a blurred background
   - **Quote cards** (×5) — styled quote text on an aesthetic background

## Project structure

```
IG_Quotes_Automation/
├── Data/
│   ├── config/
│   │   ├── settings.py          # All constants and env vars
│   │   └── authors_quotes.py    # List of authors to collect
│   ├── db/
│   │   ├── connection.py
│   │   ├── queries.py
│   │   └── modules/             # Author / Book model classes
│   ├── goodreads/               # Goodreads scraper (quotes)
│   ├── openlibrary/             # OpenLibrary API (books + covers)
│   ├── wikipedia/               # Wikipedia API (author bio + photo)
│   ├── pexels/                  # Pexels API (background images)
│   ├── ig_post_creator/
│   │   ├── create_quote.py      # Quote image renderer
│   │   └── helpers.py           # Book cover + author image renderers
│   ├── get_autors_books.py      # Data collection pipeline
│   ├── get_backgrounds.py       # Background image downloader
│   ├── make_post.py             # Post generation pipeline
│   └── Dockerfile
├── mysql-init/
│   └── init.sql                 # Database schema
├── logs/
├── docker-compose.yml
└── .env
```

## Database schema

| Table | Description |
|---|---|
| `Authors` | Author metadata: Wikipedia/OpenLibrary IDs, bio, photo path |
| `Books` | Book metadata + 5 quotes + cover path, linked to an author |
| `Variables` | Internal counters (e.g. background rotation index) |

## Setup

### 1. Environment variables

Create a `.env` file at the root:

```env
MYSQL_ROOT_PASSWORD=yourpassword
MYSQL_DATABASE=QUOTES_BOOKS
MYSQL_USER=youruser
MYSQL_PASSWORD=yourpassword
DB_HOST=mysql
DB_PORT=3306
PEXELS_API_KEY=your_pexels_api_key
```

### 2. Add authors

Edit `Data/config/authors_quotes.py` and add the authors you want to collect:

```python
TEST_AUTHORS = [
    "Toni Morrison",
    "Cormac McCarthy",
    "Philip Roth",
    "Don DeLillo",
]
```

### 3. Build the image

Only needed the first time, or when `requirements.txt` or `Dockerfile` changes:

```bash
docker compose --profile data-only build data
```

## Usage

### Collect authors, books and quotes

Fetches data for all authors in `authors_quotes.py` and stores it in the database:

```bash
docker compose --profile data-only run --rm data python get_autors_books.py
```

### Download background images

Downloads aesthetic background images from Pexels (run once):

```bash
docker compose --profile data-only run --rm data python get_backgrounds.py
```

### Generate Instagram post

Picks a random available book and generates all post images into `media/post/`:

```bash
docker compose --profile data-only run --rm data python make_post.py
```

Output files:
- `media/post/author.png` — author card
- `media/post/book.png` — book cover card
- `media/post/quote_1.png` … `quote_5.png` — quote cards

## API resilience

All external API clients (OpenLibrary, Goodreads, Wikipedia) include:
- **5 retries** with 30–60 second waits between attempts
- Specific handling for `502`, `503`, and SSL errors
- Graceful degradation: a failed book is skipped without stopping the entire run

## Tech stack

- **Python 3.11** inside Docker
- **MySQL 8.0** for storage
- **Pillow** for image generation
- **Requests** for all HTTP calls
- Wikipedia REST API, OpenLibrary API, Goodreads (scraping), Pexels API
