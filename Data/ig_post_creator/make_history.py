import os
import random
import subprocess
import time
import requests
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance, ImageFont
from config.settings import POST_BASE_URL, API_VERSION, IG_USER_ID, OUTPUT_POST, FONT_FALLBACKS, SANS_FALLBACKS
from ig_connector.post_content import _wait_until_ready

_STORY_W             = 1080
_STORY_H             = 1920
_STORY_DURATION      = 15
_SONGS_PATH          = "media/songs"
_STORY_RETRY_WAIT    = 15
_STORY_MAX_PUB_TRIES = 3


def _load_font(size):
    for path in FONT_FALLBACKS + SANS_FALLBACKS:
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def _wrap_text(text, font, max_px, draw):
    words = text.split()
    lines, line = [], ""
    for word in words:
        candidate = f"{line} {word}".strip()
        if draw.textlength(candidate, font=font) <= max_px:
            line = candidate
        else:
            if line:
                lines.append(line)
            line = word
    if line:
        lines.append(line)
    return lines


def _draw_centered(draw, lines, font, y, fill, shadow=3):
    for line in lines:
        tw = draw.textlength(line, font=font)
        x = int((_STORY_W - tw) // 2)
        draw.text((x + shadow, y + shadow), line, font=font, fill=(0, 0, 0, 160))
        draw.text((x, y), line, font=font, fill=fill)
        y += font.size + 14
    return y


def _create_story_image(book_path, output_path, author, quote):
    book = Image.open(book_path).convert("RGB")

    bg_scale = max(_STORY_W / book.width, _STORY_H / book.height)
    bg = book.resize(
        (int(book.width * bg_scale), int(book.height * bg_scale)), Image.LANCZOS
    )
    left = (bg.width  - _STORY_W) // 2
    top  = (bg.height - _STORY_H) // 2
    bg = bg.crop((left, top, left + _STORY_W, top + _STORY_H))
    bg = bg.filter(ImageFilter.GaussianBlur(radius=25))
    bg = ImageEnhance.Brightness(bg).enhance(0.45)
    canvas = bg.convert("RGBA")

    padding = 100
    max_w = _STORY_W - padding * 2
    max_h = int(_STORY_H * 0.58)
    scale = min(max_w / book.width, max_h / book.height)
    book_resized = book.resize(
        (int(book.width * scale), int(book.height * scale)), Image.LANCZOS
    ).convert("RGBA")
    bx = (_STORY_W - book_resized.width) // 2
    by = int(_STORY_H * 0.05)
    canvas.paste(book_resized, (bx, by), book_resized)

    gradient = Image.new("RGBA", (_STORY_W, _STORY_H), (0, 0, 0, 0))
    pixels = gradient.load()
    grad_start = int(_STORY_H * 0.60)
    for y in range(_STORY_H):
        if y >= grad_start:
            alpha = int(220 * (y - grad_start) / (_STORY_H - grad_start))
            for x in range(_STORY_W):
                pixels[x, y] = (0, 0, 0, alpha)
    canvas = Image.alpha_composite(canvas, gradient)

    draw        = ImageDraw.Draw(canvas)
    font_quote  = _load_font(44)
    font_author = _load_font(58)
    max_text_w  = _STORY_W - padding * 2

    quote_lines  = _wrap_text(f'"{quote}"', font_quote,  max_text_w, draw)
    author_lines = _wrap_text(f"— {author}", font_author, max_text_w, draw)

    quote_block_h  = len(quote_lines)  * (font_quote.size  + 14)
    author_block_h = len(author_lines) * (font_author.size + 14)
    gap     = 28
    total_h = quote_block_h + gap + author_block_h

    # Center the text block in the space below the book cover
    text_area_top    = by + book_resized.height + 40
    text_area_bottom = _STORY_H - 80
    y_start = text_area_top + (text_area_bottom - text_area_top - total_h) // 2

    y = _draw_centered(draw, quote_lines,  font_quote,  y_start, fill=(230, 230, 230, 240))
    y += gap
    _draw_centered(draw, author_lines, font_author, y, fill=(255, 255, 255, 255))

    canvas.convert("RGB").save(output_path, quality=97)
    print(f"  Story image created: {output_path}")


def _pick_random_song(base):
    songs_dir = os.path.join(base, _SONGS_PATH)
    songs = [f for f in os.listdir(songs_dir) if f.lower().endswith(".mp3")]
    if not songs:
        raise RuntimeError(f"No .mp3 files found in {songs_dir}")
    chosen = random.choice(songs)
    print(f"  Song selected: {chosen}")
    return os.path.join(songs_dir, chosen)


def _create_story_video(image_path, song_path, output_path):
    cmd = [
        "ffmpeg", "-y",
        "-loop", "1", "-i", image_path,
        "-i", song_path,
        "-vf", "scale=1080:1920:force_original_aspect_ratio=decrease,"
               "pad=1080:1920:(ow-iw)/2:(oh-ih)/2:color=black",
        "-c:v", "libx264", "-tune", "stillimage",
        "-c:a", "aac", "-b:a", "192k",
        "-t", str(_STORY_DURATION), "-shortest",
        "-pix_fmt", "yuv420p",
        output_path,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg failed:\n{result.stderr}")
    print(f"  Story video created: {output_path}")


def _get_permalink(post_id, access_token):
    res = requests.get(
        f"https://graph.facebook.com/{API_VERSION}/{post_id}",
        params={"fields": "permalink", "access_token": access_token},
    ).json()
    if "permalink" not in res:
        raise RuntimeError(f"Could not fetch permalink for post {post_id}: {res}")
    return res["permalink"]


def post_story(post_id, access_token, base, author, quote):
    permalink = _get_permalink(post_id, access_token)
    print(f"  Story link → {permalink}")

    book_path  = os.path.join(base, OUTPUT_POST, "book.png")
    image_path = os.path.join(base, OUTPUT_POST, "story.png")
    video_path = os.path.join(base, OUTPUT_POST, "story.mp4")

    _create_story_image(book_path, image_path, author, quote)
    song_path = _pick_random_song(base)
    _create_story_video(image_path, song_path, video_path)

    story_video_url = POST_BASE_URL + f"/story.mp4?t={int(time.time())}"

    container_payload = {
        "media_type": "STORIES",
        "video_url":  story_video_url,
        "access_token": access_token,
    }
    container = requests.post(
        f"https://graph.facebook.com/{API_VERSION}/{IG_USER_ID}/media",
        data=container_payload,
    ).json()
    print("Story container response:", container)

    if "id" not in container:
        raise RuntimeError(f"Failed to create story container: {container}")

    publish_payload = {
        "creation_id": container["id"],
        "access_token": access_token,
    }

    for attempt in range(1, _STORY_MAX_PUB_TRIES + 1):
        _wait_until_ready(container["id"], access_token)

        published = requests.post(
            f"https://graph.facebook.com/{API_VERSION}/{IG_USER_ID}/media_publish",
            data=publish_payload,
        ).json()

        if "error" not in published:
            print("Story published:", published)
            return published

        print(f"  Story publish attempt {attempt}/{_STORY_MAX_PUB_TRIES} failed: {published['error']['message']}")
        if attempt < _STORY_MAX_PUB_TRIES:
            print(f"  Retrying in {_STORY_RETRY_WAIT}s...")
            time.sleep(_STORY_RETRY_WAIT)

    raise RuntimeError(f"Failed to publish story after {_STORY_MAX_PUB_TRIES} attempts. Last response: {published}")
