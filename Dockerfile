# Utilise une image Python légère
FROM python:3.10-slim

# Évite que Python génère des fichiers .pyc et permet l'affichage des logs en temps réel
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Installation des dépendances système nécessaires pour compiler dlib et opencv
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    libopenblas-dev \
    liblapack-dev \
    libx11-dev \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Définit le dossier de travail
WORKDIR /app

# Copie le fichier des dépendances
COPY requirements.txt .

# Installe les dépendances Python (le cache est désactivé pour économiser de l'espace)
RUN pip install --no-cache-dir -r requirements.txt

# Copie tout le reste du code
COPY . .

# Définit le port par défaut (Render injectera sa propre valeur via la variable $PORT)
ENV PORT 10000

# Commande pour lancer l'application avec Gunicorn
CMD ["sh", "-c", "gunicorn app:app --bind 0.0.0.0:$PORT"]