import logging
import random
import requests
from pexels.client import PexelsClient
from pexels import endpoints, helpers
from config.settings import (
    PEXELS_VIDEOS_BASE_URL,
    PEXELS_TOTAL_VIDEOS,
    PEXELS_VIDEOS_PER_PAGE,
    PEXELS_VIDEO_MIN_DURATION,
    PEXELS_VIDEO_MAX_DURATION,
    PEXELS_VIDEO_QUERIES,
    BACKGROUND_VIDEO_PATH,
)


def get_background_videos(client):
    seen_ids = set()
    count = 1

    queries = PEXELS_VIDEO_QUERIES.copy()
    random.shuffle(queries)

    for query in queries:
        if count > PEXELS_TOTAL_VIDEOS:
            break

        for page in range(1, 4):
            if count > PEXELS_TOTAL_VIDEOS:
                break

            param = endpoints.video_search(
                query,
                orientation="portrait",
                per_page=PEXELS_VIDEOS_PER_PAGE,
                page=page,
                min_duration=PEXELS_VIDEO_MIN_DURATION,
                max_duration=PEXELS_VIDEO_MAX_DURATION,
            )
            response = client.get(
                endpoint=param["endpoint"],
                params=param["params"],
                base_url=PEXELS_VIDEOS_BASE_URL,
            )

            videos = helpers.get_videos(response)
            if not videos:
                logging.warning(f"No videos found for query '{query}' page {page}")
                break

            for video in videos:
                if count > PEXELS_TOTAL_VIDEOS:
                    break

                vid_id = video["id"]
                if vid_id in seen_ids:
                    continue

                duration = video.get("duration", 0)
                if not (PEXELS_VIDEO_MIN_DURATION <= duration <= PEXELS_VIDEO_MAX_DURATION):
                    continue

                file_info = helpers.best_portrait_file(video.get("video_files", []))
                if not file_info:
                    continue

                seen_ids.add(vid_id)
                filename = f"video_{count:03d}_{vid_id}.mp4"
                file_path = BACKGROUND_VIDEO_PATH + filename

                try:
                    resp = requests.get(file_info["link"], stream=True, timeout=60)
                    resp.raise_for_status()
                    with open(file_path, "wb") as f:
                        for chunk in resp.iter_content(chunk_size=16384):
                            f.write(chunk)
                    logging.info(f"VIDEO DOWNLOAD: {file_path}")
                    count += 1
                except Exception as e:
                    logging.error(f"Failed to download video {vid_id}: {e}")


if __name__ == "__main__":

    logging.basicConfig(
        filename="/app/logs/app.log",
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s"
    )

    client = PexelsClient()
    get_background_videos(client)
