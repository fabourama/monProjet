#!/bin/bash

# Demander un message de commit via le terminal (fonctionne sur tous les systèmes)
echo "Entrez votre message de commit :"
read commit_message

# Vérifier si le message de commit est vide
if [ -z "$commit_message" ]; then
    echo "Erreur : Le message de commit ne peut pas être vide."
    exit 1
fi

# Initialiser le dépôt Git (si ce n'est pas déjà fait)
git init

# Ajouter tous les fichiers modifiés
git add .

# Faire le commit avec le message saisi
git commit -m "$commit_message"

# Configurer l'origine si elle n'est pas déjà configurée
if ! git remote -v | grep -q "origin"; then
    git remote add origin https://github.com/fabourama/cours.git
fi

# Passer à la branche principale (si ce n'est pas déjà fait)
git branch -M main

# Pousser les modifications vers GitHub
git push -u origin main
