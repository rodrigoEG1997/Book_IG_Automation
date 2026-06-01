import requests
import logging
from config.settings import TIKTOK_BASE_URL, TIKTOK_TOKEN_URL, TIMEOUT


class TikTokClient:

    def __init__(self, access_token):
        self.access_token = access_token
        self.base_url = TIKTOK_BASE_URL

    def _auth_headers(self):
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json; charset=UTF-8",
        }

    def post(self, endpoint, body):
        url = f"{self.base_url}/{endpoint}"
        logging.info(f"POST {url}")
        response = requests.post(url, json=body, headers=self._auth_headers(), timeout=TIMEOUT)
        response.raise_for_status()
        return response.json()

    def refresh_token(self, client_key, client_secret, refresh_token):
        logging.info(f"POST {TIKTOK_TOKEN_URL} (refresh)")
        response = requests.post(TIKTOK_TOKEN_URL, data={
            "client_key": client_key,
            "client_secret": client_secret,
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
        }, timeout=TIMEOUT)
        response.raise_for_status()
        return response.json()

    def put_file(self, upload_url, video_path, video_size):
        headers = {
            "Content-Type": "video/mp4",
            "Content-Range": f"bytes 0-{video_size - 1}/{video_size}",
            "Content-Length": str(video_size),
        }
        logging.info(f"PUT {upload_url} ({video_size} bytes)")
        with open(video_path, "rb") as f:
            response = requests.put(upload_url, data=f, headers=headers, timeout=300)
        return response.status_code == 201
