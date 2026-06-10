#!/usr/bin/env python3
"""
auto_fiches.py — Génère automatiquement les fiches HTML manquantes.

Usage :
  python3 auto_fiches.py                     # 5 fiches, pause 45s
  python3 auto_fiches.py --count 3           # 3 fiches
  python3 auto_fiches.py --count 10 --delay 60
  python3 auto_fiches.py --start-from 280    # reprend à partir de l'item 280
  python3 auto_fiches.py --model claude-opus-4-8
  python3 auto_fiches.py --dry-run           # simulation sans rien exécuter
  python3 auto_fiches.py --list              # affiche les items manquants
"""
import argparse
import glob
import json
import os
import re
import subprocess
import time

BASE_DIR      = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MD_DIR        = os.path.join(BASE_DIR, "LiSa/FichiersMD")
FICHES_DIR    = os.path.join(BASE_DIR, "Fiches")
MODEL_DEFAULT = "claude-sonnet-4-6"

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


def run_fiche(claude_bin, model, num):
    """Lance Claude pour un item. Retourne (returncode, stats_dict, elapsed_s)."""
    prompt = (
        f"Fais la fiche item {num}. "
        "IMPORTANT : ne lance pas update_avancement.py et ne fais pas de push git — "
        "le script d'automatisation s'en charge une seule fois à la fin du batch."
    )
    t0 = time.time()
    result = subprocess.run(
        # --dangerously-skip-permissions requis pour le mode non-interactif (-p) :
        # sans lui, Claude demande confirmation à chaque outil (Read, Write, Bash).
        # Portée limitée : CLAUDE.md contraint les actions autorisées.
        [claude_bin, "--model", model, "--dangerously-skip-permissions",
         "--output-format", "json", "-p", prompt],
        cwd=BASE_DIR, capture_output=True, text=True
    )
    elapsed = time.time() - t0
    stats = {}
    if result.returncode == 0:
        try:
            data = json.loads(result.stdout)
            usage = data.get("usage", {})
            stats = {
                "input_tokens": usage.get("input_tokens", 0),
                "cache_read":   usage.get("cache_read_input_tokens", 0),
                "cache_write":  usage.get("cache_creation_input_tokens", 0),
                "output_tokens": usage.get("output_tokens", 0),
                "cost_usd":     data.get("total_cost_usd", 0.0),
            }
        except (json.JSONDecodeError, AttributeError):
            pass
    return result.returncode, stats, elapsed


def fiche_exists(num):
    """Vérifie qu'un fichier HTML pour cet item existe dans Fiches/."""
    return bool(glob.glob(os.path.join(FICHES_DIR, f"{num}_*.html")))


def main():
    parser = argparse.ArgumentParser(description="Génère les fiches HTML manquantes")
    parser.add_argument("--count",      type=int, default=5,
                        help="Nombre de fiches à générer (défaut: 5)")
    parser.add_argument("--delay",      type=int, default=45,
                        help="Délai cible en secondes entre fiches (défaut: 45)")
    parser.add_argument("--model",      default=MODEL_DEFAULT,
                        help=f"Modèle Claude (défaut: {MODEL_DEFAULT})")
    parser.add_argument("--start-from", type=int, default=None, dest="start_from",
                        help="Premier item à traiter (numéro)")
    parser.add_argument("--retry",      type=int, default=1,
                        help="Tentatives supplémentaires en cas d'échec (défaut: 1)")
    parser.add_argument("--dry-run",    action="store_true",
                        help="Affiche ce qui serait fait sans rien exécuter")
    parser.add_argument("--list",       action="store_true",
                        help="Liste tous les items manquants et quitte")
    args = parser.parse_args()

    have   = get_items_with_fiche()
    all_md = get_items_with_md()
    missing = [n for n in all_md if n not in have]
    if args.start_from is not None:
        missing = [n for n in missing if n >= args.start_from]

    print(f"Fiches existantes : {len(have)}/{len(all_md)}")
    suffix = f" (depuis item {args.start_from})" if args.start_from else ""
    print(f"Manquantes        : {len(missing)}{suffix}")

    if args.list:
        for n in missing:
            print(f"  item {n}")
        return

    if not missing:
        print("Toutes les fiches sont déjà générées !")
        return

    batch = missing[:args.count]
    mode  = "[DRY-RUN] " if args.dry_run else ""
    print(f"{mode}Cette session : {len(batch)} fiche(s) — items {batch}")
    print(f"Modèle : {args.model}\n")

    claude_bin = find_claude_binary()
    failed     = []
    all_stats  = []

    for i, num in enumerate(batch, 1):
        print(f"[{i}/{len(batch)}] Item {num}...", end=" ", flush=True)

        if args.dry_run:
            print("(dry-run)")
            continue

        success = False
        stats   = {}
        elapsed = 0.0

        for attempt in range(args.retry + 1):
            rc, stats, elapsed = run_fiche(claude_bin, args.model, num)
            if fiche_exists(num):
                success = True
                break
            reason = f"returncode={rc}, fiche absente"
            print(f"\n  Tentative {attempt + 1} échouée ({reason})", end=" ", flush=True)
            if attempt < args.retry:
                print("— retry dans 15s...", end=" ", flush=True)
                time.sleep(15)

        if success:
            inp  = stats.get("input_tokens", 0)
            cr   = stats.get("cache_read", 0)
            cw   = stats.get("cache_write", 0)
            out  = stats.get("output_tokens", 0)
            cost = stats.get("cost_usd", 0.0)
            print(f"OK  [{elapsed:.0f}s | in:{inp} cr:{cr} cw:{cw} out:{out} | ${cost:.4f}]")
            all_stats.append(stats)
        else:
            print(f"\n  ECHEC définitif")
            failed.append(num)

        if i < len(batch):
            wait = max(0, args.delay - elapsed)
            if wait > 0:
                print(f"  Pause {wait:.0f}s...")
                time.sleep(wait)

    # ── Mise à jour avancement + push UNE SEULE FOIS ─────────────────────────
    if not args.dry_run:
        print("\nMise à jour de l'avancement et push...")
        r = subprocess.run(["python3", "Config/update_avancement.py"], cwd=BASE_DIR)
        if r.returncode != 0:
            print("ERREUR lors de la mise à jour")

    # ── Résumé de consommation ────────────────────────────────────────────────
    if all_stats:
        total_in   = sum(s.get("input_tokens", 0) for s in all_stats)
        total_cr   = sum(s.get("cache_read", 0)   for s in all_stats)
        total_cw   = sum(s.get("cache_write", 0)  for s in all_stats)
        total_out  = sum(s.get("output_tokens", 0) for s in all_stats)
        total_cost = sum(s.get("cost_usd", 0.0)   for s in all_stats)
        done       = len(all_stats)
        print("\n" + "═" * 52)
        print(f"  RÉSUMÉ — {done} fiche(s) générée(s)")
        print("═" * 52)
        print(f"  Tokens input      : {total_in:>8,}")
        print(f"  Cache read        : {total_cr:>8,}")
        print(f"  Cache write       : {total_cw:>8,}")
        print(f"  Tokens output     : {total_out:>8,}")
        print(f"  Coût total        :  ${total_cost:.4f}")
        if done > 1:
            print(f"  Coût moyen/fiche  :  ${total_cost / done:.4f}")
        print("═" * 52)

    if failed:
        print(f"\nEchecs : items {failed}")


if __name__ == "__main__":
    main()
