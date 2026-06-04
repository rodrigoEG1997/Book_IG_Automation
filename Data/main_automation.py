from ig_post_creator.make_post import make_post
from ig_connector.post_content import post_book
from ig_post_creator.make_history import post_story, post_video_story, pick_random_song
import os
import sys
import time
from config.settings import IG_APP_ID, IG_SECRET, TEMP_TOKEN
import logging
import mysql.connector
import requests
from db import queries
from db.connection import get_connection
from ig_connector import ig_tokens
from datetime import datetime
from tiktok_create.long_video import generate_long_video
from tiktok_create.quote_videos import generate_tiktok_videos
from tiktok.client import TikTokClient
from tiktok import helpers as tiktok_helpers
_BASE = os.path.dirname(os.path.abspath(__file__))


def _cleanup(*paths):
    for path in paths:
        try:
            if os.path.isfile(path):
                os.remove(path)
        except Exception:
            pass

if __name__ == "__main__":

    logging.basicConfig(
        filename="/app/logs/app.log",
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s"
    )

    logging.info("Starting automation")

    connection = None
    try:
        connection = get_connection()
        cursor = connection.cursor()
        logging.info("Database connection established")
    except mysql.connector.Error as e:
        logging.error(f"Could not connect to the database: {e}")
        if connection:
            connection.close()
        sys.exit(1)

    try:
        token = queries.get_long_token(cursor)

        if not token:
            logging.info("No token found, fetching long-lived token...")
            token_response = ig_tokens.get_long_token(IG_APP_ID, IG_SECRET, TEMP_TOKEN)
            if "access_token" not in token_response:
                raise KeyError(f"Unexpected response when fetching token: {token_response}")
            token = token_response["access_token"]
            queries.create_long_token(connection, cursor, token)
            logging.info("Long-lived token created and saved")
        elif datetime.now().day == 1:
            logging.info("First day of the month, refreshing token...")
            new_token_response = ig_tokens.refresh_token(IG_APP_ID, IG_SECRET, token)
            if "access_token" not in new_token_response:
                raise KeyError(f"Unexpected response when refreshing token: {new_token_response}")
            token = new_token_response["access_token"]
            queries.update_long_token(connection, cursor, token)
            logging.info("Token refreshed and updated")

        base = os.path.dirname(os.path.abspath(__file__))
        logging.info("Building post content...")

        song = pick_random_song(base)
        content, author, quote, quotes = make_post(connection, cursor, base, song)

        logging.info("Publishing to Instagram...")
        post_id = post_book(content, token)
        logging.info("Post published successfully")
        _cleanup(*[os.path.join(base, "media", "post", f) for f in os.listdir(os.path.join(base, "media", "post")) if os.path.isfile(os.path.join(base, "media", "post", f))])

        time.sleep(10)
        logging.info("Publishing story...")
        post_story(post_id, token, base, author, quote, song)
        logging.info("Story published successfully")
        _cleanup(
            os.path.join(base, "media", "post", "story.png"),
            os.path.join(base, "media", "post", "story.mp4"),
        )

        #New Implementations...
        time.sleep(2)
        filename = "history_video"
        long_video_path = os.path.join(_BASE, "media", "post", f"{filename}.mp4")
        generate_long_video(author, quotes, filename)
        logging.info("Posting video story to Instagram...")
        post_video_story(f"{filename}.mp4", token)
        logging.info("Video story published successfully")
        _cleanup(long_video_path)

        #Generate videos of tiktok
        time.sleep(2)
        output_dir = os.path.join(_BASE, "media", "post", "tiktok")
        output_paths = generate_tiktok_videos(quotes, author, output_dir)

        #Upload videos to TikTok
        time.sleep(2)
        logging.info("Uploading TikTok videos...")
        refresh_token = queries.get_tiktok_refresh_token(cursor)
        if not refresh_token:
            raise ValueError("No TikTok refresh token found in Variables table")

        temp_client = TikTokClient(access_token=None)
        tiktok_token, new_refresh_token = tiktok_helpers.refresh_tokens(temp_client, refresh_token)
        if not tiktok_token:
            raise ValueError("Failed to refresh TikTok tokens")

        queries.update_tiktok_tokens(connection, cursor, tiktok_token, new_refresh_token)
        logging.info(f"TikTok tokens refreshed. Access token: {tiktok_token[:20]}...")

        tiktok_client = TikTokClient(tiktok_token)
        for video_path in output_paths:
            logging.info(f"Uploading to TikTok: {os.path.basename(video_path)}")
            video_size = os.path.getsize(video_path)
            publish_id, upload_url = tiktok_helpers.init_upload(tiktok_client, video_size)
            if not upload_url:
                logging.error(f"Failed to get upload URL for {os.path.basename(video_path)}, skipping")
                _cleanup(video_path)
                continue
            success = tiktok_helpers.upload_video(tiktok_client, upload_url, video_path, video_size)
            if not success:
                logging.error(f"Upload failed for {os.path.basename(video_path)}, skipping")
                _cleanup(video_path)
                continue
            status = tiktok_helpers.check_status(tiktok_client, publish_id)
            logging.info(f"{os.path.basename(video_path)} → {status}")
            _cleanup(video_path)
        


    except requests.exceptions.RequestException as e:
        logging.error(f"Network error when communicating with the API: {e}")
        sys.exit(1)
    except mysql.connector.Error as e:
        logging.error(f"Database error: {e}")
        sys.exit(1)
    except KeyError as e:
        logging.error(f"Unexpected key in API response: {e}")
        sys.exit(1)
    except Exception as e:
        logging.exception(f"Unexpected error: {e}")
        sys.exit(1)
    finally:
        cursor.close()
        connection.close()
        logging.info("Connection closed")