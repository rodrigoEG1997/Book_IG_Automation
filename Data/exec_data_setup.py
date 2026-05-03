import subprocess
import sys
import time
import logging

logging.basicConfig(
    filename="/app/logs/app.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

logging.info("Starting data setup")

# run get_backgrounds.py
logging.info("Running get_backgrounds.py...")
try:
    subprocess.run([sys.executable, "get_backgrounds.py"], check=True)
    logging.info("get_backgrounds.py finished successfully")
except subprocess.CalledProcessError as e:
    logging.error(f"get_backgrounds.py failed with exit code {e.returncode}")
    sys.exit(1)

# time sleep (5 seg)
time.sleep(5)

# run get_autors_books.py
logging.info("Running get_autors_books.py...")
try:
    subprocess.run([sys.executable, "get_autors_books.py"], check=True)
    logging.info("get_autors_books.py finished successfully")
except subprocess.CalledProcessError as e:
    logging.error(f"get_autors_books.py failed with exit code {e.returncode}")
    sys.exit(1)

logging.info("Data setup completed")
