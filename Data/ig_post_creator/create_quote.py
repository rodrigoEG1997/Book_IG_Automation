from PIL import Image, ImageDraw, ImageFont, ImageEnhance
import os
from config.settings import *

BACKGROUND = "media/backgrounds/background_3.jpg"
OUTPUT     = "quote_post.png"
QUOTE      = "You think when you wake up in the mornin yesterday don't count. But yesterday is all that does count. What else is there? Your life is made out of the days it’s made out of. Nothin else."
#QUOTE      = "Some people are born into families that encourage education; others are against it. Some are born into flourishing economies encouraging of entrepreneurship; others are born into war and destitution. I want you to be successful, and I want you to earn it. But realize that not all success is due to hard work, and not all poverty is due to laziness. Keep this in mind when judging people, including yourself."
AUTHOR     = "Cormac McCarthy"

def load_font(size, index=0):
    if os.path.exists(PALATINO):
        return ImageFont.truetype(PALATINO, size, index=index)
    for path in FONT_FALLBACKS:
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def wrap_text(text, font, max_px, draw):
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


def cover_crop(img, target_w, target_h, anchor_y=0.5, zoom=1.0):
    """Resize + crop to fill target dimensions.
    anchor_y: 0.0=top  0.5=center  1.0=bottom
    zoom: 1.0=normal  1.5=50% closer  2.0=double zoom"""
    src_w, src_h = img.size
    scale = max(target_w / src_w, target_h / src_h) * zoom
    new_w = int(src_w * scale)
    new_h = int(src_h * scale)
    img = img.resize((new_w, new_h), Image.LANCZOS)
    left = (new_w - target_w) // 2
    top  = int(max(0, new_h - target_h) * anchor_y)
    return img.crop((left, top, left + target_w, top + target_h))


def apply_matte_filter(img, saturation):
    """Reduce color saturation so vivid backgrounds look soft and muted."""
    r, g, b, a = img.split()
    rgb = ImageEnhance.Color(Image.merge("RGB", (r, g, b))).enhance(saturation)
    r2, g2, b2 = rgb.split()
    return Image.merge("RGBA", (r2, g2, b2, a))


def build_band_overlay(width, height, color, max_opacity,
                       center_frac, band_frac, fade_frac):
    """Horizontal band overlay: fully opaque in the centre, fades at top & bottom."""
    overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    pixels  = overlay.load()

    cy         = height * center_frac
    half_solid = height * band_frac / 2
    fade_px    = height * fade_frac

    top_solid    = cy - half_solid
    bottom_solid = cy + half_solid
    top_fade     = top_solid    - fade_px
    bottom_fade  = bottom_solid + fade_px

    for y in range(height):
        if y < top_fade or y > bottom_fade:
            alpha = 0
        elif y < top_solid:
            alpha = int(max_opacity * (y - top_fade) / fade_px)
        elif y > bottom_solid:
            alpha = int(max_opacity * (bottom_fade - y) / fade_px)
        else:
            alpha = max_opacity
        for x in range(width):
            pixels[x, y] = (*color, alpha)

    return overlay


def create_quote_image(bg_path, quote, author, out_path):
    base_img = cover_crop(
        Image.open(bg_path).convert("RGBA"), OUTPUT_W, OUTPUT_H, CROP_ANCHOR, ZOOM
    )
    base_img = apply_matte_filter(base_img, SATURATION)

    # Work at SCALE× for crisp text
    sw, sh = OUTPUT_W * SCALE, OUTPUT_H * SCALE
    canvas = base_img.resize((sw, sh), Image.LANCZOS).convert("RGBA")

    # ── Overlay band ──────────────────────────────────────────
    overlay = build_band_overlay(
        sw, sh, OVERLAY_COLOR, OVERLAY_OPACITY,
        BAND_CENTER, BAND_HEIGHT, BAND_FADE,
    )
    canvas = Image.alpha_composite(canvas, overlay)

    # ── Fonts: auto-shrink until text fits inside the band ───
    MAX_QUOTE_SIZE = int(sw * 0.072)
    MIN_QUOTE_SIZE = int(sw * 0.028)
    AUTHOR_SIZE    = int(sw * 0.044)
    available_h    = int(sh * (BAND_HEIGHT + BAND_FADE))

    ml    = int(sw * MARGIN_LEFT)
    max_w = int(sw * TEXT_AREA_W)
    draw  = ImageDraw.Draw(canvas)
    a_font = load_font(AUTHOR_SIZE, index=2)   # Palatino Bold

    quote_size = MAX_QUOTE_SIZE
    while quote_size >= MIN_QUOTE_SIZE:
        line_gap   = int(quote_size * 0.45)
        author_gap = int(quote_size * 0.90)
        q_font = load_font(quote_size, index=3)   # Palatino BoldItalic
        lines  = wrap_text(f"“{quote}”", q_font, max_w, draw)
        total_h = len(lines) * (quote_size + line_gap) - line_gap + author_gap + AUTHOR_SIZE
        if total_h <= available_h:
            break
        quote_size -= int(sw * 0.002)

    # Centre text block on the band centre
    y = int(sh * BAND_CENTER - total_h / 2)

    # ── Quote lines ───────────────────────────────────────────
    for line in lines:
        draw.text((ml, y), line, font=q_font, fill=TEXT_COLOR)
        y += quote_size + line_gap

    # ── Author ────────────────────────────────────────────────
    y += author_gap - line_gap
    draw.text((ml, y), f"— {author}", font=a_font, fill=AUTHOR_COLOR)

    # ── Downscale to final output size ───────────────────────
    final = canvas.convert("RGB").resize((OUTPUT_W, OUTPUT_H), Image.LANCZOS)
    final.save(out_path, quality=85)
    print(f"Saved → {out_path}  ({OUTPUT_W}×{OUTPUT_H} px)")

def call_me():
    print("ENTRAMOOOOOOS")
    base = os.path.dirname(os.path.abspath(__file__))
    print(base)
    print(os.path.join(base, BACKGROUND))
    print(os.path.join(base, OUTPUT))
    create_quote_image(
        os.path.join(base, BACKGROUND),
        QUOTE,
        AUTHOR,
        os.path.join(base, OUTPUT),
    )

# if __name__ == "__main__":
#     base = os.path.dirname(os.path.abspath(__file__))
#     print(base)
#     print(os.path.join(base, BACKGROUND))
#     print(os.path.join(base, OUTPUT))
#     create_quote_image(
#         os.path.join(base, BACKGROUND),
#         QUOTE,
#         AUTHOR,
#         os.path.join(base, OUTPUT),
#     )