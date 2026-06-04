import logging
from tiktok_create.long_video import generate_long_video

logging.basicConfig(
    filename="/app/logs/app.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

autor    = "Philip Roth"
filename = "history_video"
quotes   = [
    "The pleasure isn't in owning the person. The pleasure is this. Having another contender in the room with you.",
    "Because that is when you love somebody - when you see them being game in the face of the worst. Not courageous. Not heroic. Just game.",
    "Nothing lasts and yet nothing passes either, and nothing passes just because nothing lasts.",
    "The danger with hatred is, once you start in on it, you get a hundred times more than you bargained for. Once you start, you can't stop.",
    "Who are they now? They are the simplest version possible of themselves... They are out from under everything ever piled on top of them.",
]

if __name__ == "__main__":
    output_path = generate_long_video(autor, quotes, filename)
    print(f"Video created: {output_path}")
