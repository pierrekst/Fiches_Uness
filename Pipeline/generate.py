#!/usr/bin/env python3
"""
generate.py — Pipeline complet : cours .md → JSON (via Claude) → HTML (render.py).

Backend : claude -p (CLI, auth abonnement). Le cours est passé INLINE dans le
prompt → Claude n'a aucun fichier à lire, il génère directement le JSON. On
récupère le JSON, on le valide, et render.py produit le HTML déterministe.

Usage :
  python3 generate.py 283                       # → out/283.json + out/283.html
  python3 generate.py 283 --model claude-opus-4-8
  python3 generate.py 283 --keep-json           # conserve le JSON intermédiaire
"""
import argparse
import glob
import json
import os
import re
import shutil
import subprocess
import sys
import time

import render

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MD_DIR   = os.path.join(BASE_DIR, "LiSa/FichiersMD")
PIPE_DIR = os.path.dirname(os.path.abspath(__file__))
OUT_DIR  = os.path.join(PIPE_DIR, "out")
MODEL_DEFAULT  = "claude-sonnet-4-6"
CLAUDE_APP_DIR = os.path.expanduser("~/Library/Application Support/Claude/claude-code")


def find_claude_binary():
    if shutil.which("claude"):
        return "claude"
    if os.path.isdir(CLAUDE_APP_DIR):
        for v in sorted(os.listdir(CLAUDE_APP_DIR), reverse=True):
            cand = os.path.join(CLAUDE_APP_DIR, v, "claude.app", "Contents", "MacOS", "claude")
            if os.path.isfile(cand) and os.access(cand, os.X_OK):
                return cand
    raise FileNotFoundError("Binaire claude introuvable.")


def find_md(num):
    matches = glob.glob(os.path.join(MD_DIR, f"{num} *.md"))
    if not matches:
        raise FileNotFoundError(f"Aucun .md pour l'item {num} dans {MD_DIR}")
    return matches[0]


def extract_json(text):
    """Extrait l'objet JSON de la réponse (tolère les fences ```json)."""
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```[a-z]*\n?", "", text)
        text = re.sub(r"\n?```$", "", text).strip()
    # filet de sécurité : du premier { au dernier }
    i, j = text.find("{"), text.rfind("}")
    if i != -1 and j != -1:
        text = text[i:j + 1]
    return json.loads(text)


def validate(data):
    """Validation schéma si jsonschema dispo, sinon contrôles structurels."""
    try:
        import jsonschema
        with open(os.path.join(PIPE_DIR, "schema.json"), encoding="utf-8") as f:
            schema = json.load(f)
        jsonschema.validate(data, schema)
        return "jsonschema OK"
    except ImportError:
        assert "header" in data and "sections" in data, "header/sections manquants"
        assert isinstance(data["sections"], list) and data["sections"], "sections vide"
        return "contrôles basiques OK (jsonschema absent)"


def build_prompt(md_text):
    with open(os.path.join(PIPE_DIR, "system_prompt.txt"), encoding="utf-8") as f:
        system = f.read()
    return f"{system}\n\n=== COURS LiSa ===\n{md_text}\n=== FIN DU COURS ===\n"


def main():
    ap = argparse.ArgumentParser(description="Génère une fiche via le pipeline JSON")
    ap.add_argument("item", type=int, help="Numéro d'item")
    ap.add_argument("--model", default=MODEL_DEFAULT)
    ap.add_argument("--keep-json", action="store_true", help="Conserve le .json intermédiaire")
    args = ap.parse_args()

    os.makedirs(OUT_DIR, exist_ok=True)
    md_path = find_md(args.item)
    with open(md_path, encoding="utf-8") as f:
        md_text = f.read()
    print(f"Source : {os.path.basename(md_path)} ({len(md_text)} car.)")

    prompt = build_prompt(md_text)
    claude_bin = find_claude_binary()

    print(f"Génération du JSON via {args.model}...")
    t0 = time.time()
    result = subprocess.run(
        [claude_bin, "--model", args.model, "--dangerously-skip-permissions",
         "--output-format", "json", "-p", prompt],
        cwd=PIPE_DIR, capture_output=True, text=True
    )
    elapsed = time.time() - t0

    if result.returncode != 0:
        print(f"ERREUR claude (rc={result.returncode}) :\n{result.stderr[:500]}")
        sys.exit(1)

    wrapper = json.loads(result.stdout)
    answer  = wrapper.get("result", "")
    usage   = wrapper.get("usage", {})
    cost    = wrapper.get("total_cost_usd", 0.0)

    try:
        data = extract_json(answer)
    except json.JSONDecodeError as e:
        bad = os.path.join(OUT_DIR, f"{args.item}_RAW.txt")
        with open(bad, "w", encoding="utf-8") as f:
            f.write(answer)
        print(f"ERREUR : JSON invalide ({e}). Réponse brute → {bad}")
        sys.exit(1)

    print(f"Validation : {validate(data)}")

    json_path = os.path.join(OUT_DIR, f"{args.item}.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    html = render.render_fiche(data)
    html_path = os.path.join(OUT_DIR, f"{args.item}.html")
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html)

    if not args.keep_json:
        os.remove(json_path)

    # ── Stats ────────────────────────────────────────────────────────────────
    out_tok = usage.get("output_tokens", 0)
    cr      = usage.get("cache_read_input_tokens", 0)
    cw      = usage.get("cache_creation_input_tokens", 0)
    inp     = usage.get("input_tokens", 0)
    print("\n" + "─" * 48)
    print(f"  ✓ {os.path.basename(html_path)} ({len(html):,} octets)")
    print(f"  Durée   : {elapsed:.0f}s")
    print(f"  Tokens  : in:{inp} cache_r:{cr} cache_w:{cw} out:{out_tok}")
    print(f"  Coût    : ${cost:.4f}")
    print("─" * 48)


if __name__ == "__main__":
    main()
