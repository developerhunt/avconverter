# 1. Use lightweight Python base image
FROM python:3.9-slim

# 2. Install FFmpeg
RUN apt-get update && \
    apt-get install -y ffmpeg && \
    apt-get clean

# 3. Set working directory
WORKDIR /app

# 4. Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copy the rest of the app code
COPY . .

# 6. Start the server on PORT 10000 (Standard for Render)
# ⚠️ CHANGED FROM 80 TO 10000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "10000"]
