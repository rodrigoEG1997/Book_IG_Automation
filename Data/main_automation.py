from ig_post_creator.create_quote import create_quote_image
from ig_post_creator.helpers import create_img_book, create_author_img
from ig_post_creator.make_post import make_post
from ig_connector.post_content import post_book
from ig_post_creator.make_history import post_story
import os
import sys
import glob
import time
from config.settings import IG_APP_ID, IG_SECRET, TEMP_TOKEN
import logging
import mysql.connector
import requests
from db import queries
from db.connection import get_connection
from ig_connector import ig_tokens
from datetime import datetime


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
        content, author, quote = make_post(connection, cursor, base)

        logging.info("Publishing to Instagram...")
        post_id = post_book(content, token)
        logging.info("Post published successfully")
        time.sleep(10)
        logging.info("Publishing story...")
        post_story(post_id, token, base, author, quote)
        logging.info("Story published successfully")

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