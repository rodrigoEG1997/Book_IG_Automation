import requests
import logging
import os
import time
from config.settings import OPENLIBRARY_BASE_URL, TIMEOUT

MAX_RETRIES = 5
RETRY_WAIT = 30
BACKOFF_FACTOR = 2

class OpenLibraryClient:

    def get(self, endpoint, params=None):

        if params is None:
            params = {}

        url = f"{OPENLIBRARY_BASE_URL}/{endpoint}"

        logging.info(f"GET {url} - params={params}")

        for attempt in range(1, MAX_RETRIES + 1):
            try:
                response = requests.get(url, params=params, timeout=TIMEOUT)
                response.raise_for_status()
                return response.json()

            except (requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout) as e:
                if attempt < MAX_RETRIES:
                    logging.warning(f"Timeout on attempt {attempt}/{MAX_RETRIES} for {url}. Retrying in {RETRY_WAIT}s...")
                    time.sleep(RETRY_WAIT)
                else:
                    logging.error(f"Max retries reached for {url}: {e}")
                    return None

            except requests.exceptions.HTTPError as e:
                if response.status_code == 503:
                    logging.warning(f"503 on attempt {attempt}/{MAX_RETRIES} for {url}. Waiting 60s...")
                    time.sleep(60)
                    continue
                logging.error(f"HTTP error: {e}")
                return None

            except requests.exceptions.RequestException as e:
                if attempt < MAX_RETRIES:
                    logging.warning(f"Request error on attempt {attempt}/{MAX_RETRIES} for {url}. Retrying in {RETRY_WAIT}s... ({e})")
                    time.sleep(RETRY_WAIT)
                else:
                    logging.error(f"Max retries reached for {url}: {e}")
                    return None

    def get_img(self, img_link, book_name, book_img_save_path):
        filename = book_name.lower().replace(" ", "_") + ".jpg"
        filepath = os.path.join(book_img_save_path, filename)

        logging.info(f"GET_BOOK_IMG {img_link}")

        for attempt in range(1, MAX_RETRIES + 1):
            try:
                headers = {
                    "User-Agent": "IGQuotesAutomation/1.0"
                }

                response = requests.get(img_link, headers=headers, timeout=20)
                response.raise_for_status()

                with open(filepath, "wb") as f:
                    f.write(response.content)
                return filepath

            except (requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout) as e:
                wait = BACKOFF_FACTOR ** attempt
                if attempt < MAX_RETRIES:
                    logging.warning(f"Image timeout attempt {attempt}/{MAX_RETRIES}. Retrying in {wait}s...")
                    time.sleep(wait)
                else:
                    logging.error(f"Failed to download image after {MAX_RETRIES} attempts: {e}")

            except requests.exceptions.HTTPError as e:
                if response.status_code == 502:
                    if attempt < MAX_RETRIES:
                        logging.warning(f"502 on image attempt {attempt}/{MAX_RETRIES}. Waiting 30s...")
                        time.sleep(30)
                        continue
                    logging.error(f"Failed to download image after {MAX_RETRIES} attempts: {e}")
                    return None
                logging.error(f"Failed to download image: {e}")
                return None

            except requests.exceptions.RequestException as e:
                logging.error(f"Failed to download image: {e}")
                return None