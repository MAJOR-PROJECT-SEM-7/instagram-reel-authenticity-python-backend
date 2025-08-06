# Use slim Python base image
FROM python:3.10-slim

# Install OS-level dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    git \
    curl \
    && apt-get clean

# Set working directory
WORKDIR /app

# Copy requirements and install Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Whisper and preload model
RUN pip install git+https://github.com/openai/whisper.git \
 && python3 -c "import whisper; whisper.load_model('base')"

# Copy the rest of the app
COPY . .

# Expose FastAPI port
EXPOSE 8000

# Run app
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
