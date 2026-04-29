import os
from dotenv import load_dotenv
load_dotenv()

TIMEOUT = 60

#PEXELS VARIABLES
PEXELS_API_KEY = os.environ.get("PEXELS_API_KEY")
PEXELS_BASE_URL = "https://api.pexels.com/v1"
PEXELS_TOTAL_IMAGES = 500
PEXELS_IMAGES_PER_PAGE = 50
PEXELS_IMAGES_QUERY = "background cartoon book coffee reading aesthetic soft colors"
PEXELS_ORIENTATION = "portrait"
BACKGROUND_IMG_PATH = "media/backgrounds/"

#OPENLIBRARY VARIABLES
OPENLIBRARY_BASE_URL = "https://openlibrary.org"
BOOK_IMG_PATH = "./media/cover_books/"


#WIKIPEDIA
WIKI_SUMMARY_URL = "https://en.wikipedia.org/api/rest_v1"
WIKIDATA_ENTITY_URL = "https://www.wikidata.org/wiki"
AUTHRDS_IMG_PATH = "./media/autor_img/"

#GoogleBooks
GOOGLEBOOKS_BASE_URL = "https://www.googleapis.com/books/v1"

#GOODREADS
GOODREADS_BASE_URL = "https://www.goodreads.com/"
MAX_QUOTE_CHARS   = 200 
MIN_QUOTE_CHARS   = 15 
SLEEP_BETWEEN_REQ = 2.5 
MAX_RETRIES = 7
RETRY_DELAY = 3

#DATABASE CONNECTION
DB_HOST = os.environ.get("DB_HOST")
DB_PORT = os.environ.get("DB_PORT")
DB_USER = os.environ.get("MYSQL_USER")
DB_PASWORD = os.environ.get("MYSQL_PASSWORD")
DB_NAME = os.environ.get("MYSQL_DATABASE")

#CREATE QUOTE
OUTPUT_POST = "media/post/"
BACKGROUND_QUOTE = "media/backgrounds/"
TEXT_COLOR   = (25, 18, 10)
AUTHOR_COLOR = (65, 50, 35)
OVERLAY_COLOR   = (255, 251, 243)
OVERLAY_OPACITY = 185 
SATURATION = 0.65
CROP_ANCHOR = 0.35
ZOOM = 1.5
OUTPUT_W = 1080
OUTPUT_H = 1350
MARGIN_LEFT  = 0.08
TEXT_AREA_W  = 0.84  
BAND_CENTER  = 0.50   
BAND_HEIGHT  = 0.48  
BAND_FADE    = 0.10  
SCALE = 3
PALATINO = "/System/Library/Fonts/Palatino.ttc"
FONT_FALLBACKS = [
    # macOS
    "/Library/Fonts/Georgia.ttf",
    "/System/Library/Fonts/Times.ttc",
    # Linux (DejaVu / Liberation — installed in Dockerfile)
    "/usr/share/fonts/truetype/dejavu/DejaVuSerif-BoldItalic.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSerif-BoldItalic.ttf",
]

SANS_FALLBACKS = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    "/Library/Fonts/Arial.ttf",
    "/System/Library/Fonts/Helvetica.ttc",
]

#BOOK IMG
CANVAS_W = 1080
CANVAS_H = 1350
PADDING  = 80