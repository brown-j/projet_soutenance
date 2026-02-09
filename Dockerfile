# 1. Utilise une image Python légère
FROM python:3.10-slim

# 2. Variables d'environnement pour Python et la compilation
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
# Force la compilation sur un seul cœur pour économiser la RAM
ENV MAKEFLAGS="-j1"
ENV CMAKE_BUILD_PARALLEL_LEVEL=1

# 3. Installation des dépendances système (OBLIGATOIRE pour dlib/opencv)
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    libopenblas-dev \
    liblapack-dev \
    libx11-dev \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# 4. Définit le dossier de travail
WORKDIR /app

# 5. Installation des dépendances Python par étapes pour gérer la mémoire
# D'abord les bibliothèques légères
RUN pip install --no-cache-dir \
    Flask \
    gunicorn \
    python-dotenv \
    mysql-connector-python \
    "numpy<2.0.0" \
    Pillow \
    opencv-python-headless

# Ensuite face-recognition (C'est ici que le flag CMAKE_BUILD_PARALLEL_LEVEL=1 est crucial)
RUN pip install --no-cache-dir face-recognition

# 6. Copie le reste du code du projet
COPY . .

# 7. Configuration du port et lancement
ENV PORT 10000
CMD ["sh", "-c", "gunicorn app:app --bind 0.0.0.0:$PORT"]