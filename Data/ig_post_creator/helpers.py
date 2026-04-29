from PIL import Image, ImageDraw, ImageFilter, ImageEnhance
from config.settings import CANVAS_W, CANVAS_H, PADDING, PALATINO, FONT_FALLBACKS, SANS_FALLBACKS
from PIL import ImageFont
import os

def _load_serif(size, index=1):
    if os.path.exists(PALATINO):
        return ImageFont.truetype(PALATINO, size, index=index)
    for path in FONT_FALLBACKS:
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()

def _load_sans(size):
    for path in SANS_FALLBACKS:
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

def _split_parenthetical(text):
    if text.endswith(")"):
        idx = text.rfind("(")
        if idx != -1:
            return text[:idx].strip(), text[idx:]
    return text, None

def _draw_text_with_shadow(draw, pos, text, font, fill, shadow_offset=4, shadow_color=(0, 0, 0, 180)):
    sx, sy = pos[0] + shadow_offset, pos[1] + shadow_offset
    draw.text((sx, sy), text, font=font, fill=shadow_color)
    draw.text(pos, text, font=font, fill=fill)

def create_img_book(origin_path, post_path):
    img = Image.open(origin_path).convert("RGB")

    # ── Blurred background: scale to fill the canvas ──────────
    bg_scale = max(CANVAS_W / img.width, CANVAS_H / img.height)
    bg = img.resize(
        (int(img.width * bg_scale), int(img.height * bg_scale)),
        Image.LANCZOS
    )
    left = (bg.width  - CANVAS_W) // 2
    top  = (bg.height - CANVAS_H) // 2
    bg = bg.crop((left, top, left + CANVAS_W, top + CANVAS_H))
    bg = bg.filter(ImageFilter.GaussianBlur(radius=30))
    bg = ImageEnhance.Brightness(bg).enhance(0.5)

    # ── Book cover: scale to fit inside canvas with padding ───
    max_w = CANVAS_W - PADDING * 2
    max_h = CANVAS_H - PADDING * 2
    book_scale = min(max_w / img.width, max_h / img.height)
    book = img.resize(
        (int(img.width * book_scale), int(img.height * book_scale)),
        Image.LANCZOS
    )

    # ── Paste centered ────────────────────────────────────────
    x = (CANVAS_W - book.width)  // 2
    y = (CANVAS_H - book.height) // 2
    bg.paste(book, (x, y))

    bg.save(post_path, quality=97)

def create_author_img(origin_path, post_path, description):
    img = Image.open(origin_path).convert("RGB")

    # ── Cover crop to fill canvas ─────────────────────────────
    bg_scale = max(CANVAS_W / img.width, CANVAS_H / img.height)
    canvas = img.resize(
        (int(img.width * bg_scale), int(img.height * bg_scale)),
        Image.LANCZOS
    )
    left = (canvas.width  - CANVAS_W) // 2
    top  = (canvas.height - CANVAS_H) // 2
    canvas = canvas.crop((left, top, left + CANVAS_W, top + CANVAS_H))
    canvas = canvas.convert("RGBA")

    # ── Dark gradient from 45% height to bottom ───────────────
    gradient = Image.new("RGBA", (CANVAS_W, CANVAS_H), (0, 0, 0, 0))
    pixels   = gradient.load()
    grad_start = int(CANVAS_H * 0.45)
    for y in range(CANVAS_H):
        if y >= grad_start:
            alpha = int(210 * (y - grad_start) / (CANVAS_H - grad_start))
            for x in range(CANVAS_W):
                pixels[x, y] = (0, 0, 0, alpha)

    canvas = Image.alpha_composite(canvas, gradient)

    # ── Description text ──────────────────────────────────────
    draw      = ImageDraw.Draw(canvas)
    margin    = int(CANVAS_W * 0.08)
    max_w     = CANVAS_W - margin * 2

    main, parenthetical = _split_parenthetical(description)

    font_main  = _load_serif(int(CANVAS_W * 0.052), index=1)   # Palatino Italic
    font_small = _load_serif(int(CANVAS_W * 0.036), index=0)   # Palatino Regular
    line_h1    = int(CANVAS_W * 0.052 * 1.5)
    line_h2    = int(CANVAS_W * 0.036 * 1.5)
    gap        = int(CANVAS_H * 0.025)

    lines_main  = _wrap_text(main, font_main, max_w, draw)
    lines_small = _wrap_text(parenthetical, font_small, max_w, draw) if parenthetical else []

    total_h = len(lines_main) * line_h1
    if lines_small:
        total_h += gap + len(lines_small) * line_h2

    y = CANVAS_H - margin - total_h

    for line in lines_main:
        x = (CANVAS_W - draw.textlength(line, font=font_main)) // 2
        _draw_text_with_shadow(draw, (x, y), line, font_main, fill=(255, 255, 255, 240))
        y += line_h1

    if lines_small:
        y += gap
        for line in lines_small:
            x = (CANVAS_W - draw.textlength(line, font=font_small)) // 2
            _draw_text_with_shadow(draw, (x, y), line, font_small, fill=(220, 220, 220, 210))
            y += line_h2

    canvas.convert("RGB").save(post_path, quality=97)
