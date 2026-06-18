#!/usr/bin/env bash
#
# sync_garmin.sh — kopieer nieuwe Garmin-activiteiten van het horloge (MTP)
# naar de lokale OneDrive-map. Kopieert alleen bestanden die lokaal nog
# ontbreken (op bestandsnaam). Bestaande bestanden worden nooit overschreven.
#
set -euo pipefail

DEST="/mnt/hgfs/D/OneDrive/Running/Garmin/ACTIVITY"

# Vind de gekoppelde Garmin automatisch onder gvfs (MTP).
GVFS="/run/user/$(id -u)/gvfs"
MTP_ROOT=$(find "$GVFS" -maxdepth 1 -type d -name 'mtp:host=091e_*' 2>/dev/null | head -1)

if [[ -z "${MTP_ROOT:-}" ]]; then
  echo "FOUT: geen Garmin-horloge gevonden onder $GVFS (is het aangesloten en ontgrendeld?)" >&2
  exit 1
fi

SRC="$MTP_ROOT/Internal Storage/GARMIN/Activity"
if [[ ! -d "$SRC" ]]; then
  echo "FOUT: Activity-map niet gevonden op het horloge: $SRC" >&2
  exit 1
fi

mkdir -p "$DEST"

echo "Bron : $SRC"
echo "Doel : $DEST"
echo

copied=0
skipped=0
for f in "$SRC"/*.fit "$SRC"/*.FIT; do
  [[ -e "$f" ]] || continue
  name=$(basename "$f")
  if [[ -e "$DEST/$name" ]]; then
    skipped=$((skipped+1))
    continue
  fi
  echo "  + $name"
  cp -n "$f" "$DEST/$name"
  copied=$((copied+1))
done

echo
echo "Klaar (horloge → ACTIVITY): $copied nieuw gekopieerd, $skipped al aanwezig."

# --- Fase 2: backup van ALLE activiteit-FIT's naar de projectmap ---------------
# Spiegelt $DEST naar de projectmap zodat het project een self-contained kopie
# heeft (ongeacht of een bestand van het horloge of elders kwam). Alleen nieuwe
# bestanden; bestaande worden nooit overschreven.
PROJECT_DIR=$(dirname "$(readlink -f "$0")")
BACKUP="$PROJECT_DIR/data/activities"
mkdir -p "$BACKUP"

echo
echo "Backup → $BACKUP"
bcopied=0
bskipped=0
for f in "$DEST"/*.fit "$DEST"/*.FIT; do
  [[ -e "$f" ]] || continue
  name=$(basename "$f")
  if [[ -e "$BACKUP/$name" ]]; then
    bskipped=$((bskipped+1))
    continue
  fi
  cp -n "$f" "$BACKUP/$name"
  bcopied=$((bcopied+1))
done
echo "Klaar (backup → project): $bcopied nieuw gekopieerd, $bskipped al aanwezig."
