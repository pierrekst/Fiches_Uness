# Pipeline — Génération de fiches par contenu/présentation séparés

Architecture alternative au pipeline racine (`Config/auto_fiches.py`), conçue
pour réduire drastiquement la consommation de tokens.

## Principe

```
cours .md  →  [Claude]  →  JSON structuré  →  [render.py]  →  HTML
              "quoi dire"   (le contenu)       déterministe   charte fixe
```

L'IA ne produit que le **contenu** (JSON léger). La **présentation** (CSS,
icônes SVG, composants) est appliquée par `render.py` sans aucun token.

## Gains

- Output divisé par ~6 (JSON ~4k vs HTML+agentique ~30k tokens).
- Règles de charte (viewBox, card-icon, rowspan, pas de display:block)
  **garanties par le code** → relecture manuelle supprimée.

## Fichiers

| Fichier | Rôle |
|---|---|
| `render.py` | Moteur JSON → HTML. Icônes + CSS + dispatch récursif. Zéro LLM. |
| `schema.json` | Schéma JSON Schema des fiches (validation + doc). |
| `system_prompt.txt` | Consigne donnée à Claude. |
| `generate.py` | Orchestrateur : .md → Claude → valide → render. |
| `examples/` | JSON de référence écrits à la main (tests du renderer). |
| `out/` | Sorties générées (non versionné). |

## Usage

```bash
python3 render.py examples/283.json out/283.html   # renderer seul (0 token)
python3 generate.py 283 --keep-json                # pipeline complet
```

## Statut

Prototype. Le renderer est validé (6 règles de charte + HTML équilibré sur
l'item 283). Validation de la qualité du JSON produit par l'IA en cours.
