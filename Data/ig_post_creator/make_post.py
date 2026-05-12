from ig_post_creator.create_quote import create_quote_image
from ig_post_creator.helpers import create_img_book, create_author_img
import os
import glob
import time
import json
import subprocess
from config.settings import OUTPUT_POST, BACKGROUND_QUOTE
import logging
from db import queries
from db.connection import get_connection

_CAROUSEL_VIDEO_DURATION = 7


def _create_carousel_video(image_path, song_path, output_path):
    cmd = [
        "ffmpeg", "-y",
        "-loop", "1", "-i", image_path,
        "-i", song_path,
        "-vf", "scale=1080:1350:force_original_aspect_ratio=decrease,"
               "pad=1080:1350:(ow-iw)/2:(oh-ih)/2:color=black",
        "-c:v", "libx264", "-profile:v", "high", "-level", "4.0",
        "-r", "30", "-b:v", "5000k",
        "-c:a", "aac", "-b:a", "192k",
        "-t", str(_CAROUSEL_VIDEO_DURATION), "-shortest",
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
        output_path,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg failed for {output_path}:\n{result.stderr}")
    print(f"  Carousel video created: {output_path}")


def _is_clean_subject(s: str) -> bool:
    skip_any = ('award:', 'nyt:', 'Reading Level', 'open_syllabus', '(fictional works', '--fiction', ', fiction')
    if any(p in s for p in skip_any):
        return False
    if not s or s[0].isdigit() or '=' in s:
        return False
    # call-number heuristic: period followed by a lowercase letter
    if any(c == '.' and i + 1 < len(s) and s[i + 1].islower() for i, c in enumerate(s)):
        return False
    return len(s) <= 35


def _to_hashtag(s: str) -> str:
    return '#' + ''.join(w.capitalize() for w in s.replace(',', '').replace("'", '').replace('-', ' ').split())


def create_caption(book, author) -> str:
    MAX_CHARS = 2200

    # Subjects → 4 clean hashtags
    try:
        subjects_raw = json.loads(book.get('subjects') or '[]')
    except (json.JSONDecodeError, TypeError):
        subjects_raw = []
    top_subjects = [s for s in subjects_raw if _is_clean_subject(s)][:4]
    hashtags = ' '.join(_to_hashtag(s) for s in top_subjects)

    # Links (plain URLs only)
    try:
        links_raw = json.loads(book.get('links') or '[]')
    except (json.JSONDecodeError, TypeError):
        links_raw = []
    link_lines = []
    for lnk in links_raw[:3]:
        if isinstance(lnk, dict) and 'url' in lnk:
            link_lines.append(lnk['url'])
        elif isinstance(lnk, str) and lnk.startswith('http'):
            link_lines.append(lnk)

    # Fields
    title       = book.get('title', '')
    author_name = author.get('name', '')
    year        = book.get('first_publish_year', '')
    rating      = book.get('ratings_average')
    rating_cnt  = book.get('ratings_count', 0)
    description = (book.get('description') or '').strip()
    author_desc = (author.get('description') or '').strip()
    wiki_url    = (author.get('wikipedia_url') or '').strip()

    rating_str = f"{float(rating):.1f}/5 ⭐" if rating else "N/A"

    # Truncate description so the whole caption stays under the limit
    desc_limit = 350
    if len(description) > desc_limit:
        description = description[:desc_limit].rsplit(' ', 1)[0] + '...'

    year_str = f'  ·  {year}' if year else ''
    lines = [
        f'⭐ {rating_str}  ({rating_cnt} ratings)',
        '',
        f'📖 "{title}"',
        f'✍️  {author_name}{year_str}',
        '',
        description,
    ]

    if hashtags:
        lines += ['', hashtags]

    if link_lines:
        lines += ['', '🔗 ' + '  '.join(link_lines)]

    lines += [
        '',
        '─' * 18,
        f'👤 {author_name} — {author_desc}',
    ]
    if wiki_url:
        lines.append(wiki_url)

    caption = '\n'.join(lines)

    if len(caption) > MAX_CHARS:
        caption = caption[:MAX_CHARS - 3] + '...'

    return caption

def make_post(connection, cursor, base, song_path):

    #Delete Old Post
    old_post = os.path.join(base, OUTPUT_POST, "*")

    for file in glob.glob(old_post):
        os.remove(file)

    time.sleep(1)

    #Get Data
    id_book = queries.get_random_id_book(cursor)
    book = queries.get_book(cursor, id_book)
    author = queries.get_author(cursor, book['id_Author'])
    num_bg = int(queries.get_background(cursor))

    #Create Book Image
    path_book = book["img_book"].replace("Data", base, 1)
    book_post = os.path.join(base, OUTPUT_POST, "book.png")
    create_img_book(path_book, book_post)

    #Create Quotes
    background = f"background_{num_bg}.jpg"
    for i in range(1, 6):
        quote = book[f"quote_{i}"]
        output = f"quote_{i}.png"
        if quote:
            create_quote_image(os.path.join(base, BACKGROUND_QUOTE, background),
                    quote,
                    author['name'],
                    os.path.join(base, OUTPUT_POST, output))

    #Create Author Image
    path_book = author["img_author"].replace("Data", base, 1)
    author_post = os.path.join(base, OUTPUT_POST, "author.png")
    create_author_img(path_book, author_post, author["description"], author["name"])

    #Convert images to videos with music
    post_dir = os.path.join(base, OUTPUT_POST)
    for img_file in sorted(os.listdir(post_dir)):
        if img_file.endswith(".png"):
            img_path = os.path.join(post_dir, img_file)
            vid_path = os.path.join(post_dir, img_file.replace(".png", ".mp4"))
            _create_carousel_video(img_path, song_path, vid_path)

    caption = create_caption(book, author)

    num_bg = 1 if num_bg > 430 else num_bg + 1

    queries.update_book_available(connection, cursor, id_book)
    queries.update_background(connection, cursor, num_bg)

    return caption, author['name'], book['quote_1']