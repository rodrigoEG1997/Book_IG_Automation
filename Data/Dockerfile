FROM python:3.11.13-slim

RUN apt-get update && apt-get install -y gcc g++ fonts-dejavu-core fonts-liberation && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

# CMD ["python", "get_backgrounds.py"]
CMD ["python", "get_autors_books.py"]