import logging
import requests
import time
from config.settings import AUTHRDS_IMG_PATH, BOOK_IMG_PATH
from config.authors_quotes import TEST_AUTHORS
from db.connection import get_connection
from db import queries
from db.modules.author import Author
from db.modules.book import Book

#Get QUOTES
from get_quotes import *

#APIs
from openlibrary.client import OpenLibraryClient
from openlibrary import endpoints as OpenLibraryEndpoint, helpers as OpenLibraryHelpers
from wikipedia.client import WikipediaClient
from wikipedia import endpoints as WikipediaEndpoint, helpers as WikipediaHelpers
from goodreads.client import GoodreadsClient

def get_books(connection, cursor, clientWikipedia, clientOpenLibrary, clientGoodreads):

    for name in TEST_AUTHORS:
        try:
            author, img_author = get_authors(clientWikipedia, name)
            id_author = OpenLibraryHelpers.search_author(clientOpenLibrary, name)

            if not id_author or not author:
                logging.warning(f"Skipping '{name}': could not find author data.")
                continue

            json_author = Author(author).to_json()
            json_author['id_OpenLibrary'] = id_author
            json_author['img_author'] = img_author
            print("Author: ", json_author['name'])
            queries.insert_author(cursor, json_author)
            connection.commit()

            paramAuthorBooks = OpenLibraryEndpoint.books(id_author, 15)
            response = clientOpenLibrary.get(
                    endpoint=paramAuthorBooks["endpoint"],
                    params = paramAuthorBooks["params"]
                )

            if response is None:
                logging.warning(f"Skipping '{name}': failed to fetch books.")
                continue

            books = OpenLibraryHelpers.top_books(response, 5)
            for book in books:
                try:
                    paramBook_Details = OpenLibraryEndpoint.book_detail(book["work_key"])
                    resp_book_detail = clientOpenLibrary.get(
                            endpoint=paramBook_Details["endpoint"],
                            params = paramBook_Details["params"]
                        )
                    if resp_book_detail is None:
                        logging.warning(f"Skipping book '{book.get('title')}': could not fetch book details.")
                        continue

                    resp_book = OpenLibraryHelpers.merge_book(book, resp_book_detail)
                    filename  = str(resp_book["cover_id"]) + "_" + str(resp_book["title"])
                    img_book_path = clientOpenLibrary.get_img(resp_book["cover_url"], filename, BOOK_IMG_PATH)
                    if img_book_path:
                        img_book_path = img_book_path.replace(".", "Data", 1)
                        raw_quotes = get_quotes_with_retry(clientGoodreads, resp_book["title"], author["name"])

                        if raw_quotes:
                            json_book = Book(resp_book).to_json()
                            json_book["id_Author"] = queries.get_author_id(cursor, 
                                                                           json_author['id_Wikipedia'], 
                                                                           json_author['id_OpenLibrary'], 
                                                                           json_author['name'])
                            
                            json_book["img_book"] = img_book_path

                            for i, quote in enumerate(raw_quotes[:5], start=1):
                                json_book[f"quote_{i}"] = quote

                            print("Book: ", json_book['title'])
                            # print(json_book)
                            queries.insert_book(cursor, json_book)
                            connection.commit()
                            


                    #INERT IN DATABASE

                except Exception as e:
                    logging.error(f"Error processing book '{book.get('title', '?')}' for '{name}': {e}")
                    continue

        except Exception as e:
            logging.error(f"Error processing author '{name}': {e}")
            continue
                

def get_authors(clientWikipedia, name):
    paramAuthorImg= WikipediaEndpoint.imge_bio_link(name)
    response = clientWikipedia.get(
            endpoint=paramAuthorImg["endpoint"], 
            params = paramAuthorImg["params"]
        )
    
    result = {
        "name": response.get("title"),
        "bio": response.get("extract"),
        "photo": (
            response.get("originalimage", {}).get("source")
            or response.get("thumbnail", {}).get("source")
        ),
        "wikipedia_url": response.get("content_urls", {}).get("desktop", {}).get("page"),
        "wikidata_id": response.get("wikibase_item"),
        "description": response.get("description"),
    }

    filename  = str(result["wikidata_id"]) + "_" + str(result["name"])
    if result["photo"]:
        filename = clientWikipedia.get_img(result["photo"], filename, AUTHRDS_IMG_PATH)
        img_path = filename.replace(".", "Data", 1)
        return result, img_path
    else:
        logging.warning(f"No photo found for '{name}' on Wikipedia.")
        return None, None


if __name__ == "__main__":

    logging.basicConfig(
        filename="/app/logs/app.log",
        #filename="../logs/app.log",
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s"
        )

    clientOpenLibrary = OpenLibraryClient()
    clientWikipedia = WikipediaClient()
    clientGoodreads = GoodreadsClient()

    connection = get_connection()
    cursor = connection.cursor()

    get_books(connection, cursor, clientWikipedia, clientOpenLibrary, clientGoodreads)

    cursor.close()
    connection.close()
