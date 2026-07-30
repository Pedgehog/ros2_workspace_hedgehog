#!/bin/bash

if ! git rev-parse --is-inside-work-tree &> /dev/null; then
    echo "Fehler: Du bist in keinem Git-Repository."
    exit 1
fi

echo "Durchsuche Git-Historie nach Issue-Nummern (#...)..."
echo "--------------------------------------------------"

# Alle Nummern holen, #0 direkt rausfiltern
issue_numbers=$(git log --oneline | grep -oE '#[0-9]+' | tr -d '#' | grep -v '^0$' | sort -un)

if [ -z "$issue_numbers" ]; then
    echo "Keine Issue-Referenzen (#...) in der Commit-Historie gefunden."
    exit 0
fi

# Prüfen ob GitHub Remote existiert und gh bereit ist
has_github=false
if command -v gh &> /dev/null && gh auth status &> /dev/null && git remote -v | grep -q "github.com"; then
    has_github=true
fi

all_local_closed=true
all_gh_closed=true

for issue in $issue_numbers; do
    # 1. Lokale Prüfung (Commit-Log nach 'Closes #X' oder 'Fixes #X')
    local_closed=false
    if git log --grep="[Cc]loses #$issue" --grep="[Ff]ixes #$issue" --oneline | grep -q .; then
        local_closed=true
    fi

    if [ "$local_closed" = true ]; then
        local_status="CLOSED (lokal)"
    else
        local_status="OPEN (lokal)"
        all_local_closed=false
    fi

    # 2. GitHub-Prüfung (falls GitHub verfügbar)
    if [ "$has_github" = true ]; then
        gh_state=$(gh issue view "$issue" --json state --jq '.state' 2>/dev/null)
        if [ "$gh_state" = "CLOSED" ]; then
            gh_status="CLOSED (GitHub)"
        elif [ "$gh_state" = "OPEN" ]; then
            gh_status="OPEN (GitHub)"
            all_gh_closed=false
        else
            gh_status="NICHT GEFUNDEN (GitHub)"
            all_gh_closed=false
        fi
        echo "Issue #$issue -> Lokaler Log: $local_status | GitHub: $gh_status"
    else
        echo "Issue #$issue -> Lokaler Log: $local_status | GitHub: Keins/Nicht konfiguriert"
    fi
done

echo "--------------------------------------------------"
if [ "$all_local_closed" = true ]; then
    echo "Ergebnis Lokaler Log: Alle Issues sind im Log als geschlossen markiert."
else
    echo "Ergebnis Lokaler Log: Es gibt noch offene Issues im Log."
fi

if [ "$has_github" = true ]; then
    if [ "$all_gh_closed" = true ]; then
        echo "Ergebnis GitHub: Alle Issues sind auf GitHub geschlossen."
    else
        echo "Ergebnis GitHub: Es gibt noch offene Issues auf GitHub."
    fi
fi
