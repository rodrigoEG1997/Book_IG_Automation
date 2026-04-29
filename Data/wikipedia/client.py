import requests
import logging
import os
import time
from config.settings import WIKI_SUMMARY_URL, TIMEOUT

MAX_RETRIES = 5
RETRY_WAIT = 30

class WikipediaClient:

    def get(self, endpoint, params=None):

        if params is None:
            params = {}

        url = f"{WIKI_SUMMARY_URL}/{endpoint}"

        headers = {
            "User-Agent": "IGQuotesAutomation/1.0"
            }

        logging.info(f"GET {url} - params={params}")

        for attempt in range(1, MAX_RETRIES + 1):
            try:
                response = requests.get(url, headers=headers, params=params, timeout=TIMEOUT)
                response.raise_for_status()
                return response.json()

            except requests.exceptions.HTTPError as e:
                if attempt < MAX_RETRIES:
                    logging.warning(f"HTTP error on attempt {attempt}/{MAX_RETRIES} for {url}. Retrying in {RETRY_WAIT}s... ({e})")
                    time.sleep(RETRY_WAIT)
                else:
                    logging.error(f"HTTP error: {e}")
                    raise

            except requests.exceptions.RequestException as e:
                if attempt < MAX_RETRIES:
                    logging.warning(f"Request error on attempt {attempt}/{MAX_RETRIES} for {url}. Retrying in {RETRY_WAIT}s... ({e})")
                    time.sleep(RETRY_WAIT)
                else:
                    logging.error(f"Request error: {e}")
                    raise

    def get_img(self, img_link, author_name, author_img_save_path):
        filename = author_name.lower().replace(" ", "_") + ".jpg"
        filepath = os.path.join(author_img_save_path, filename)

        logging.info(f"GET_AUTHOR_IMG {img_link}")

        headers = {"User-Agent": "IGQuotesAutomation/1.0"}

        for attempt in range(1, MAX_RETRIES + 1):
            try:
                response = requests.get(img_link, headers=headers, timeout=20)
                response.raise_for_status()

                with open(filepath, "wb") as f:
                    f.write(response.content)

                return filepath

            except requests.exceptions.HTTPError as e:
                if response.status_code == 502:
                    if attempt < MAX_RETRIES:
                        logging.warning(f"502 on author image attempt {attempt}/{MAX_RETRIES}. Waiting 30s...")
                        time.sleep(30)
                        continue
                    logging.error(f"Failed to download author image after {MAX_RETRIES} attempts: {e}")
                    return None
                logging.error(f"HTTP error downloading author image: {e}")
                return None

            except requests.exceptions.RequestException as e:
                logging.error(f"Request error downloading author image: {e}")
                return None