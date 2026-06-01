import os
import logging
from tiktok_create.quote_videos import generate_tiktok_videos

logging.basicConfig(
    filename="/app/logs/app.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

_BASE = os.path.dirname(os.path.abspath(__file__))

author = "Philip Roth"

quotes = [
    "The pleasure isn't in owning the person. The pleasure is this. Having another contender in the room with you.",
    "Because that is when you love somebody - when you see them being game in the face of the worst. Not courageous. Not heroic. Just game.",
    "Nothing lasts and yet nothing passes either, and nothing passes just because nothing lasts.",
    "The danger with hatred is, once you start in on it, you get a hundred times more than you bargained for. Once you start, you can't stop.",
    "Who are they now? They are the simplest version possible of themselves... They are out from under everything ever piled on top of them.",
]

if __name__ == "__main__":
    output_dir = os.path.join(_BASE, "media", "post", "tiktok")
    output_paths = generate_tiktok_videos(quotes, author, output_dir)
    print(f"\nDone: {len(output_paths)} videos generated")
    for path in output_paths:
        print(f"  {path}")
