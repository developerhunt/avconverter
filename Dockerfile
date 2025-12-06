# 1. Use lightweight Python base image
FROM python:3.9-slim

# 2. Install FFmpeg (The Core Engine)
# -y means "yes" to prompts, update ensures we get the latest pkg list
RUN apt-get update && \
    apt-get install -y ffmpeg && \
    apt-get clean

# 3. Set working directory
WORKDIR /app

# 4. Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copy the rest of the app code
COPY . .

# 6. Start the server (Host 0.0.0.0 is required for Docker)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80"]
