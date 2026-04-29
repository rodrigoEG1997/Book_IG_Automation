import re
import time
import json
import requests
from bs4 import BeautifulSoup
import anthropic
import logging

from goodreads.client import GoodreadsClient
from goodreads import endpoints as GoodreadsEndpoint, helpers as GoodreadsHelpers
from config.settings import GOODREADS_BASE_URL, SLEEP_BETWEEN_REQ, MAX_RETRIES, RETRY_DELAY

def search_quotes_url(clientGoodreads, book_title, author):
    paramQuotesURL= GoodreadsEndpoint.search(book_title, author)
    response = clientGoodreads.get(
            endpoint=paramQuotesURL["endpoint"], 
            params = paramQuotesURL["params"]
        )
    
    soup = BeautifulSoup(response.text, "html.parser")

    book_links = soup.select("a.bookTitle")
    author_links = soup.select("a.authorName")

    result_path = GoodreadsHelpers.find_best_match_url(book_links, author_links, author)

    if result_path:

        time.sleep(SLEEP_BETWEEN_REQ)

        try:
            book_resp = clientGoodreads.get(
                    endpoint=result_path[1:]
                )
        except requests.exceptions.RequestException as e:
            logging.error(f"NOT QUOTE URL FOUND: {e}")

        book_soup = BeautifulSoup(book_resp.text, "html.parser")

        quotes_link = book_soup.find("a", href=re.compile(r"/work/quotes/"))
        if quotes_link:
            quotes_url = quotes_link["href"]

    return quotes_url

def scrape_quotes_page(clientGoodreads, quotes_url, limit):

    endpoint = GoodreadsHelpers.remove_base(quotes_url, GOODREADS_BASE_URL)
    try:
        resp = clientGoodreads.get(endpoint=endpoint)
        resp.raise_for_status()
    except requests.RequestException as e:
        logging.error(f"NOT QUOTE PAGE: {e}")
        return []
    
    soup   = BeautifulSoup(resp.text, "html.parser")
    raw_quotes = GoodreadsHelpers.get_top_5_quotes(soup, limit)

    quotes_english = [GoodreadsHelpers.translate_to_english(q) for q in raw_quotes]

    return quotes_english

def get_quotes_with_retry(clientGoodreads, book_title, author):
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            quotes_url = search_quotes_url(clientGoodreads, book_title, author)
            time.sleep(SLEEP_BETWEEN_REQ)
            raw_quotes = scrape_quotes_page(clientGoodreads, quotes_url, 5)
            if not raw_quotes:
                raise ValueError("No quotes returned")
            return raw_quotes
        except (
            requests.exceptions.ReadTimeout,
            requests.exceptions.ConnectionError,
            ValueError,
            Exception
        ) as e:
            if attempt == MAX_RETRIES:
                return []
            time.sleep(RETRY_DELAY)

if __name__ == "__main__":

    logging.basicConfig(
        # filename="/app/logs/app.log",
        filename="../logs/app.log",
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s"
        )
    
    author = "Toni Morrison"
    book_title = "Beloved"

    clientGoodreads = GoodreadsClient()

    raw_quotes = get_quotes_with_retry(clientGoodreads, book_title, author)
        
    for quote in raw_quotes:
        print(quote)