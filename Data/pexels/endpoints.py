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

def video_search(query, orientation, per_page, page, min_duration, max_duration):
    return {
        "endpoint": "search",
        "params": {
            "query": query,
            "orientation": orientation,
            "size": "medium",
            "min_duration": min_duration,
            "max_duration": max_duration,
            "per_page": per_page,
            "page": page,
        }
    }