/* ============================================================
   ANNOTATIONS — logique partagée par toutes les fiches
   Chargée via : <script src="../Config/annotations.js" defer></script>
   (le CSS est dans Config/annotations.css)

   - Surligner : sélectionner du texte → mini-barre → couleur.
   - Note : cliquer sur un surlignage → éditer (Entrée = valider,
            Maj+Entrée = saut de ligne). Affichée en marge droite si place.
   - Sauvegarde : localStorage, par fiche, dans CE navigateur.

   Clé de stockage : <body data-annot-key="…"> si défini, sinon déduite du
   nom de fichier. Version : <body data-annot-version="N"> (défaut "1") —
   l'incrémenter quand le contenu d'une fiche est régénéré pour invalider
   les annotations devenues obsolètes.
   ============================================================ */
(function(){
  function init(){
    var page = document.querySelector('.page');
    if(!page || !window.localStorage) return;

    var body = document.body;
    var KEY = body.dataset.annotKey || ('annot_' + (location.pathname.split('/').pop() || 'fiche'));
    var CONTENT_VERSION = body.dataset.annotVersion || '1';

    /* ---- Injection de l'UI ---- */
    var ui = document.createElement('div');
    ui.innerHTML =
      '<div id="annot-bar">' +
        '<button class="sw sw-yellow" data-color="yellow" title="Surligner jaune"></button>' +
        '<button class="sw sw-green" data-color="green" title="Surligner vert"></button>' +
        '<button class="sw sw-blue" data-color="blue" title="Surligner cyan"></button>' +
        '<button class="sw sw-pink" data-color="pink" title="Surligner rose"></button>' +
        '<button class="sw sw-orange" data-color="orange" title="Surligner orange"></button>' +
        '<button class="sw sw-underline" data-color="underline" title="Souligner en rouge"></button>' +
      '</div>' +
      '<div id="annot-pop">' +
        '<textarea placeholder="Ta note…"></textarea>' +
        '<div class="pop-actions">' +
          '<button class="annot-del">Supprimer</button>' +
          '<button class="annot-save">Enregistrer</button>' +
        '</div>' +
      '</div>' +
      '<button id="annot-clear" title="Efface tous les surlignages et notes de cette fiche">Effacer mes annotations</button>' +
      '<div id="annot-margin"></div>';
    while(ui.firstChild) body.appendChild(ui.firstChild);

    var bar = document.getElementById('annot-bar');
    var pop = document.getElementById('annot-pop');
    var clearBtn = document.getElementById('annot-clear');
    var marginBox = document.getElementById('annot-margin');
    var ta = pop.querySelector('textarea');

    var currentRange = null;
    var activeAid = null;

    /* ---- Persistance ---- */
    function save(){
      try{ localStorage.setItem(KEY, JSON.stringify({v:CONTENT_VERSION, html:page.innerHTML})); }catch(e){}
      renderMargin();
    }
    function restore(){
      try{
        var raw = localStorage.getItem(KEY);
        if(raw){
          var data = JSON.parse(raw);
          if(data && data.v === CONTENT_VERSION && data.html){ page.innerHTML = data.html; }
        }
      }catch(e){}
      renderMargin();
    }

    /* ---- Notes en marge droite ---- */
    function renderMargin(){
      marginBox.innerHTML = '';
      var prect = page.getBoundingClientRect();
      var avail = document.documentElement.clientWidth - prect.right;
      if(avail < 235){ marginBox.style.display = 'none'; return; }
      marginBox.style.display = 'block';
      var left = prect.right + window.pageXOffset + 16;
      var cards = [];
      page.querySelectorAll('.annot-hl.has-note').forEach(function(span){
        if(!span.dataset.note) return;
        var r = span.getBoundingClientRect();
        cards.push({center:r.top + r.height/2 + window.pageYOffset, note:span.dataset.note, color:span.dataset.color, aid:span.dataset.aid});
      });
      cards.sort(function(a,b){ return a.center - b.center; });
      var lastBottom = -Infinity;
      cards.forEach(function(c){
        var el = document.createElement('div');
        el.className = 'annot-margin-card';
        el.dataset.color = c.color;
        el.dataset.aid = c.aid;
        el.textContent = c.note;
        el.style.left = left + 'px';
        el.style.visibility = 'hidden';
        marginBox.appendChild(el);                          // ajout d'abord pour mesurer la hauteur
        // centrer la carte sur le surlignage, sinon empiler sous la précédente (anti-chevauchement)
        var top = Math.max(c.center - el.offsetHeight/2, lastBottom + 8);
        if(top < 0) top = 0;
        el.style.top = top + 'px';
        el.style.visibility = '';
        lastBottom = top + el.offsetHeight;
      });
    }
    marginBox.addEventListener('click', function(e){
      var card = e.target.closest('.annot-margin-card');
      if(card){ openNote(card.dataset.aid); }
    });
    var rzTimer;
    window.addEventListener('resize', function(){ clearTimeout(rzTimer); rzTimer = setTimeout(renderMargin, 120); });

    /* ---- Surlignage ---- */
    function newAid(){ return 'a' + Date.now().toString(36) + Math.random().toString(36).slice(2,5); }

    function highlightRange(range, color){
      var aid = newAid();
      var walker = document.createTreeWalker(page, NodeFilter.SHOW_TEXT, {
        acceptNode: function(node){
          if(!node.nodeValue.trim()) return NodeFilter.FILTER_REJECT;
          if(node.parentElement && node.parentElement.closest('.annot-hl')) return NodeFilter.FILTER_REJECT;
          if(!range.intersectsNode(node)) return NodeFilter.FILTER_REJECT;
          return NodeFilter.FILTER_ACCEPT;
        }
      });
      var nodes = [];
      while(walker.nextNode()) nodes.push(walker.currentNode);
      var spans = [];
      nodes.forEach(function(node){
        var start = 0, end = node.nodeValue.length;
        if(node === range.startContainer) start = range.startOffset;
        if(node === range.endContainer) end = range.endOffset;
        if(start >= end) return;
        var r = document.createRange();
        r.setStart(node, start); r.setEnd(node, end);
        var span = document.createElement('span');
        span.className = 'annot-hl';
        span.dataset.color = color;
        span.dataset.aid = aid;
        try{ r.surroundContents(span); spans.push(span); }catch(e){}
      });
      return spans.length ? aid : null;
    }

    function unwrapAid(aid){
      page.querySelectorAll('.annot-hl[data-aid="'+aid+'"]').forEach(function(span){
        var parent = span.parentNode;
        while(span.firstChild) parent.insertBefore(span.firstChild, span);
        parent.removeChild(span);
        parent.normalize();
      });
    }

    /* ---- Barre flottante ---- */
    function showBar(rect){
      bar.style.display = 'flex';
      var bw = bar.offsetWidth, bh = bar.offsetHeight;
      var top = rect.top - bh - 8;
      if(top < 8) top = rect.bottom + 8;
      var left = rect.left + rect.width/2 - bw/2;
      left = Math.max(8, Math.min(left, window.innerWidth - bw - 8));
      bar.style.top = top + 'px';
      bar.style.left = left + 'px';
    }
    function hideBar(){ bar.style.display = 'none'; }

    document.addEventListener('mouseup', function(e){
      if(e.target.closest('#annot-bar') || e.target.closest('#annot-pop')) return;
      setTimeout(function(){
        var sel = window.getSelection();
        if(!sel || sel.isCollapsed || !sel.rangeCount){ hideBar(); return; }
        var range = sel.getRangeAt(0);
        if(!page.contains(range.commonAncestorContainer)){ hideBar(); return; }
        currentRange = range.cloneRange();
        showBar(range.getBoundingClientRect());
      }, 10);
    });

    bar.addEventListener('mousedown', function(e){ e.preventDefault(); });
    bar.addEventListener('click', function(e){
      var btn = e.target.closest('button');
      if(!btn || !currentRange) return;
      highlightRange(currentRange, btn.dataset.color);
      window.getSelection().removeAllRanges();
      hideBar();
      save();
    });

    /* ---- Notes ---- */
    function openNote(aid){
      activeAid = aid;
      var spans = page.querySelectorAll('.annot-hl[data-aid="'+aid+'"]');
      if(!spans.length) return;
      ta.value = spans[0].dataset.note || '';
      var rect = spans[0].getBoundingClientRect();
      pop.style.display = 'block';
      var pw = pop.offsetWidth, ph = pop.offsetHeight;
      var top = rect.bottom + 8;
      if(top + ph > window.innerHeight - 8) top = Math.max(8, rect.top - ph - 8);
      var left = Math.max(8, Math.min(rect.left, window.innerWidth - pw - 8));
      pop.style.top = top + 'px';
      pop.style.left = left + 'px';
      ta.focus();
    }
    function closePop(){ pop.style.display = 'none'; activeAid = null; }

    page.addEventListener('click', function(e){
      var hl = e.target.closest('.annot-hl');
      if(hl){ e.stopPropagation(); openNote(hl.dataset.aid); }
    });

    ta.addEventListener('keydown', function(e){
      if(e.key === 'Enter' && !e.shiftKey){ e.preventDefault(); pop.querySelector('.annot-save').click(); }
    });
    pop.querySelector('.annot-save').addEventListener('click', function(){
      if(!activeAid) return;
      var spans = page.querySelectorAll('.annot-hl[data-aid="'+activeAid+'"]');
      var txt = ta.value.trim();
      spans.forEach(function(s){
        if(txt) s.dataset.note = txt; else delete s.dataset.note;
        s.classList.remove('has-note');
      });
      if(txt && spans.length) spans[spans.length-1].classList.add('has-note');
      save(); closePop();
    });
    pop.querySelector('.annot-del').addEventListener('click', function(){
      if(!activeAid) return;
      unwrapAid(activeAid);
      save(); closePop();
    });

    document.addEventListener('mousedown', function(e){
      if(!e.target.closest('#annot-pop') && !e.target.closest('.annot-hl')) closePop();
    });

    clearBtn.addEventListener('click', function(){
      if(!confirm('Effacer tous les surlignages et notes de cette fiche ?')) return;
      page.querySelectorAll('.annot-hl').forEach(function(span){
        var parent = span.parentNode;
        while(span.firstChild) parent.insertBefore(span.firstChild, span);
        parent.removeChild(span);
      });
      page.normalize();
      save(); closePop(); hideBar();
    });

    /* ---- Init ---- */
    restore();
  }

  if(document.readyState === 'loading'){ document.addEventListener('DOMContentLoaded', init); }
  else { init(); }
})();
