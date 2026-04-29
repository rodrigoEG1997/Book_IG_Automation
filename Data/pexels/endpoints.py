def search(query, orientation, per_page, page):
    return {
        "endpoint": "search",
        "params": {
                "query": query,
                "orientation": orientation,
                "per_page": per_page,
                "page": page
            }
    }