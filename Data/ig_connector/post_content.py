import os
import time
import requests
from dotenv import load_dotenv
load_dotenv()
from config.settings import POST_BASE_URL, POST_MEDIA_FOLDER, API_VERSION, IG_USER_ID

_PUBLISH_WAIT_SECONDS  = 10
_PUBLISH_MAX_RETRIES   = 10
_PUBLISH_RETRY_WAIT    = 30
_PUBLISH_MAX_PUB_TRIES = 5
_ITEM_MAX_RETRIES      = 3
_ITEM_RETRY_WAIT       = 20


def _wait_until_ready(media_id, access_token):
    """Poll IG until the container status is FINISHED before publishing."""
    for attempt in range(1, _PUBLISH_MAX_RETRIES + 1):
        res = requests.get(
            f"https://graph.facebook.com/{API_VERSION}/{media_id}",
            params={"fields": "status_code", "access_token": access_token},
        ).json()
        status = res.get("status_code", "UNKNOWN")
        print(f"  Media status (attempt {attempt}/{_PUBLISH_MAX_RETRIES}): {status}")
        if status == "FINISHED":
            return
        if status == "ERROR":
            raise RuntimeError(f"Instagram rejected the media container: {res}")
        time.sleep(_PUBLISH_WAIT_SECONDS)
    raise RuntimeError(f"Media container not ready after {_PUBLISH_MAX_RETRIES} attempts.")


def post_book(caption, LONG_TOKEN):
    all_files = os.listdir(POST_MEDIA_FOLDER)
    quotes = sorted([f for f in all_files if f not in ("book.png", "author.png") and f.endswith(".png")])
    ordered_images = ["book.png"] + quotes + ["author.png"]

    print("Image order:", ordered_images)

    # Step 1: Create a carousel item container for each image
    item_ids = []
    for filename in ordered_images:
        url = POST_BASE_URL + filename + f"?t={int(time.time())}"
        payload = {
            "image_url": url,
            "is_carousel_item": "true",
            "access_token": LONG_TOKEN,
        }
        for item_attempt in range(1, _ITEM_MAX_RETRIES + 1):
            res = requests.post(
                f"https://graph.facebook.com/{API_VERSION}/{IG_USER_ID}/media",
                data=payload,
            ).json()
            print(f"  Item container [{filename}] attempt {item_attempt}:", res)
            if "id" in res:
                break
            if item_attempt < _ITEM_MAX_RETRIES:
                print(f"  Retrying in {_ITEM_RETRY_WAIT}s...")
                time.sleep(_ITEM_RETRY_WAIT)
        else:
            raise RuntimeError(f"Failed to create item container for {filename} after {_ITEM_MAX_RETRIES} attempts: {res}")
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

    # Step 3: Wait until IG has processed the container, then publish (with retries)
    carousel_id = carousel["id"]
    publish_payload = {
        "creation_id": carousel_id,
        "access_token": LONG_TOKEN,
    }

    for pub_attempt in range(1, _PUBLISH_MAX_PUB_TRIES + 1):
        _wait_until_ready(carousel_id, LONG_TOKEN)

        published = requests.post(
            f"https://graph.facebook.com/{API_VERSION}/{IG_USER_ID}/media_publish",
            data=publish_payload,
        ).json()

        if "error" not in published:
            print("Published:", published)
            return published["id"]

        print(f"  Publish attempt {pub_attempt}/{_PUBLISH_MAX_PUB_TRIES} failed: {published['error']['message']}")
        if pub_attempt < _PUBLISH_MAX_PUB_TRIES:
            print(f"  Retrying in {_PUBLISH_RETRY_WAIT}s with the same carousel...")
            time.sleep(_PUBLISH_RETRY_WAIT)

    raise RuntimeError(f"Failed to publish after {_PUBLISH_MAX_PUB_TRIES} attempts. Last response: {published}")
