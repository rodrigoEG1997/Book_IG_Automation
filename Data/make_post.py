from ig_post_creator.create_quote import create_quote_image
from ig_post_creator.helpers import create_img_book, create_author_img
import os
import glob
import time
from config.settings import OUTPUT_POST, BACKGROUND_QUOTE
import logging
from db import queries
from db.connection import get_connection


if __name__ == "__main__":

    logging.basicConfig(
        filename="/app/logs/app.log",
        #filename="../logs/app.log",
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s"
        )
    
    #Delete Old Post
    base = os.path.dirname(os.path.abspath(__file__))
    old_post = os.path.join(base, OUTPUT_POST, "*")

    for file in glob.glob(old_post):
        os.remove(file)

    time.sleep(1)

    connection = get_connection()
    cursor = connection.cursor()

    #Get Data
    id_book = queries.get_random_id_book(cursor)
    book = queries.get_book(cursor, id_book)
    author = queries.get_author(cursor, book['id_Author'])
    num_bg = queries.get_background(cursor)

    #Create Book Image
    path_book = book["img_book"].replace("Data", base, 1)
    book_post = os.path.join(base, OUTPUT_POST, "book.png")
    create_img_book(path_book, book_post)

    #Create Quotes
    background = f"background_{num_bg}.jpg"
    for i in range(1, 6):
        quote = book[f"quote_{i}"]
        output = f"quote_{i}.png"
        if quote:
            create_quote_image(os.path.join(base, BACKGROUND_QUOTE, background), 
                    quote, 
                    author['name'], 
                    os.path.join(base, OUTPUT_POST, output))

    #Create Author Image
    path_book = author["img_author"].replace("Data", base, 1)
    author_post = os.path.join(base, OUTPUT_POST, "author.png")
    create_author_img(path_book, author_post, author["description"])

    num_bg = 1 if num_bg > 430 else num_bg + 1

    queries.update_book_available(connection, cursor, id_book)
    queries.update_background(connection, cursor, num_bg)

    cursor.close()
    connection.close()