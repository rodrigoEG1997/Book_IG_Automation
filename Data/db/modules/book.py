import json

class Book:
    def __init__(self, data: dict):
        self.title = data.get("title", "")
        self.work_key = data.get("work_key", "")
        self.first_publish_year = data.get("first_publish_year", "")
        self.edition_count = data.get("edition_count", "")
        self.cover_id = data.get("cover_id", "")
        self.cover_url = data.get("cover_url", "")
        self.ratings_average = data.get("ratings_average", "")
        self.ratings_count = data.get("ratings_count", "")
        self.want_to_read_count = data.get("want_to_read_count", "")
        self.first_sentence = self._normalize(data.get("first_sentence", ""))
        self.description = self._normalize(data.get("description", ""))
        self.subjects = self._normalize(data.get("subjects", ""))
        self.links = self._normalize(data.get("links", ""))

    @staticmethod
    def _normalize(value):
        if isinstance(value, list):
            return json.dumps(value)
        return value

    def to_json(self):
        return {
            "id_Author": "",
            "title": self.title,
            "id_OpenLibrary": self.work_key,
            "first_publish_year": self.first_publish_year,
            "edition_count": self.edition_count,
            "cover_id": self.cover_id,
            "cover_url": self.cover_url,
            "ratings_average": self.ratings_average,
            "ratings_count": self.ratings_count,
            "want_to_read_count": self.want_to_read_count,
            "first_sentence": self.first_sentence,
            "description": self.description,
            "subjects": self.subjects,
            "links": self.links,
            "quote_1": "",
            "quote_2": "",
            "quote_3": "",
            "quote_4": "",
            "quote_5": "",
            "available": True,
            "img_book": ""
        }

