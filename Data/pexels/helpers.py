def get_photos(response_json):
    photos = response_json.get("photos", [])
    return photos