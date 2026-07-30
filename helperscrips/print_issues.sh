#!/bin/bash

# Prüfen, ob die GitHub CLI installiert ist
if ! command -v gh &> /dev/null; then
    echo "Fehler: Die GitHub CLI ('gh') ist nicht installiert." >&2
    exit 1
fi

echo "Lade offene Issues..."
echo "--------------------------------------------------"

# GitHub CLI abfrage: offene Issues mit Nummer, Titel und Body
gh issue list --state open --json number,title,body --jq '.[] | "Issue #\(.number): \(.title)\nBeschreibung:\n\(.body // "Keine Beschreibung vorhanden.")\n--------------------------------------------------"'
