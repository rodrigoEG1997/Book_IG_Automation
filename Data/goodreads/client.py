import requests
import logging
import os
import time
from config.settings import GOODREADS_BASE_URL, TIMEOUT

MAX_RETRIES = 5
RETRY_WAIT = 60

class GoodreadsClient:

    def get(self, endpoint, params=None):

        if params is None:
            params = {}

        url = f"{GOODREADS_BASE_URL}/{endpoint}"

        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            "Accept-Language": "en-US,en;q=0.9",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        }

        logging.info(f"GET {url} - params={params}")

        for attempt in range(1, MAX_RETRIES + 1):
            try:
                response = requests.get(url, headers=headers, params=params, timeout=TIMEOUT)
                response.raise_for_status()
                return response

            except requests.exceptions.HTTPError as e:
                if attempt < MAX_RETRIES:
                    logging.warning(f"HTTP error on attempt {attempt}/{MAX_RETRIES} for {url}. Waiting {RETRY_WAIT}s... ({e})")
                    time.sleep(RETRY_WAIT)
                else:
                    logging.error(f"HTTP error: {e}")
                    raise

            except requests.exceptions.RequestException as e:
                if attempt < MAX_RETRIES:
                    logging.warning(f"Request error on attempt {attempt}/{MAX_RETRIES} for {url}. Waiting {RETRY_WAIT}s... ({e})")
                    time.sleep(RETRY_WAIT)
                else:
                    logging.error(f"Request error: {e}")
                    raise