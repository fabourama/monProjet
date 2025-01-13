#!/bin/bash

# Vérifier que le répertoire est fourni en argument, sinon utiliser le répertoire courant
directory=${1:-.}

# Fichier pour la liste des fichiers
output_file="file_list.txt"

# Fichier .gitignore
gitignore_file=".gitignore"

# Lister tous les fichiers du répertoire dans un fichier texte
echo "Listing all files in the directory $directory into $output_file..."
find "$directory" -type f > "$output_file"

# Alimenter le fichier .gitignore avec ces fichiers
echo "Adding files from $output_file to $gitignore..."
while IFS= read -r file; do
    # Ajouter le fichier à .gitignore (en évitant les doublons)
    if ! grep -q "^$file" "$gitignore_file"; then
        echo "$file" >> "$gitignore_file"
    fi
done < "$output_file"

echo "Process completed!"

# ./list_and_ignore.sh /path/to/directory
