import json
import numpy as np

def insert_author(cursor, author):

    query = "INSERT INTO Authors (id_Wikipedia, id_OpenLibrary, name, bio, photo, wikipedia_url, " \
        "                       description, img_author) " \
        "    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
    cursor.execute(query, 
                (author["id_Wikipedia"], author["id_OpenLibrary"], author["name"], author["bio"], 
                    author["photo"], author["wikipedia_url"], author["description"], author["img_author"]))
    
def insert_book(cursor, book):

    query = "INSERT INTO Books (id_Author, title, id_OpenLibrary, first_publish_year, edition_count, cover_id, " \
        "                       cover_url, ratings_average, ratings_count, want_to_read_count, first_sentence, " \
        "                       description, subjects, links, quote_1, quote_2, quote_3, quote_4, quote_5, available, img_book) " \
        "    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
    cursor.execute(query, 
                (book["id_Author"], book["title"], book["id_OpenLibrary"], book["first_publish_year"], 
                 book["edition_count"], book["cover_id"], book["cover_url"], book["ratings_average"], 
                 book["ratings_count"], book["want_to_read_count"], book["first_sentence"], book["description"], 
                 book["subjects"], book["links"], book["quote_1"], book["quote_2"], 
                 book["quote_3"], book["quote_4"], book["quote_5"], book["available"], 
                 book["img_book"]))
    
def get_author_id(cursor, id_Wikipedia, id_OpenLibrary, name):
    query = "SELECT id FROM Authors WHERE id_Wikipedia = %s AND id_OpenLibrary = %s AND name = %s"
    cursor.execute(query, (id_Wikipedia,id_OpenLibrary, name,))
    result = cursor.fetchone()
    return result[0] if result else None

def get_random_id_book(cursor):
    query = "SELECT id FROM Books WHERE available = TRUE ORDER BY RAND() LIMIT 1;"
    cursor.execute(query)
    result = cursor.fetchone()
    return result[0] if result else None

def get_book(cursor, id_book):
    query = "SELECT * FROM Books WHERE id = %s;"
    cursor.execute(query, (id_book,))
    result = cursor.fetchone()

    if not result:
        return None

    columns = [col[0] for col in cursor.description]
    return dict(zip(columns, result))

def get_author(cursor, id_author):
    query = "SELECT * FROM Authors WHERE id = %s;"
    cursor.execute(query, (id_author,))
    result = cursor.fetchone()

    if not result:
        return None

    columns = [col[0] for col in cursor.description]
    return dict(zip(columns, result))

def get_background(cursor):
    query = "SELECT value FROM Variables WHERE name = 'count_background';"
    cursor.execute(query)
    result = cursor.fetchone()
    return result[0] if result else None

def update_book_available(connection, cursor, id_book):
    query = "UPDATE Books SET available = FALSE WHERE id = %s;"
    cursor.execute(query, (id_book,))
    connection.commit()

def update_background(connection, cursor, num_bg):
    query = "UPDATE Variables SET value = %s WHERE name = 'count_background';"
    cursor.execute(query, (num_bg,))
    connection.commit()

def create_long_token(connection, cursor, long_token):
    query = "INSERT INTO Variables (name, value) " \
    "    VALUES (%s, %s)"
    cursor.execute(query, 
                ("INSTAGRAM_LONG_TOKEN", long_token))
    connection.commit()

def update_long_token(connection, cursor, long_token):
    query = "UPDATE Variables SET value = %s WHERE name = 'INSTAGRAM_LONG_TOKEN';"
    cursor.execute(query, (long_token,))
    connection.commit()

def get_long_token(cursor):
    query = "SELECT value FROM Variables WHERE name = 'INSTAGRAM_LONG_TOKEN';"
    cursor.execute(query)
    result = cursor.fetchone()
    return result[0] if result else None