import os
import requests
from dotenv import load_dotenv
load_dotenv()
from config.settings import POST_BASE_URL, POST_MEDIA_FOLDER, API_VERSION, IG_USER_ID


def post_book(caption, LONG_TOKEN):
    all_files = os.listdir(POST_MEDIA_FOLDER)
    quotes = sorted([f for f in all_files if f not in ("book.png", "author.png") and f.endswith(".png")])
    ordered_images = ["book.png"] + quotes + ["author.png"]

    print("Image order:", ordered_images)

    # Step 1: Create a carousel item container for each image
    item_ids = []
    for filename in ordered_images:
        url = POST_BASE_URL + filename
        payload = {
            "image_url": url,
            "is_carousel_item": "true",
            "access_token": LONG_TOKEN,
        }
        res = requests.post(
            f"https://graph.facebook.com/{API_VERSION}/{IG_USER_ID}/media",
            data=payload,
        ).json()
        print(f"  Item container [{filename}]:", res)
        item_ids.append(res["id"])

    # Step 2: Create the carousel container
    carousel_payload = {
        "media_type": "CAROUSEL",
        "children": ",".join(item_ids),
        "caption": caption,
        "access_token": LONG_TOKEN,
    }
    carousel = requests.post(
        f"https://graph.facebook.com/{API_VERSION}/{IG_USER_ID}/media",
        data=carousel_payload,
    ).json()
    print("Carousel container:", carousel)

    # Step 3: Publish
    publish_payload = {
        "creation_id": carousel["id"],
        "access_token": LONG_TOKEN,
    }
    published = requests.post(
        f"https://graph.facebook.com/{API_VERSION}/{IG_USER_ID}/media_publish",
        data=publish_payload,
    ).json()
    print("Published:", published)
