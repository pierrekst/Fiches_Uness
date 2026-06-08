#!/bin/bash
# ============================================================
# git_auto_push.sh — Push automatique des fiches vers GitHub
# Déclenché par le Launch Agent macOS (WatchPaths sur Fiches/)
# Tourne sous l'identité de l'utilisateur Mac (droits complets)
# ============================================================

REPO="$HOME/Desktop/Cours_UNESS"
LOG="$REPO/logs/git_push.log"

log() { echo "$(date '+%Y-%m-%d %H:%M:%S') $*" >> "$LOG"; }

cd "$REPO" || { log "ERREUR: impossible d'accéder à $REPO"; exit 1; }

# Petite pause pour laisser Claude finir d'écrire tous les fichiers
sleep 3

# Nettoyer les verrous résiduels (laissés par des process interrompus)
rm -f .git/index.lock .git/HEAD.lock .git/refs/heads/*.lock 2>/dev/null

# Vérifier s'il y a des changements à committer
STATUS=$(git status --short Fiches/ avancement_fiches.html 2>/dev/null)
if [[ -z "$STATUS" ]]; then
    log "Rien à committer."
    exit 0
fi

# Préparer et envoyer
git add Fiches/ avancement_fiches.html 2>>"$LOG"
COMMIT_MSG="Auto-push fiches — $(date '+%Y-%m-%d %H:%M')"
git commit -m "$COMMIT_MSG" 2>>"$LOG"
git push 2>>"$LOG"

if [[ $? -eq 0 ]]; then
    log "Push réussi : $COMMIT_MSG"
else
    log "ERREUR lors du push — voir les lignes ci-dessus."
fi
