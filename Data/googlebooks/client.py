import requests
import logging
import os
from config.settings import GOOGLEBOOKS_BASE_URL, TIMEOUT

class GoogleBooksClient:

    def get(self, endpoint, params=None):

        if params is None:
            params = {}

        url = f"{GOOGLEBOOKS_BASE_URL}/{endpoint}"

        headers = {
            "User-Agent": "IGQuotesAutomation/1.0"
        }

        logging.info(f"GET {url} - params={params}")

        try:
            response = requests.get(url, headers=headers, params=params, timeout=TIMEOUT)
            response.raise_for_status()
            return response.json()

        except requests.exceptions.HTTPError as e:
            logging.error(f"HTTP error: {e}")
            raise
        except requests.exceptions.RequestException as e:
            logging.error(f"Request error: {e}")
            raise