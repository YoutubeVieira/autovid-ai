# Image complète : serveur Node + FFmpeg + outils Python gratuits (téléchargement, transcription, voix Kokoro).
# Le clonage Chatterbox demande une carte graphique : installez-le à part (voir README) ou utilisez fal.ai.
FROM node:22-bookworm-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
      ffmpeg python3 python3-pip python3-venv espeak-ng fonts-dejavu-core ca-certificates \
    && rm -rf /var/lib/apt/lists/*

RUN python3 -m venv /opt/py && /opt/py/bin/pip install --no-cache-dir \
      --extra-index-url https://download.pytorch.org/whl/cpu \
      yt-dlp faster-whisper "kokoro>=0.7" soundfile torch
ENV PYTHON=/opt/py/bin/python

WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci --omit=dev
COPY . .

ENV NODE_ENV=production PORT=8080 DOSSIER_DONNEES=/data
VOLUME /data
EXPOSE 8080
CMD ["node", "--no-warnings=ExperimentalWarning", "server.mjs"]
