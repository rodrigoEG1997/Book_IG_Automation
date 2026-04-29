def get_title(response):
    items = response.get("items", [])

    if not items:
        return None

    # Get first result in english
    for item in items:
        volume_info = item.get("volumeInfo", {})
        title = volume_info.get("title")
        language = volume_info.get("language")

        if title and language == "en":
            return title

    return None