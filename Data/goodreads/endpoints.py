def search(book_title, author):
    query  = f"{book_title} {author}".strip()
    return {
        "endpoint": f"search",
        "params": {
            "q": query, 
            "search_type": "books"}
    }