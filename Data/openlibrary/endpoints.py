def search_author(name):
    return {
        "endpoint": "search/authors.json",
        "params": {
                "q": name
            }
    }

def author_details(AUTHOR_KEY):
    return {
        "endpoint": f"authors/{AUTHOR_KEY}.json",
        "params": {}
    }

def books(AUTHOR_KEY, num):
    return {
        "endpoint": f"search.json",
        "params": {
            "author_key": AUTHOR_KEY,
            "language": "eng",
            "limit": num,  
            "fields": (
                "key,"
                "title,"
                "first_publish_year,"
                "edition_count,"
                "cover_i",
                "ratings_average",   
                "ratings_count",       
                "want_to_read_count",   
                "first_sentence"
            )
        }
    }

def book_detail(BOOK_KEY):
    return {
        "endpoint": f"{BOOK_KEY[1:]}.json",
        "params": {}
    }