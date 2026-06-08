#!/usr/bin/env python3
"""
auto_fiches.py — Génère automatiquement les fiches HTML manquantes.

Usage :
  python3 auto_fiches.py                  # 5 fiches, pause 45s
  python3 auto_fiches.py --count 3        # 3 fiches
  python3 auto_fiches.py --count 10 --delay 60
  python3 auto_fiches.py --dry-run        # simulation sans rien exécuter
  python3 auto_fiches.py --list           # affiche les items manquants
"""
import argparse
import glob
import os
import re
import subprocess
import time

BASE_DIR   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # racine Cours_UNESS/
MD_DIR     = os.path.join(BASE_DIR, "LiSa/FichiersMD")
FICHES_DIR = os.path.join(BASE_DIR, "Fiches")
MODEL      = "claude-sonnet-4-6"

CLAUDE_APP_DIR = os.path.expanduser(
    "~/Library/Application Support/Claude/claude-code"
)


def find_claude_binary():
    """Trouve le binaire macOS claude même s'il n'est pas dans le PATH."""
    import shutil
    if shutil.which("claude"):
        return "claude"
    # Binaire natif macOS dans l'app bundle
    if os.path.isdir(CLAUDE_APP_DIR):
        versions = sorted(os.listdir(CLAUDE_APP_DIR), reverse=True)
        for v in versions:
            candidate = os.path.join(
                CLAUDE_APP_DIR, v, "claude.app", "Contents", "MacOS", "claude"
            )
            if os.path.isfile(candidate) and os.access(candidate, os.X_OK):
                return candidate
    raise FileNotFoundError(
        "Binaire claude introuvable. "
        "Assurez-vous que Claude Code est installé."
    )


def get_items_with_md():
    files = sorted(glob.glob(os.path.join(MD_DIR, "*.md")))
    items = []
    for f in files:
        m = re.match(r"^(\d+)\s", os.path.basename(f))
        if m:
            items.append(int(m.group(1)))
    return items


def get_items_with_fiche():
    files = glob.glob(os.path.join(FICHES_DIR, "*.html"))
    nums = set()
    for f in files:
        m = re.match(r"^(\d+)_", os.path.basename(f))
        if m:
            nums.add(int(m.group(1)))
    return nums


def main():
    parser = argparse.ArgumentParser(description="Génère les fiches HTML manquantes")
    parser.add_argument("--count",   type=int, default=5,
                        help="Nombre de fiches à générer (défaut: 5)")
    parser.add_argument("--delay",   type=int, default=45,
                        help="Pause en secondes entre chaque fiche (défaut: 45)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Affiche ce qui serait fait sans rien exécuter")
    parser.add_argument("--list",    action="store_true",
                        help="Liste tous les items manquants et quitte")
    args = parser.parse_args()

    have    = get_items_with_fiche()
    all_md  = get_items_with_md()
    missing = [n for n in all_md if n not in have]

    print(f"Fiches existantes : {len(have)}/{len(all_md)}")
    print(f"Manquantes        : {len(missing)}")

    if args.list:
        for n in missing:
            print(f"  item {n}")
        return

    if not missing:
        print("Toutes les fiches sont déjà générées !")
        return

    batch = missing[:args.count]
    mode  = "[DRY-RUN] " if args.dry_run else ""
    print(f"{mode}Cette session : {len(batch)} fiche(s) — items {batch}\n")

    claude_bin = find_claude_binary()
    failed = []
    for i, num in enumerate(batch, 1):
        print(f"[{i}/{len(batch)}] Item {num}...", end=" ", flush=True)

        if args.dry_run:
            print("(dry-run)")
            continue

        # On demande explicitement à Claude de NE PAS lancer update_avancement.py
        # car on le fait une seule fois à la fin du batch.
        prompt = (
            f"Fais la fiche item {num}. "
            "IMPORTANT : ne lance pas update_avancement.py et ne fais pas de push git — "
            "le script d'automatisation s'en charge une seule fois à la fin du batch."
        )

        result = subprocess.run(
            [claude_bin, "--model", MODEL, "--dangerously-skip-permissions", "-p", prompt],
            cwd=BASE_DIR
        )

        if result.returncode == 0:
            print("OK")
        else:
            print("ERREUR")
            failed.append(num)

        if i < len(batch):
            print(f"  Pause {args.delay}s avant la prochaine fiche...")
            time.sleep(args.delay)

    # Mise à jour avancement + push : UNE SEULE FOIS à la fin
    if not args.dry_run:
        print("\nMise à jour de l'avancement et push...")
        r = subprocess.run(["python3", "update_avancement.py"], cwd=BASE_DIR)
        if r.returncode == 0:
            print("OK")
        else:
            print("ERREUR lors de la mise à jour")

    if failed:
        print(f"\nEchecs : items {failed}")
    elif not args.dry_run:
        done = len(batch) - len(failed)
        print(f"\n{done} fiche(s) générée(s) avec succès.")


if __name__ == "__main__":
    main()
