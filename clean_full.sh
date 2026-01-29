#!/bin/bash

# Definition der Dateiendungen, die weg sollen
# Ergänzt um deine spezifischen Glossar- und Index-Dateien aus dem tree-Output
EXTENSIONS=(
    "aux" "log" "out" "toc" "lof" "lot"       # Standard
    "synctex.gz" "fdb_latexmk" "fls"          # Build-Tools
    "bbl" "blg" "bbl-SAVE-ERROR"              # Literaturverzeichnis & Fehler
    "acn" "acr" "alg" "glg" "glo" "gls" "ist" # Glossaries & Acronyms
    "nav" "snm" "vrb"                         # Beamer (falls mal genutzt)
    "xdv" "indent.log"                        # Sonstiges
)

echo "Starte Bereinigung..."

# Loop durch alle Endungen
for ext in "${EXTENSIONS[@]}"; do
    # Löscht Dateien im aktuellen Verzeichnis (ohne Unterordner zu zerstören)
    # 2>/dev/null unterdrückt Fehlermeldungen, falls keine Datei dieses Typs existiert
    rm -f *."$ext" 2>/dev/null
done

# Speziell für Dateien, die mit .bbl-SAVE-ERROR enden (Wildcard am Ende)
rm -f *.bbl-SAVE-ERROR 2>/dev/null

echo "Fertig! Es verbleiben nur .tex, .pdf, .bib und Ressourcen."