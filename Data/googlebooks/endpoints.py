def english_title(title):

    return {
        "endpoint": f"volumes",
        "params": {
            "q": f'intitle:{title}',
            "printType": "books",
            "langRestrict": "en",
            "maxResults": 5
        }
    }