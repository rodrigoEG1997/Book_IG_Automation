def get_photos(response_json):
    return response_json.get("photos", [])

def get_videos(response_json):
    return response_json.get("videos", [])

def best_portrait_file(video_files):
    portrait = [f for f in video_files if f.get("height", 0) > f.get("width", 0)]
    candidates = portrait if portrait else video_files
    candidates.sort(key=lambda f: f.get("width", 0) * f.get("height", 0), reverse=True)
    return candidates[0] if candidates else None