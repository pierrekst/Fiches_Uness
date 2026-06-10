#!/usr/bin/env python3
"""
render.py — Moteur de rendu déterministe JSON → HTML pour les fiches UNESS.

Aucun LLM ici. On reçoit un JSON conforme à schema.json et on émet le HTML
final en appliquant la charte. Les règles absolues (viewBox, card-icon,
rowspan, pas de display:block) sont garanties par le code → impossibles à
violer.

Usage :
  python3 render.py examples/283.json            # → stdout
  python3 render.py examples/283.json out/283.html
"""
import html as _html
import json
import sys

# ─────────────────────────────────────────────────────────────────────────────
# REGISTRE D'ICÔNES — paths Tabler extraits de Config/template_fiche.html.
# icon(name) garantit toujours viewBox="0 0 24 24".
# ─────────────────────────────────────────────────────────────────────────────
ICONS = {
    "definition":   '<path d="M3 19a9 9 0 0 1 9 0a9 9 0 0 1 9 0"/><path d="M3 6a9 9 0 0 1 9 0a9 9 0 0 1 9 0"/><line x1="3" y1="6" x2="3" y2="19"/><line x1="12" y1="6" x2="12" y2="19"/><line x1="21" y1="6" x2="21" y2="19"/>',
    "epidemio":     '<rect x="3" y="12" width="6" height="8" rx="1"/><rect x="9" y="8" width="6" height="12" rx="1"/><rect x="15" y="4" width="6" height="16" rx="1"/><line x1="4" y1="20" x2="18" y2="20"/>',
    "physiopath":   '<path d="M3 12h4l3 8l4-16l3 8h4"/>',
    "mecanisme":    '<path d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 0 0 2.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 0 0 1.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 0 0-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 0 0-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 0 0-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 0 0-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 0 0 1.066-2.573c-.94-1.543.826-3.31 2.37-2.37c1 .608 2.296.07 2.572-1.065z"/><circle cx="12" cy="12" r="3"/>',
    "diagnostic":   '<circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>',
    "traitement":   '<path d="M4.5 12.5l8-8a4.94 4.94 0 0 1 7 7l-8 8a4.94 4.94 0 0 1-7-7"/><line x1="8.5" y1="8.5" x2="15.5" y2="15.5"/>',
    "complications":'<path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/>',
    "synthese":     '<polyline points="20 6 9 17 4 12"/>',
    "info":         '<circle cx="12" cy="12" r="9"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/>',
}

# Couleurs autorisées pour les pastilles d'icône et variantes.
ICON_COLORS  = {"purple", "blue", "teal", "red", "amber", "coral"}
ALERT_COLORS = {"red", "blue", "green", "amber", "teal"}
# Icône par défaut d'une alerte selon sa couleur.
ALERT_DEFAULT_ICON = {
    "red": "complications", "amber": "complications",
    "green": "synthese", "blue": "info", "teal": "info",
}


def icon(name):
    """Émet un <svg> Tabler avec viewBox garanti. Inconnu → info."""
    path = ICONS.get(name, ICONS["info"])
    return (f'<svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">'
            f'{path}</svg>')


# ─────────────────────────────────────────────────────────────────────────────
# RENDU DES BLOCS — dispatch récursif sur block["type"].
# Les champs "rich" (titres, cellules, html d'alerte…) sont du HTML inline de
# confiance (<strong>/<em>/<br>/<span class="badge">) : passés tels quels.
# ─────────────────────────────────────────────────────────────────────────────
def render_blocks(blocks):
    return "\n".join(render_block(b) for b in (blocks or []))


def render_block(b):
    t = b.get("type")
    fn = _DISPATCH.get(t)
    if fn is None:
        # Garde-fou : type inconnu → commentaire visible, jamais de crash.
        return f"<!-- bloc inconnu: {_html.escape(str(t))} -->"
    return fn(b)


def _card(b):
    variant = b.get("variant")
    cls = "card" + (f" card-{variant}" if variant in ICON_COLORS else "")
    color = b.get("icon_color", "purple")
    color = color if color in ICON_COLORS else "purple"
    ic = b.get("icon", "info")
    # RÈGLE : tout .card-title contient toujours un .card-icon.
    title = (
        '<div class="card-title">'
        f'<div class="card-icon" style="background:var(--{color});">{icon(ic)}</div>'
        f'{b.get("title", "")}</div>'
    )
    return f'<div class="{cls}">{title}{render_blocks(b.get("blocks"))}</div>'


def _grid(b):
    cols = 3 if b.get("cols") == 3 else 2
    return f'<div class="grid{cols}">{render_blocks(b.get("blocks"))}</div>'


def _alert(b):
    color = b.get("color", "blue")
    color = color if color in ALERT_COLORS else "blue"
    ic = b.get("icon") or ALERT_DEFAULT_ICON[color]
    return (
        f'<div class="alert alert-{color}">'
        f'<div class="alert-icon">{icon(ic)}</div>'
        f'<div>{b.get("html", "")}</div></div>'
    )


def _cell(c, tag):
    """Rend une cellule de tableau. c = str (rich) ou {html, rowspan, colspan}."""
    if isinstance(c, str):
        return f"<{tag}>{c}</{tag}>"
    attrs = ""
    style = ""
    rs = c.get("rowspan")
    cs = c.get("colspan")
    if rs and int(rs) > 1:
        attrs += f' rowspan="{int(rs)}"'
        # RÈGLE : cellule rowspan toujours centrée verticalement.
        style = "vertical-align:middle; text-align:center;"
    if cs and int(cs) > 1:
        attrs += f' colspan="{int(cs)}"'
    if c.get("style"):
        style = (style + c["style"]) if style else c["style"]
    if style:
        attrs += f' style="{style}"'
    return f"<{tag}{attrs}>{c.get('html', '')}</{tag}>"


def _table(b):
    variant = b.get("variant")
    cls = f"table-{variant}" if variant in ICON_COLORS else ""
    cls_attr = f' class="{cls}"' if cls else ""
    thead = ""
    if b.get("headers"):
        ths = "".join(_cell(h, "th") for h in b["headers"])
        thead = f"<thead><tr>{ths}</tr></thead>"
    rows = ""
    for row in b.get("rows", []):
        tds = "".join(_cell(c, "td") for c in row)
        rows += f"<tr>{tds}</tr>"
    return f"<table{cls_attr}>{thead}<tbody>{rows}</tbody></table>"


def _kv(b):
    rows = "".join(
        f'<div class="kv-row"><span class="kv-key">{r.get("key","")}</span>'
        f'<span class="kv-val">{r.get("val","")}</span></div>'
        for r in b.get("rows", [])
    )
    return rows


def _steps(b):
    lis = ""
    for s in b.get("items", []):
        num_cls = "step-num step-num-red" if s.get("danger") else "step-num"
        content = (f'<div class="step-content">{s["content"]}</div>'
                   if s.get("content") else "")
        lis += (
            f'<li><div class="{num_cls}">{s.get("num","")}</div>'
            f'<div><div class="step-title">{s.get("title","")}</div>'
            f'{content}</div></li>'
        )
    return f'<ol class="steps">{lis}</ol>'


def _pills(b):
    items = "".join(
        f'<span class="pill pill-{p.get("color","gray")}">{p.get("text","")}</span>'
        for p in b.get("items", [])
    )
    return f'<div class="pills">{items}</div>'


def _list(b):
    items = "".join(f"<li>{it}</li>" for it in b.get("items", []))
    return f'<ul class="lst">{items}</ul>'


def _phase(b):
    kind = b.get("kind", "prod")  # prod | mod | sev
    kind = kind if kind in {"prod", "mod", "sev"} else "prod"
    return f'<span class="phase phase-{kind}">{b.get("text","")}</span>'


def _raw(b):
    """Échappatoire : HTML brut quand le schéma ne suffit pas."""
    return b.get("html", "")


_DISPATCH = {
    "card": _card, "grid": _grid, "alert": _alert, "table": _table,
    "kv": _kv, "steps": _steps, "pills": _pills, "list": _list,
    "phase": _phase, "html": _raw,
}


# ─────────────────────────────────────────────────────────────────────────────
# ASSEMBLAGE DE LA PAGE
# ─────────────────────────────────────────────────────────────────────────────
def _header(h):
    tags = "".join(f'<span class="htag">{t}</span>' for t in h.get("tags", []))
    tags_block = f'<div class="header-tags">{tags}</div>' if tags else ""
    sub = f'<div class="header-sub">{h["subtitle"]}</div>' if h.get("subtitle") else ""
    return (
        '<div class="header">'
        f'<div class="header-num">Item {h.get("num","")}</div>'
        f'<h1>{h.get("title","")}</h1>{sub}{tags_block}</div>'
    )


def _section(s):
    ic = icon(s.get("icon", "info"))
    title = f'<div class="section-title">{ic}{s.get("title","")}</div>'
    return title + render_blocks(s.get("blocks"))


def render_fiche(data):
    parts = ['<div class="page">', _header(data["header"])]
    if data.get("objectifs"):
        parts.append(f'<div class="objectifs">{data["objectifs"]}</div>')
    sections = data.get("sections", [])
    for i, s in enumerate(sections):
        parts.append(_section(s))
        if i < len(sections) - 1:
            parts.append("<hr>")
    parts.append("</div>")
    body = "\n".join(parts)
    return _PAGE.replace("{{TITRE}}", data["header"].get("title", "Fiche")) \
               .replace("{{BODY}}", body)


# ─────────────────────────────────────────────────────────────────────────────
# SQUELETTE + CSS (charte copiée verbatim depuis Config/template_fiche.html).
# Invariant : jamais regénéré par un LLM.
# ─────────────────────────────────────────────────────────────────────────────
_PAGE = """<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{{TITRE}}</title>
<link rel="icon" href="../Config/favicon.svg">
<style>
  :root {
    --purple:#534AB7; --purple-light:#eeecfb;
    --teal:#1D9E75;   --teal-light:#e6f7f2;
    --coral:#D85A30;  --coral-light:#fbeee9;
    --blue:#378ADD;   --blue-light:#eaf2fc;
    --red:#E24B4A;    --red-light:#fdeaea;
    --amber:#C97B2A;  --amber-light:#fdf3e3;
    --text:#1e2029; --muted:#6b7280;
    --border:#e5e7eb; --bg:#f9fafb; --card:#fff;
  }
  @media (prefers-color-scheme:dark){
    :root{
      --text:#e8eaf0; --muted:#9ca3af;
      --border:#2d3040; --bg:#141520; --card:#1e2030;
      --purple-light:#1e1b3a; --teal-light:#0f2a22;
      --coral-light:#2a1810; --blue-light:#0f1e2e;
      --red-light:#2a0f0f; --amber-light:#2a1e0a;
    }
  }
  *{box-sizing:border-box;margin:0;padding:0;}
  body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:var(--bg);color:var(--text);font-size:.9rem;line-height:1.5;padding:20px;}
  .page{max-width:920px;margin:0 auto;}
  .header{background:linear-gradient(135deg,#534AB7 0%,#378ADD 60%,#1D9E75 100%);border-radius:16px;padding:28px 32px;margin-bottom:24px;color:#fff;}
  .header-num{font-size:.8rem;font-weight:700;letter-spacing:2px;text-transform:uppercase;opacity:.8;margin-bottom:6px;}
  .header h1{font-size:1.9rem;font-weight:800;margin-bottom:10px;}
  .header-tags{display:flex;flex-wrap:wrap;gap:8px;margin-top:12px;}
  .htag{background:rgba(255,255,255,.18);border-radius:20px;padding:3px 12px;font-size:.75rem;font-weight:600;}
  .objectifs{background:var(--blue-light);border-left:4px solid var(--blue);border-radius:10px;padding:14px 18px;margin-bottom:22px;font-size:.84rem;color:var(--blue);}
  .objectifs strong{font-weight:800;}
  hr{border:none;border-top:1.5px solid var(--border);margin:22px 0;}
  .card{background:var(--card);border:0.5px solid var(--border);border-radius:14px;padding:18px 20px;margin-bottom:14px;}
  .card-title{font-size:.88rem;font-weight:700;color:var(--text);margin-bottom:10px;display:flex;align-items:center;gap:8px;}
  .card-icon{width:28px;height:28px;border-radius:7px;flex-shrink:0;display:flex;align-items:center;justify-content:center;}
  .card-icon svg{width:15px;height:15px;fill:none;stroke:#fff;stroke-width:1.8;stroke-linecap:round;stroke-linejoin:round;}
  .grid2{display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-bottom:14px;}
  .grid3{display:grid;grid-template-columns:1fr 1fr 1fr;gap:14px;margin-bottom:14px;}
  @media(max-width:640px){.grid2,.grid3{grid-template-columns:1fr;}}
  .alert{border-radius:10px;padding:11px 16px;font-size:.84rem;margin-bottom:10px;line-height:1.55;display:flex;gap:10px;align-items:flex-start;}
  .alert strong{font-weight:800;}
  .alert-icon{flex-shrink:0;margin-top:1px;}
  .alert-icon svg{width:15px;height:15px;fill:none;stroke-width:1.8;stroke-linecap:round;stroke-linejoin:round;}
  .alert-red   {background:var(--red-light);  color:var(--red);  border-left:3px solid var(--red);  }
  .alert-blue  {background:var(--blue-light); color:var(--blue); border-left:3px solid var(--blue); }
  .alert-green {background:var(--teal-light); color:var(--teal); border-left:3px solid var(--teal); }
  .alert-amber {background:var(--amber-light);color:var(--amber);border-left:3px solid var(--amber);}
  .alert-teal  {background:var(--teal-light); color:var(--teal); border-left:3px solid var(--teal); }
  .alert-red   .alert-icon svg{stroke:var(--red);  }
  .alert-blue  .alert-icon svg{stroke:var(--blue); }
  .alert-green .alert-icon svg{stroke:var(--teal); }
  .alert-amber .alert-icon svg{stroke:var(--amber);}
  .alert-teal  .alert-icon svg{stroke:var(--teal); }
  .pills{display:flex;flex-wrap:wrap;gap:6px;margin-top:6px;}
  .pill{border-radius:20px;padding:3px 11px;font-size:.76rem;font-weight:600;}
  .pill-red   {background:var(--red-light);   color:var(--red);   }
  .pill-blue  {background:var(--blue-light);  color:var(--blue);  }
  .pill-teal  {background:var(--teal-light);  color:var(--teal);  }
  .pill-amber {background:var(--amber-light); color:var(--amber); }
  .pill-purple{background:var(--purple-light);color:var(--purple);}
  .pill-coral {background:var(--coral-light); color:var(--coral); }
  .pill-gray{background:#f3f4f6;color:#6b7280;}
  .kv-row{display:flex;justify-content:space-between;align-items:center;padding:6px 0;border-bottom:1px solid var(--border);font-size:.84rem;}
  .kv-row:last-child{border-bottom:none;}
  .kv-key{color:var(--muted);flex:1;}
  .kv-val{font-weight:700;color:var(--text);text-align:right;}
  table{width:100%;border-collapse:collapse;font-size:.82rem;margin-top:8px;}
  th{background:var(--purple-light);color:var(--purple);font-weight:700;padding:8px 10px;text-align:left;}
  td{padding:7px 10px;border-bottom:1px solid var(--border);vertical-align:top;}
  tr:last-child td{border-bottom:none;}
  tr:hover td{background:var(--bg);}
  .steps{list-style:none;padding:0;}
  .steps li{display:flex;gap:12px;align-items:flex-start;padding:8px 0;border-bottom:1px solid var(--border);font-size:.85rem;}
  .steps li:last-child{border-bottom:none;}
  .step-num{min-width:24px;height:24px;border-radius:50%;background:var(--purple-light);color:var(--purple);font-weight:800;font-size:.75rem;display:flex;align-items:center;justify-content:center;flex-shrink:0;}
  .step-num-red{background:var(--red-light);color:var(--red);}
  .step-title{font-weight:700;margin-bottom:2px;}
  .step-content{font-size:.83rem;color:var(--muted);}
  ul.lst,ul.list{padding-left:16px;margin-top:6px;}
  ul.lst li,ul.list li{margin-bottom:4px;font-size:.84rem;}
  .badge{display:inline-block;padding:2px 8px;border-radius:5px;font-size:.72rem;font-weight:700;margin-left:4px;}
  .badge-red   {background:var(--red-light);  color:var(--red);  }
  .badge-amber {background:var(--amber-light);color:var(--amber);}
  .badge-green {background:var(--teal-light); color:var(--teal); }
  .badge-blue  {background:var(--blue-light); color:var(--blue); }
  .badge-purple{background:var(--purple-light);color:var(--purple);}
  .phase{display:inline-block;color:#fff;font-size:.72rem;font-weight:700;padding:2px 8px;border-radius:6px;margin-bottom:4px;}
  .phase-prod{background:var(--teal);}
  .phase-mod {background:var(--amber);}
  .phase-sev {background:var(--red);}
  .bl-red   {border-left:4px solid var(--red);  padding-left:12px;}
  .bl-amber {border-left:4px solid var(--amber);padding-left:12px;}
  .bl-blue  {border-left:4px solid var(--blue); padding-left:12px;}
  .bl-teal  {border-left:4px solid var(--teal); padding-left:12px;}
  .section-badge{display:inline-flex;align-items:center;justify-content:center;color:#fff;font-size:.68rem;font-weight:700;padding:3px 10px;border-radius:20px;}
  .table-blue th {background:var(--blue-light); color:var(--blue); }
  .table-teal th {background:var(--teal-light); color:var(--teal); }
  .table-red  th {background:var(--red-light);  color:var(--red);  }
  .table-amber th{background:var(--amber-light);color:var(--amber);}
  .card-red   {border-left:4px solid var(--red);   }
  .card-blue  {border-left:4px solid var(--blue);  }
  .card-teal  {border-left:4px solid var(--teal);  }
  .card-amber {border-left:4px solid var(--amber); }
  .card-purple{border-left:4px solid var(--purple);}
  .section-title{font-size:1rem;font-weight:800;color:var(--purple);margin:22px 0 12px;display:flex;align-items:center;gap:8px;}
  .section-title svg{width:18px;height:18px;fill:none;stroke:var(--purple);stroke-width:1.8;stroke-linecap:round;stroke-linejoin:round;}
</style>
</head>
<body>
{{BODY}}
</body>
</html>
"""


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 render.py <fiche.json> [sortie.html]", file=sys.stderr)
        sys.exit(1)
    with open(sys.argv[1], encoding="utf-8") as f:
        data = json.load(f)
    out = render_fiche(data)
    if len(sys.argv) >= 3:
        with open(sys.argv[2], "w", encoding="utf-8") as f:
            f.write(out)
        print(f"✓ {sys.argv[2]} ({len(out)} octets)")
    else:
        sys.stdout.write(out)


if __name__ == "__main__":
    main()
