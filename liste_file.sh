#!/bin/bash

# Répertoire à lister (par défaut, le répertoire courant)
directory=${1:-.}

# Fichier de sortie pour la liste des fichiers et dossiers
output_file="file_list.txt"

# Lister tous les fichiers et dossiers à la racine du répertoire sans entrer dans les sous-répertoires
echo "Listing all files and directories in $directory (without subdirectories) into $output_file..."

# Utilisation de `find` avec `-maxdepth 1` pour lister uniquement les fichiers et dossiers à la racine
find "$directory" -maxdepth 1 -print > "$output_file"

echo "La liste des fichiers et dossiers à la racine a été enregistrée dans $output_file"


# ./liste_file.sh /path/to/directory
