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

    bg.save(post_path, quality=85)

def create_author_img(origin_path, post_path, description, name):
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

    # ── Text ──────────────────────────────────────────────────
    draw      = ImageDraw.Draw(canvas)
    margin    = int(CANVAS_W * 0.08)
    max_w     = CANVAS_W - margin * 2

    desc_main, parenthetical = _split_parenthetical(description)

    font_name  = _load_serif(int(CANVAS_W * 0.065), index=1)   # Palatino Italic – large
    font_desc  = _load_serif(int(CANVAS_W * 0.036), index=0)   # Palatino Regular – small
    line_h_name = int(CANVAS_W * 0.065 * 1.4)
    line_h_desc = int(CANVAS_W * 0.036 * 1.5)
    gap         = int(CANVAS_H * 0.022)

    lines_name  = _wrap_text(name, font_name, max_w, draw)
    lines_desc  = _wrap_text(desc_main, font_desc, max_w, draw)
    lines_paren = _wrap_text(parenthetical, font_desc, max_w, draw) if parenthetical else []

    all_desc_lines = lines_desc + lines_paren   # description + parenthetical together

    total_h = (len(lines_name) * line_h_name
               + gap + len(all_desc_lines) * line_h_desc)

    # Don't let the block start above 72% of the canvas (avoids covering the face)
    min_y   = int(CANVAS_H * 0.72)
    y       = max(min_y, CANVAS_H - margin - total_h)

    for line in lines_name:
        x = (CANVAS_W - draw.textlength(line, font=font_name)) // 2
        _draw_text_with_shadow(draw, (x, y), line, font_name, fill=(255, 255, 255, 240))
        y += line_h_name

    y += gap

    for line in all_desc_lines:
        x = (CANVAS_W - draw.textlength(line, font=font_desc)) // 2
        _draw_text_with_shadow(draw, (x, y), line, font_desc, fill=(220, 220, 220, 220))
        y += line_h_desc

    canvas.convert("RGB").save(post_path, quality=85)
