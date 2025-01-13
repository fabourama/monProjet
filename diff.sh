#!/bin/bash

# Nom des fichiers à comparer
file1="packages_with_versions.txt"
file2="requirements_pipdeptree.txt"
diff_file="diff.txt"

# Créer/vider le fichier diff.txt
> "$diff_file"

# Lignes décoratives pour embellir l'affichage
line="#--------------------------------------------------------------------------"

# Trier les fichiers et enlever les espaces blancs avant et après chaque ligne
sort "$file1" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//' > "$file1.sorted"
sort "$file2" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//' > "$file2.sorted"

# Lignes communes : Utilise comm pour obtenir les lignes communes entre file1 et file2
echo "$line" >> "$diff_file"
echo "Lignes communes entre $file1 et $file2 :" >> "$diff_file"
echo "$line" >> "$diff_file"
comm -12 "$file1.sorted" "$file2.sorted" >> "$diff_file"
echo "" >> "$diff_file"

# Lignes uniquement dans file1 : Utilise comm pour obtenir les lignes uniquement dans file1
echo "$line" >> "$diff_file"
echo "Lignes uniquement dans $file1 :" >> "$diff_file"
echo "$line" >> "$diff_file"
comm -23 "$file1.sorted" "$file2.sorted" >> "$diff_file"
echo "" >> "$diff_file"

# Lignes uniquement dans file2 : Utilise comm pour obtenir les lignes uniquement dans file2
echo "$line" >> "$diff_file"
echo "Lignes uniquement dans $file2 :" >> "$diff_file"
echo "$line" >> "$diff_file"
comm -13 "$file1.sorted" "$file2.sorted" >> "$diff_file"

# Nettoyage des fichiers temporaires
rm "$file1.sorted" "$file2.sorted"

echo "Les différences ont été enregistrées dans $diff_file"
