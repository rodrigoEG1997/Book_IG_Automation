import os
import sys
import glob
import logging
import mysql.connector
from db import queries
from db.connection import get_connection
from tiktok.client import TikTokClient
from tiktok import helpers as tiktok_helpers

_BASE       = os.path.dirname(os.path.abspath(__file__))
_TIKTOK_DIR = os.path.join(_BASE, "media", "post", "tiktok")

if __name__ == "__main__":

    logging.basicConfig(
        filename="/app/logs/app.log",
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s"
    )

    logging.info("Starting TikTok upload")

    video_files = sorted(glob.glob(os.path.join(_TIKTOK_DIR, "*.mp4")))
    if not video_files:
        logging.error(f"No videos found in {_TIKTOK_DIR}")
        sys.exit(1)

    logging.info(f"Found {len(video_files)} video(s) to upload")

    connection = None
    try:
        connection = get_connection()
        cursor = connection.cursor()
        logging.info("Database connection established")
    except mysql.connector.Error as e:
        logging.error(f"Could not connect to the database: {e}")
        sys.exit(1)

    try:
        refresh_token = queries.get_tiktok_refresh_token(cursor)
        if not refresh_token:
            raise ValueError("No TikTok refresh token found in Variables table")

        logging.info("Refreshing TikTok tokens...")
        temp_client = TikTokClient(access_token=None)
        access_token, new_refresh_token = tiktok_helpers.refresh_tokens(temp_client, refresh_token)
        if not access_token:
            raise ValueError("Failed to refresh TikTok tokens")

        queries.update_tiktok_tokens(connection, cursor, access_token, new_refresh_token)
        logging.info(f"Tokens refreshed and saved. Access token: {access_token[:20]}...")

        client = TikTokClient(access_token)

        for video_path in video_files:
            logging.info(f"Uploading: {os.path.basename(video_path)}")
            video_size = os.path.getsize(video_path)

            publish_id, upload_url = tiktok_helpers.init_upload(client, video_size)
            if not upload_url:
                logging.error(f"Failed to get upload URL for {os.path.basename(video_path)}, skipping")
                continue

            logging.info(f"publish_id: {publish_id}")
            success = tiktok_helpers.upload_video(client, upload_url, video_path, video_size)

            if not success:
                logging.error(f"Upload failed for {os.path.basename(video_path)}, skipping")
                continue

            status = tiktok_helpers.check_status(client, publish_id)
            logging.info(f"{os.path.basename(video_path)} → Status: {status}")

    except ValueError as e:
        logging.error(f"Error: {e}")
        sys.exit(1)
    except mysql.connector.Error as e:
        logging.error(f"Database error: {e}")
        sys.exit(1)
    except Exception as e:
        logging.exception(f"Unexpected error: {e}")
        sys.exit(1)
    finally:
        if connection:
            cursor.close()
            connection.close()
            logging.info("Connection closed")
