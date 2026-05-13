# 1. Utilise une image Python légère
FROM python:3.10-slim

# 2. Variables d'environnement
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
# Optimisation pour la compilation de dlib (face-recognition) sur des petits serveurs
ENV MAKEFLAGS="-j1"
ENV CMAKE_BUILD_PARALLEL_LEVEL=1

# 3. Dépendances système (Version compatible Debian Trixie/Slim)
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    libopenblas-dev \
    liblapack-dev \
    libx11-dev \
    libgl1 \
    libsm6 \
    libxext6 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# 4. Dossier de travail
WORKDIR /app

# 5. Installation des dépendances Python
# On installe d'abord les outils de base
RUN pip install --no-cache-dir --upgrade pip

# Installation groupée pour optimiser les couches Docker
# Note : Celery et Redis sont ajoutés ici pour corriger ton erreur
RUN pip install --no-cache-dir \
    Flask \
    gunicorn \
    celery \
    redis \
    python-dotenv \
    mysql-connector-python \
    "numpy<2.0.0" \
    Pillow \
    opencv-python-headless

# Installation de face-recognition (lourd, séparé pour le cache)
RUN pip install --no-cache-dir face-recognition

# 6. Copie des fichiers du projet
COPY requirements.txt .
# Au cas où tu as d'autres libs dans ton requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# 7. Configuration du port et lancement
ENV PORT 10000

# Utilisation d'un script ou d'une commande directe
# Note : En production, Flask et Celery Worker doivent souvent être lancés séparément.
# Cette commande lance uniquement l'interface Web.
CMD gunicorn app:app --bind 0.0.0.0:$PORT