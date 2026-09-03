FROM python:3.11-slim

# ffmpeg va yt-dlp ishlashi uchun kerakli tizim kutubxonalari
RUN apt-get update && apt-get install -y ffmpeg git && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PORT=10000
EXPOSE 10000

CMD ["gunicorn", "-b", "0.0.0.0:10000", "--timeout", "600", "app:app"]
