import logging
import requests
import time
from pexels.client import PexelsClient
from pexels import endpoints, helpers
from config.settings import PEXELS_TOTAL_IMAGES, PEXELS_IMAGES_PER_PAGE, PEXELS_IMAGES_QUERY, PEXELS_ORIENTATION, BACKGROUND_IMG_PATH

def get_backgroundImg(client):

    pages = (PEXELS_TOTAL_IMAGES // PEXELS_IMAGES_PER_PAGE) + 1
    count = 1

    for page in range(1, pages + 1):

        paramImgBackground = endpoints.search(PEXELS_IMAGES_QUERY, PEXELS_ORIENTATION, PEXELS_IMAGES_PER_PAGE, page)
        response = client.get(
                endpoint=paramImgBackground["endpoint"], 
                params = paramImgBackground["params"]
            )
        
        photos = helpers.get_photos(response)

        if not photos:
            logging.error(f"NOT AVAILABE IMAGES")
            break

        for photo in photos:
            if count > PEXELS_TOTAL_IMAGES:
                break

            image_url = photo["src"]["large"]
            img_data = requests.get(image_url).content
            name_img = f"background_{count}.jpg"

            file_path = BACKGROUND_IMG_PATH + name_img
            with open(file_path, "wb") as f:
                f.write(img_data)

            logging.info(f"IMG DOWNLOAD: {file_path}")
            count += 1

        if count > PEXELS_TOTAL_IMAGES:
            break
    

if __name__ == "__main__":

    logging.basicConfig(
        # filename="/app/logs/app.log",
        filename="../logs/app.log",
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s"
        )

    client = PexelsClient()
    get_backgroundImg(client)