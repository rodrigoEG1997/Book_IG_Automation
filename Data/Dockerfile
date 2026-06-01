FROM python:3.11.13-slim

RUN apt-get update && apt-get install -y gcc g++ fonts-dejavu-core fonts-liberation ffmpeg imagemagick && rm -rf /var/lib/apt/lists/*
RUN find /etc -name "policy.xml" -path "*/ImageMagick*" -exec sed -i 's/rights="none" pattern="@\*"/rights="read|write" pattern="@*"/g' {} \;

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

CMD ["python", "exec_data_setup.py"]