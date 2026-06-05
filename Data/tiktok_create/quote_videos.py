import os
import glob
import random
import logging
import numpy as np
from PIL import Image as _PILImage, ImageDraw, ImageFont

# moviepy 1.x uses Image.ANTIALIAS which was removed in Pillow 10+
if not hasattr(_PILImage, "ANTIALIAS"):
    _PILImage.ANTIALIAS = _PILImage.LANCZOS

from moviepy.editor import (
    VideoFileClip, AudioFileClip, ColorClip, ImageClip,
    CompositeVideoClip,
)
import moviepy.audio.fx.all as afx
from config.settings import BACKGROUND_VIDEO_PATH

_TARGET_W         = 720
_TARGET_H         = 1280
_CLIP_DURATION    = 10
_FONT_SIZE_QUOTE  = 40
_FONT_SIZE_AUTHOR = 28
_FONT_SIZE_HANDLE = 24
_TEXT_MAX_W       = _TARGET_W - 100
_IG_HANDLE        = "@rod.littlebooks"

_BASE    = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_IG_LOGO = os.path.join(_BASE, "media", "ig.png")

_BOLD_FONT_PATHS = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    "/Library/Fonts/Arial Bold.ttf",
    "/System/Library/Fonts/Helvetica.ttc",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
]


def _load_font_path():
    for path in _BOLD_FONT_PATHS:
        if os.path.exists(path):
            return path
    raise RuntimeError("No compatible font found.")


def _wrap_text(text, font_path, font_size, max_px_width):
    font = ImageFont.truetype(font_path, font_size)
    words = text.split()
    lines, current = [], []
    for word in words:
        test = " ".join(current + [word])
        if font.getlength(test) <= max_px_width or not current:
            current.append(word)
        else:
            lines.append(" ".join(current))
            current = [word]
    if current:
        lines.append(" ".join(current))
    return "\n".join(lines)


def _color_to_rgba(color):
    if color == "white":
        return (255, 255, 255, 255)
    if color == "black":
        return (0, 0, 0, 255)
    return color


def _make_text_clip(text, font_path, font_size, color="white", stroke_color="black",
                    stroke_width=3, align="center", interline=0):
    """Render text with Pillow/FreeType for clean antialiased output (no ImageMagick)."""
    font = ImageFont.truetype(font_path, font_size)
    lines = text.split("\n")

    metrics = []
    for line in lines:
        bbox = font.getbbox(line, stroke_width=stroke_width)
        metrics.append((bbox[2] - bbox[0], bbox[3] - bbox[1], -bbox[0], -bbox[1]))

    img_w = max(m[0] for m in metrics) + 4
    img_h = sum(m[1] for m in metrics) + interline * (len(lines) - 1) + 4

    img = _PILImage.new("RGBA", (img_w, img_h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    fill   = _color_to_rgba(color)
    stroke = _color_to_rgba(stroke_color)

    y = 2
    for i, line in enumerate(lines):
        lw, lh, x_off, y_off = metrics[i]
        x = (img_w - lw) // 2 + x_off if align == "center" else x_off + 2
        draw.text(
            (x, y + y_off),
            line,
            font=font,
            fill=fill,
            stroke_width=stroke_width,
            stroke_fill=stroke,
        )
        y += lh + interline

    return ImageClip(np.array(img))


def _build_branding(font):
    ig_logo = None
    logo_w, logo_h = 0, 0

    if os.path.exists(_IG_LOGO):
        ig_logo = ImageClip(_IG_LOGO).resize(height=48)
        logo_w, logo_h = ig_logo.size

    ig_handle = _make_text_clip(
        _IG_HANDLE,
        font,
        _FONT_SIZE_HANDLE,
        color="white",
        stroke_color="black",
        stroke_width=0,
    )
    handle_w, handle_h = ig_handle.size
    brand_gap = 10 if ig_logo else 0
    brand_total_w = logo_w + brand_gap + handle_w
    brand_x = (_TARGET_W - brand_total_w) // 2

    return ig_logo, ig_handle, logo_w, logo_h, handle_h, brand_x, brand_gap


def generate_tiktok_videos(quotes, author, output_dir):
    font = _load_font_path()

    videos_dir = os.path.join(_BASE, BACKGROUND_VIDEO_PATH)
    video_files = glob.glob(os.path.join(videos_dir, "*.mp4"))
    if not video_files:
        raise RuntimeError(f"No videos found in {videos_dir}")

    songs_dir = os.path.join(_BASE, "media", "songs")
    song_files = glob.glob(os.path.join(songs_dir, "*.mp3"))
    if not song_files:
        raise RuntimeError(f"No songs found in {songs_dir}")

    selected = random.sample(video_files, min(len(quotes), len(video_files)))
    os.makedirs(output_dir, exist_ok=True)

    ig_logo, ig_handle, logo_w, logo_h, handle_h, brand_x, brand_gap = _build_branding(font)

    output_paths = []

    for i, (video_path, quote) in enumerate(zip(selected, quotes)):
        output_path = os.path.join(output_dir, f"quote_{i + 1}.mp4")
        logging.info(f"Creating TikTok video [{i + 1}/{len(quotes)}]: {os.path.basename(video_path)}")

        # ── Background video ─────────────────────────────────────
        raw = VideoFileClip(video_path).without_audio()
        duration = min(_CLIP_DURATION, raw.duration)
        raw = raw.subclip(0, duration)

        iw, ih = raw.size
        scale = max(_TARGET_W / iw, _TARGET_H / ih) * 1.08
        raw = raw.resize(scale)

        w, h = raw.size
        raw = raw.crop(
            x_center=w // 2, y_center=h // 2,
            width=_TARGET_W, height=_TARGET_H,
        )

        # ── Text layers ───────────────────────────────────────────
        wrapped = _wrap_text(f'"{quote}"', font, _FONT_SIZE_QUOTE, _TEXT_MAX_W)
        txt_quote = _make_text_clip(
            wrapped,
            font,
            _FONT_SIZE_QUOTE,
            color="white",
            stroke_color="black",
            stroke_width=0,
            align="center",
            interline=16,
        )
        txt_author = _make_text_clip(
            f"— {author}",
            font,
            _FONT_SIZE_AUTHOR,
            color="white",
            stroke_color="black",
            stroke_width=0,
            align="center",
        )

        gap = 30
        block_h = txt_quote.size[1] + gap + txt_author.size[1]
        start_y = (_TARGET_H - block_h) // 2
        padding_y = 40

        overlay_top = start_y - padding_y
        brand_mid_y = overlay_top // 2
        logo_y = brand_mid_y - logo_h // 2
        handle_y = brand_mid_y - handle_h // 2

        # ── Overlay + positioned clips ────────────────────────────
        overlay = (
            ColorClip(size=(_TARGET_W, block_h + padding_y * 2), color=(0, 0, 0))
            .set_opacity(0.45)
            .set_duration(duration)
            .set_position(("center", overlay_top))
        )
        txt_quote = (
            txt_quote.set_duration(duration)
            .set_position(("center", start_y))
        )
        txt_author = (
            txt_author.set_duration(duration)
            .set_position(("center", start_y + txt_quote.size[1] + gap))
        )

        layers = [raw, overlay, txt_quote, txt_author]

        if ig_logo:
            layers.append(
                ig_logo.set_duration(duration).set_opacity(0.82).set_position((brand_x, logo_y))
            )
        layers.append(
            ig_handle.set_duration(duration).set_opacity(0.82).set_position(
                (brand_x + logo_w + brand_gap, handle_y)
            )
        )

        # ── Audio ─────────────────────────────────────────────────
        song = random.choice(song_files)
        logging.info(f"Song selected: {os.path.basename(song)}")
        audio = AudioFileClip(song)
        if audio.duration > duration:
            audio = audio.subclip(0, duration)
        audio = (
            audio.volumex(0.49)
            .fx(afx.audio_fadein,  1.0)
            .fx(afx.audio_fadeout, 1.5)
        )

        # ── Render ────────────────────────────────────────────────
        video = CompositeVideoClip(layers, size=(_TARGET_W, _TARGET_H)).set_audio(audio)
        video.write_videofile(
            output_path,
            fps=30,
            codec="libx264",
            audio_codec="aac",
            threads=2,
            verbose=False,
            logger=None,
        )

        logging.info(f"TikTok video saved: {output_path}")
        output_paths.append(output_path)

    return output_paths
