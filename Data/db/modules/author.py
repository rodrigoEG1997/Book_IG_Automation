import json

class Author:
    def __init__(self, data: dict):
        self.name = data.get("name", "")
        self.bio = data.get("bio", "")
        self.photo = data.get("photo", "")
        self.wikipedia_url = data.get("wikipedia_url", "")
        self.wikidata_id = data.get("wikidata_id", "")
        self.description = data.get("description", "")

    def to_json(self):
        return {
            "id_Wikipedia": self.wikidata_id,
            "id_OpenLibrary": "",
            "name": self.name,
            "bio": self.bio,
            "photo": self.photo,
            "wikipedia_url": self.wikipedia_url,
            "description": self.description,
            "img_author": "",
        }