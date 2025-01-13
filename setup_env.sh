#!/bin/bash

# Nom de l'environnement virtuel
env=".venv7"

# Fichier log pour enregistrer les erreurs
log_file="install_log.txt"

# Réinitialiser le fichier log au début
> $log_file

# Créer un environnement virtuel avec Python
echo "Création de l'environnement virtuel..."
python3.11 -m venv $env >> $log_file 2>&1
if [ $? -ne 0 ]; then
    echo "Erreur lors de la création de l'environnement virtuel. Consultez le fichier log pour plus de détails."
    exit 1
fi

# Activer l'environnement virtuel
echo "Activation de l'environnement virtuel..."
source $env/Scripts/activate >> $log_file 2>&1
if [ $? -ne 0 ]; then
    echo "Erreur lors de l'activation de l'environnement virtuel. Consultez le fichier log pour plus de détails."
    exit 1
fi

# Mettre à jour pip dans l'environnement virtuel
echo "Mise à jour de pip..."
python -m pip install --upgrade pip >> $log_file 2>&1
if [ $? -ne 0 ]; then
    echo "Erreur lors de la mise à jour de pip. Consultez le fichier log pour plus de détails."
    exit 1
fi

# Installer les packages nécessaires
echo "Installation des packages..."
# pip install fastapi uvicorn pandas numpy scikit-learn shap==0.43.0 requests lightgbm >> $log_file 2>&1
pip install -r requirements_pipdeptree.txt >> $log_file 2>&1
if [ $? -ne 0 ]; then
    echo "Erreur lors de l'installation des packages. Consultez le fichier log pour plus de détails."
    exit 1
fi

# Si tout s'est bien passé, afficher le message de succès
echo "Installation terminée avec succès!"
