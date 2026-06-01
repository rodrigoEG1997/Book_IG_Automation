def init_inbox_upload(video_size):
    return {
        "endpoint": "post/publish/inbox/video/init/",
        "body": {
            "source_info": {
                "source": "FILE_UPLOAD",
                "video_size": video_size,
                "chunk_size": video_size,
                "total_chunk_count": 1,
            }
        }
    }

def upload_status(publish_id):
    return {
        "endpoint": "post/publish/status/fetch/",
        "body": {"publish_id": publish_id}
    }
