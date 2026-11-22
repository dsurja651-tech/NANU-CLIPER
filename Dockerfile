# NanuCut Clipper: Cloud Docker Image for Hugging Face Spaces & Cloud Hosting
FROM python:3.11-slim

RUN apt-get update \
 && apt-get install -y --no-install-recommends ffmpeg ca-certificates bzip2 fonts-noto-core fonts-noto-cjk \
 && rm -rf /var/lib/apt/lists/*

# yt-dlp needs a JavaScript runtime for YouTube
COPY --from=denoland/deno:bin /deno /usr/local/bin/deno

# Hugging Face Spaces runs as user with uid 1000
RUN useradd -m -u 1000 user
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH \
    PEAKCUT_DATA=/data \
    PEAKCUT_HOST=0.0.0.0 \
    PEAKCUT_PORT=7860 \
    PEAKCUT_TRUST_PROXY=1 \
    PYTHONUNBUFFERED=1

RUN mkdir -p /data && chown -R user:user /data /home/user

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY studio studio
COPY web web

# Automatically fetch YuNet AI face-detection model and stylish caption fonts during build
RUN mkdir -p studio/models studio/fonts \
 && python -c "import urllib.request; urllib.request.urlretrieve('https://raw.githubusercontent.com/opencv/opencv_zoo/main/models/face_detection_yunet/face_detection_yunet_2023mar.onnx', 'studio/models/yunet.onnx')" \
 && python -c "import urllib.request; urllib.request.urlretrieve('https://raw.githubusercontent.com/google/fonts/main/ofl/anton/Anton-Regular.ttf', 'studio/fonts/Anton-Regular.ttf')" \
 && python -c "import urllib.request; urllib.request.urlretrieve('https://raw.githubusercontent.com/google/fonts/main/ofl/poppins/Poppins-ExtraBold.ttf', 'studio/fonts/Poppins-ExtraBold.ttf')" \
 && python -c "import urllib.request; urllib.request.urlretrieve('https://raw.githubusercontent.com/google/fonts/main/ofl/archivoblack/ArchivoBlack-Regular.ttf', 'studio/fonts/ArchivoBlack-Regular.ttf')"

RUN chown -R user:user /app
USER user

VOLUME /data
EXPOSE 7860
HEALTHCHECK --interval=30s --timeout=5s --start-period=120s CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:7860/healthz', timeout=4)"
CMD ["python", "-m", "studio.server"]
