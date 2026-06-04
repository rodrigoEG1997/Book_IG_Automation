import glob
import random
from PIL import ImageFont
from moviepy import (
    VideoFileClip, AudioFileClip, TextClip, ColorClip,
    CompositeVideoClip, concatenate_videoclips,
)
from moviepy.video.fx import FadeIn, FadeOut, Resize, Crop
from moviepy.audio.fx import AudioFadeIn, AudioFadeOut

TARGET_W, TARGET_H = 1080, 1920
CLIP_DURATION = 10
CROSSFADE = 0.6
FONT = "/System/Library/Fonts/Helvetica.ttc"
FONT_SIZE_QUOTE = 60
FONT_SIZE_AUTHOR = 40
TEXT_MAX_W = TARGET_W - 140  # 940px usable width

author = "Paulo Coelho"

quotes = [
    "Anyone who loves in the expectation of being loved in return is wasting their time.",
    "Whenever you want to achieve something, keep your eyes open, concentrate and make sure you know exactly what it is you want. No one can hit their target with their eyes closed.",
    "People want to change everything and, at the same time, want it all to remain the same.",
    "Because you believed I was capable of behaving decently, I did.",
    "So you see, Good and Evil have the same face; it all depends on when they cross the path of each individual human being."
]

video_files = glob.glob("videos/*.mp4")
selected_videos = random.sample(video_files, len(quotes))

song_path = random.choice(glob.glob("music/*.mp3"))
print(f"Cancion: {song_path}")


def wrap_text(text, font_path, font_size, max_px_width):
    """Wraps text at word boundaries using real pixel measurements."""
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


def make_zoom(zoom_in, duration):
    if zoom_in:
        return lambda t: 1 + 0.03 * (t / duration)
    else:
        return lambda t: 1.06 - 0.03 * (t / duration)



clips = []
for i, (video_path, quote) in enumerate(zip(selected_videos, quotes)):
    print(f"[{i+1}/{len(quotes)}] {video_path}")

    raw = VideoFileClip(video_path).without_audio()
    duration = min(CLIP_DURATION, raw.duration)
    raw = raw.subclipped(0, duration)

    iw, ih = raw.size
    base_scale = max(TARGET_W / iw, TARGET_H / ih) * 1.08
    raw = raw.resized(base_scale)

    w, h = raw.size
    fx = [
        Resize(make_zoom(i % 2 == 0, duration)),
        Crop(x_center=w // 2, y_center=h // 2, width=TARGET_W, height=TARGET_H),
    ]
    if i > 0:
        fx.append(FadeIn(CROSSFADE))
    if i < len(quotes) - 1:
        fx.append(FadeOut(CROSSFADE))
    raw = raw.with_effects(fx)

    # Word-aware wrapping using pixel measurements
    wrapped = wrap_text(f'“{quote}”', FONT, FONT_SIZE_QUOTE, TEXT_MAX_W)
    txt_quote = TextClip(
        text=wrapped,
        font=FONT,
        font_size=FONT_SIZE_QUOTE,
        color="white",
        stroke_color="black",
        stroke_width=3,
        method="label",
        text_align="center",
        interline=16,
    )

    txt_author = TextClip(
        text=f"— {author}",
        font=FONT,
        font_size=FONT_SIZE_AUTHOR,
        color="white",
        stroke_color="black",
        stroke_width=2,
        method="label",
        text_align="center",
    )

    gap = 30
    block_h = txt_quote.size[1] + gap + txt_author.size[1]
    start_y = (TARGET_H - block_h) // 2
    padding_y = 40

    overlay = (
        ColorClip(size=(TARGET_W, block_h + padding_y * 2), color=(0, 0, 0))
        .with_opacity(0.40)
        .with_duration(duration)
        .with_position(("center", start_y - padding_y))
    )

    txt_quote = txt_quote.with_duration(duration).with_position(("center", start_y))
    txt_author = txt_author.with_duration(duration).with_position(
        ("center", start_y + txt_quote.size[1] + gap)
    )

    composite = CompositeVideoClip(
        [raw, overlay, txt_quote, txt_author],
        size=(TARGET_W, TARGET_H),
    )
    clips.append(composite)

video = concatenate_videoclips(clips, method="compose", padding=-CROSSFADE)
total = video.duration

audio = AudioFileClip(song_path)
if audio.duration > total:
    audio = audio.subclipped(0, total)
audio = audio.with_volume_scaled(0.49).with_effects([
    AudioFadeIn(2.0),
    AudioFadeOut(3.0),
])

video = video.with_audio(audio)
video.write_videofile(
    "cormac_mccarthy_tiktok.mp4",
    fps=30,
    codec="libx264",
    audio_codec="aac",
    threads=4,
)
