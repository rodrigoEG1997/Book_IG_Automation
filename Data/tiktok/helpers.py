from .endpoints import init_inbox_upload as endpoint_init_upload
from .endpoints import upload_status as endpoint_upload_status
from config.settings import TIKTOK_CLIENT_KEY, TIKTOK_CLIENT_SECRET


def refresh_tokens(client, refresh_token):
    response = client.refresh_token(TIKTOK_CLIENT_KEY, TIKTOK_CLIENT_SECRET, refresh_token)
    return response.get("access_token"), response.get("refresh_token")


def init_upload(client, video_size):
    params = endpoint_init_upload(video_size)
    response = client.post(params["endpoint"], params["body"])
    data = response.get("data", {})
    return data.get("publish_id"), data.get("upload_url")


def upload_video(client, upload_url, video_path, video_size):
    return client.put_file(upload_url, video_path, video_size)


def check_status(client, publish_id):
    params = endpoint_upload_status(publish_id)
    return client.post(params["endpoint"], params["body"])
