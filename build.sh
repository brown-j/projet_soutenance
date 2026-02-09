#!/usr/bin/env bash
# Arrêter le script en cas d'erreur
set -o errexit

pip install --upgrade pip
pip install cmake
pip install -r requirements.txt