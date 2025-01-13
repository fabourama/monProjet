#!/bin/bash

# Nom de l'environnement virtuel
env=".venv7"

# Créer un environnement virtuel avec Python 3.11
python3.11 -m venv $env

# Activer l'environnement virtuel (pour les systèmes Unix)
# source $env/bin/activate
source $env/Scripts/activate

# Mettre à jour pip dans l'environnement virtuel
python -m pip install --upgrade pip

# Installer les packages nécessaires
pip install fastapi uvicorn pandas numpy scikit-learn shap requests

echo "Installation terminée avec succès!"
