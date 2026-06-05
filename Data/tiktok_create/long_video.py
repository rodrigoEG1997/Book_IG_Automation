import os
import glob
import random
import logging
import numpy as np
from PIL import Image as _PILImage, ImageDraw, ImageFont

if not hasattr(_PILImage, "ANTIALIAS"):
    _PILImage.ANTIALIAS = _PILImage.LANCZOS

from moviepy.editor import (
    VideoFileClip, AudioFileClip, ColorClip, ImageClip,
    CompositeVideoClip, concatenate_videoclips,
)
import moviepy.video.fx.all as vfx
import moviepy.audio.fx.all as afx
from config.settings import BACKGROUND_VIDEO_PATH

_TARGET_W         = 720
_TARGET_H         = 1280
_CLIP_DURATION    = 10
_CROSSFADE        = 0.6
_FONT_SIZE_QUOTE  = 40
_FONT_SIZE_AUTHOR = 28
_FONT_SIZE_HANDLE = 24
_TEXT_MAX_W       = _TARGET_W - 100
_IG_HANDLE        = "@rod.littlebooks"

_BASE    = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_IG_LOGO = os.path.join(_BASE, "media", "ig.png")

_FONT_PATHS = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    "/Library/Fonts/Arial Bold.ttf",
    "/System/Library/Fonts/Helvetica.ttc",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
]


def _load_font_path():
    for path in _FONT_PATHS:
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


def _make_text_clip(text, font_path, font_size, color="white", stroke_color="black",
                    stroke_width=2, align="center", interline=0):
    font  = ImageFont.truetype(font_path, font_size)
    lines = text.split("\n")

    metrics = []
    for line in lines:
        bbox = font.getbbox(line, stroke_width=stroke_width)
        metrics.append((bbox[2] - bbox[0], bbox[3] - bbox[1], -bbox[0], -bbox[1]))

    img_w = max(m[0] for m in metrics) + 4
    img_h = sum(m[1] for m in metrics) + interline * (len(lines) - 1) + 4

    img  = _PILImage.new("RGBA", (img_w, img_h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    def to_rgba(c):
        if c == "white": return (255, 255, 255, 255)
        if c == "black": return (0, 0, 0, 255)
        return c

    y = 2
    for i, line in enumerate(lines):
        lw, lh, x_off, y_off = metrics[i]
        x = (img_w - lw) // 2 + x_off if align == "center" else x_off + 2
        draw.text((x, y + y_off), line, font=font,
                  fill=to_rgba(color), stroke_width=stroke_width, stroke_fill=to_rgba(stroke_color))
        y += lh + interline

    return ImageClip(np.array(img))


def _build_branding(font_path, duration):
    ig_logo = None
    logo_w, logo_h = 0, 0

    if os.path.exists(_IG_LOGO):
        ig_logo = ImageClip(_IG_LOGO).resize(height=48)
        logo_w, logo_h = ig_logo.size

    ig_handle = _make_text_clip(
        _IG_HANDLE, font_path, _FONT_SIZE_HANDLE,
        color="white", stroke_color="black", stroke_width=0,
    )
    handle_w, handle_h = ig_handle.size
    gap         = 10 if ig_logo else 0
    total_w     = logo_w + gap + handle_w
    brand_x     = (_TARGET_W - total_w) // 2
    brand_y     = 60

    positioned = []
    if ig_logo:
        logo_y = brand_y + (handle_h - logo_h) // 2
        positioned.append(
            ig_logo.set_duration(duration).set_opacity(0.82).set_position((brand_x, logo_y))
        )
    positioned.append(
        ig_handle.set_duration(duration).set_opacity(0.82).set_position(
            (brand_x + logo_w + gap, brand_y)
        )
    )
    return positioned


def generate_long_video(autor, quotes, filename, output_dir=None):
    if output_dir is None:
        output_dir = os.path.join(_BASE, "media", "post")

    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, f"{filename}.mp4")

    font_path = _load_font_path()

    videos_dir = os.path.join(_BASE, BACKGROUND_VIDEO_PATH)
    video_files = glob.glob(os.path.join(videos_dir, "*.mp4"))
    if not video_files:
        raise RuntimeError(f"No background videos found in {videos_dir}")

    songs_dir = os.path.join(_BASE, "media", "songs")
    song_files = glob.glob(os.path.join(songs_dir, "*.mp3"))
    if not song_files:
        raise RuntimeError(f"No songs found in {songs_dir}")

    selected_videos = random.sample(video_files, min(len(quotes), len(video_files)))
    song_path = random.choice(song_files)
    logging.info(f"Song: {os.path.basename(song_path)}")

    clips = []

    for i, (video_path, quote) in enumerate(zip(selected_videos, quotes)):
        logging.info(f"Processing clip [{i + 1}/{len(quotes)}]: {os.path.basename(video_path)}")

        raw      = VideoFileClip(video_path).without_audio()
        duration = min(_CLIP_DURATION, raw.duration)
        raw      = raw.subclip(0, duration)

        iw, ih = raw.size
        scale  = max(_TARGET_W / iw, _TARGET_H / ih) * 1.08
        raw    = raw.resize(scale)

        w, h = raw.size
        raw  = raw.crop(x_center=w // 2, y_center=h // 2, width=_TARGET_W, height=_TARGET_H)

        zoom_dir = 1 if i % 2 == 0 else -1
        raw = raw.fx(vfx.resize, lambda t, d=duration, z=zoom_dir: 1 + z * 0.03 * (t / d))

        if i > 0:
            raw = raw.crossfadein(_CROSSFADE)
        if i < len(quotes) - 1:
            raw = raw.crossfadeout(_CROSSFADE)

        wrapped    = _wrap_text(f'"{quote}"', font_path, _FONT_SIZE_QUOTE, _TEXT_MAX_W)
        txt_quote  = _make_text_clip(wrapped, font_path, _FONT_SIZE_QUOTE,
                                     stroke_width=3, interline=16)
        txt_author = _make_text_clip(f"— {autor}", font_path, _FONT_SIZE_AUTHOR,
                                     stroke_width=2)

        gap     = 30
        block_h = txt_quote.size[1] + gap + txt_author.size[1]
        start_y = (_TARGET_H - block_h) // 2
        pad     = 40

        overlay = (
            ColorClip(size=(_TARGET_W, block_h + pad * 2), color=(0, 0, 0))
            .set_opacity(0.40)
            .set_duration(duration)
            .set_position(("center", start_y - pad))
        )
        txt_quote  = txt_quote.set_duration(duration).set_position(("center", start_y))
        txt_author = txt_author.set_duration(duration).set_position(
            ("center", start_y + txt_quote.size[1] + gap)
        )

        composite = CompositeVideoClip(
            [raw, overlay, txt_quote, txt_author],
            size=(_TARGET_W, _TARGET_H),
        )
        clips.append(composite)

    video = concatenate_videoclips(clips, method="compose", padding=-_CROSSFADE)

    audio = AudioFileClip(song_path)
    if audio.duration > video.duration:
        audio = audio.subclip(0, video.duration)
    audio = (
        audio.volumex(0.49)
        .fx(afx.audio_fadein,  2.0)
        .fx(afx.audio_fadeout, 3.0)
    )

    video = video.set_audio(audio)
    video.write_videofile(
        output_path,
        fps=30,
        codec="libx264",
        audio_codec="aac",
        threads=2,
        verbose=False,
        logger=None,
    )

    logging.info(f"Video saved: {output_path}")
    return output_path
