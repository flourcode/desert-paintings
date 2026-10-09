#!/usr/bin/env python3
"""Builds desertpaintings.com into ../site from the files in this folder.

Content lives in paintings.json and photos.json. Images live in paintings/ and photos/,
one full-size file per item, named <slug>.jpg. Replace a file with a new scan or photo
(same name) and rebuild: every size, preview and share image is regenerated.
"""
import json, os, shutil, html, hashlib
from urllib.parse import quote
from datetime import date
from PIL import Image, ImageOps

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.normpath(os.path.join(ROOT, "..", "site"))
SITE = "https://desertpaintings.com"
EMAIL = "mark.flournoy@gmail.com"
CHANNEL = "https://www.youtube.com/@desertpaintings"
TODAY = date.today().isoformat()
SITE_NAME = "Desert Paintings"
TAGLINE = "Watercolors from Palm Springs and the surrounding desert."

def load(name):
    with open(os.path.join(ROOT, name), encoding="utf-8") as f:
        return json.load(f)

PD = load("paintings.json")
P = PD["paintings"]
_by = {p["slug"]: p for p in P}
GRID, HOME = PD["grid"], PD["home"]
for slug in GRID + HOME + [PD["featured"]]:
    if slug not in _by:
        raise SystemExit(f"paintings.json: '{slug}' is listed in grid/home/featured but is not in paintings")
GRID = GRID + [p["slug"] for p in P if p["slug"] not in GRID]   # new paintings not yet placed go at the end
MONTHS = ["January","February","March","April","May","June","July","August","September","October","November","December"]
for i, p in enumerate(P):
    p["no"] = i + 1
    y, m = p["date"].split("-")
    p["date_text"] = f"{MONTHS[int(m)-1]} {y}"
    p["year"] = y
    p["size"] = f"{min(p['w'],p['h'])} × {max(p['w'],p['h'])} in"
    p["orient"] = "land" if p["w"] > p["h"] else "port"
    p["url"] = f"/{p['slug']}/"
    p["file"] = f"{p['slug']}-watercolor"
    p.setdefault("available", True); p.setdefault("note", ""); p.setdefault("video", "")
    p.setdefault("geo", None); p.setdefault("tags", [])
    if not p.get("place"):
        p["place"] = None
for i, slug in enumerate(GRID): _by[slug]["grid"] = i + 1
BY_GRID = sorted(P, key=lambda p: p["grid"])
HOME_LIST = [_by[x] for x in HOME]
FEATURED = _by[PD["featured"]]
FILTERS = [(f["tag"], f["label"]) for f in PD["filters"]]

PHD = load("photos.json")
PHOTOS = PHD["photos"]
SECTIONS = [(s["key"], s["label"]) for s in PHD["sections"]]
for ph in PHOTOS:
    ph.setdefault("place", None)

e = lambda s: html.escape(str(s), quote=True)
pad = lambda n: f"{n:03d}"

def fhash(path):
    with open(path, "rb") as f:
        return hashlib.md5(f.read()).hexdigest()[:8]

def src_image(folder, slug):
    for ext in (".jpg", ".jpeg", ".JPG", ".JPEG", ".png", ".PNG"):
        path = os.path.join(ROOT, folder, slug + ext)
        if os.path.exists(path):
            return ImageOps.exif_transpose(Image.open(path)).convert("RGB")
    raise SystemExit(f"Missing image: source/{folder}/{slug}.jpg")

def desc(p):
    return f"{p['title']}: an original {p['size']} watercolor of {p['subject']}. No. {pad(p['no'])} by Mark, {p['date_text']}. Original available."

# ---------- images ----------
IMG = {}   # file key -> (url with version, width, height)
def save(im, rel, **kw):
    path = os.path.join(OUT, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    im.save(path, **kw)   # saved without EXIF: no GPS or camera data
    return f"/{rel}?v={fhash(path)}"

def build_photos():
    for ph in PHOTOS:
        im = src_image("photos", ph["slug"])
        big = im.copy(); big.thumbnail((4032, 4032), Image.LANCZOS)
        full = f"photos/{ph['slug']}-palm-springs-reference-photo.jpg"
        ph["full"] = save(big, full, quality=90, optimize=True, progressive=True)
        ph["full_plain"] = "/" + full
        t = im.copy(); t.thumbnail((800, 800), Image.LANCZOS)
        ph["thumb"] = save(t, f"photos/{ph['slug']}-800.jpg", quality=82, optimize=True, progressive=True)
        ph["w"], ph["h"] = big.size; ph["tw"], ph["th"] = t.size
        ph["kb"] = os.path.getsize(os.path.join(OUT, full)) // 1024
        ph["orient"] = "land" if big.width > big.height * 1.05 else ("port" if big.height > big.width * 1.05 else "sq")
        if ph["slug"] == PHD.get("og_photo"):
            og = ImageOps.fit(im, (1200, 630), Image.LANCZOS, centering=(0.5, 0.6))
            IMG["og-photos"] = save(og, "images/og/reference-photos.jpg", quality=86, optimize=True)
    IMG.setdefault("og-photos", IMG["og-site"])

def build_images():
    for p in P:
        im = src_image("paintings", p["slug"])
        sizes = [(800, "-800"), (1600, "")] + ([(2400, "-2400")] if max(im.size) >= 2200 else [])
        p["srcset"] = []
        for size, suffix in sizes:
            c = im.copy(); c.thumbnail((size, size), Image.LANCZOS)
            url = save(c, f"images/{p['file']}{suffix}.jpg", quality=84, optimize=True, progressive=True)
            p["srcset"].append((url, c.size[0]))
            if suffix == "":
                p["img"], p["iw"], p["ih"], p["img_plain"] = url, c.size[0], c.size[1], f"/images/{p['file']}.jpg"
        for st in p.get("stages", []):
            sim = src_image("stages", st["image"]); sim.thumbnail((900, 900), Image.LANCZOS)
            st["url"] = save(sim, f"images/stages/{st['image']}.jpg", quality=84, optimize=True, progressive=True)
            st["w"], st["h"] = sim.size
        og = Image.new("RGB", (1200, 630), (250, 249, 246))
        c = im.copy(); c.thumbnail((1080, 560), Image.LANCZOS)
        og.paste(c, ((1200 - c.width) // 2, (630 - c.height) // 2))
        p["og"] = save(og, f"images/og/{p['slug']}.jpg", quality=86, optimize=True)
        if p is FEATURED:
            IMG["og-site"] = save(og, "images/og/desert-paintings.jpg", quality=86, optimize=True)
    IMG["portrait"] = save(Image.open(os.path.join(ROOT, "brand", "mark-round.png")).resize((240, 240), Image.LANCZOS),
                           "images/mark-palm-springs-watercolor-painter.png", optimize=True)
    head = Image.open(os.path.join(ROOT, "brand", "youtube-profile-roadrunner.jpg")).convert("RGB")
    for s, name in ((512, "icon-512.png"), (192, "icon-192.png"), (180, "apple-touch-icon.png"), (48, "favicon-48.png"), (32, "favicon-32.png")):
        head.resize((s, s), Image.LANCZOS).save(os.path.join(OUT, name))
    head.resize((48, 48), Image.LANCZOS).save(os.path.join(OUT, "favicon.ico"), sizes=[(16, 16), (32, 32), (48, 48)])

def img_tag(p, eager=False, sizes="(max-width: 560px) 46vw, (max-width: 900px) 46vw, 30vw"):
    srcset = ", ".join(f"{u} {w}w" for u, w in p["srcset"])
    load_attr = 'fetchpriority="high"' if eager else 'loading="lazy"'
    return (f'<img class="art tonal {p["orient"]}" src="{p["img"]}" srcset="{srcset}" sizes="{sizes}" '
            f'width="{p["iw"]}" height="{p["ih"]}" alt="{e(p["alt"])}, {e(p["size"])} original by Mark" '
            f'{load_attr} decoding="async">')

# ---------- structured data ----------
PERSON = {"@type": "Person", "@id": f"{SITE}/#mark", "name": "Mark", "url": f"{SITE}/about/", "email": f"mailto:{EMAIL}",
          "jobTitle": "Watercolor painter", "image": f"{SITE}/images/mark-palm-springs-watercolor-painter.png", "homeLocation": {"@type": "Place", "name": "Palm Springs, California"},
          "sameAs": [CHANNEL]}
WEBSITE = {"@type": "WebSite", "@id": f"{SITE}/#website", "url": f"{SITE}/", "name": SITE_NAME, "description": TAGLINE,
           "inLanguage": "en-US", "publisher": {"@id": f"{SITE}/#mark"}}
def artwork(p):
    d = {"@type": "VisualArtwork", "@id": f"{SITE}{p['url']}#artwork", "name": p["title"], "url": f"{SITE}{p['url']}",
         "description": desc(p), "image": f"{SITE}/images/{p['file']}.jpg", "artform": "Painting",
         "artMedium": "Watercolor", "artworkSurface": "Watercolor cardstock", "dateCreated": p["date"],
         "width": {"@type": "Distance", "name": f"{p['w']} in"}, "height": {"@type": "Distance", "name": f"{p['h']} in"},
         "creator": {"@id": f"{SITE}/#mark"}, "artEdition": "1", "position": p["no"],
         "keywords": ", ".join(["watercolor", "desert painting", "original art"] + ([p["place"]] if p["geo"] else []))}
    if p["geo"]:
        d["contentLocation"] = {"@type": "Place", "name": p["geo"]}
    return d
def crumbs(items):
    return {"@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": i + 1, "name": n, "item": f"{SITE}{u}"} for i, (n, u) in enumerate(items)]}
def ld(*nodes):
    return '<script type="application/ld+json">' + json.dumps({"@context": "https://schema.org", "@graph": list(nodes)}, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/") + "</script>"

# ---------- page shell ----------
def ver(name):
    return hashlib.md5(open(os.path.join(ROOT, name), "rb").read()).hexdigest()[:8]
ASSET_V = {n: ver(n) for n in ("site.css", "site.js", "analytics.js")}

def page(path, title, description, body, nav="", og_image=None, og_type="website", schema="", alt_og="Watercolor painting by Mark"):
    url = f"{SITE}{path}"
    og_image = og_image or f"{SITE}{IMG['og-site']}"
    current = ' aria-current="page"'
    navlink = lambda key, href, label: f'<a href="{href}"{current if nav == key else ""}>{label}</a>'
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(title)}</title>
<meta name="description" content="{e(description)}">
<link rel="canonical" href="{url}">
<meta name="robots" content="index, follow, max-image-preview:large">
<meta name="author" content="Mark">
<meta property="og:site_name" content="{SITE_NAME}">
<meta property="og:type" content="{og_type}">
<meta property="og:title" content="{e(title)}">
<meta property="og:description" content="{e(description)}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{og_image}">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="{e(alt_og)}">
<meta property="og:locale" content="en_US">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{e(title)}">
<meta name="twitter:description" content="{e(description)}">
<meta name="twitter:image" content="{og_image}">
<meta name="theme-color" content="#faf9f6" media="(prefers-color-scheme: light)">
<meta name="theme-color" content="#151514" media="(prefers-color-scheme: dark)">
<link rel="icon" href="/favicon.ico" sizes="48x48">
<link rel="icon" type="image/png" sizes="32x32" href="/favicon-32.png">
<link rel="apple-touch-icon" href="/apple-touch-icon.png">
<link rel="manifest" href="/site.webmanifest">
<link rel="alternate" type="text/plain" title="LLM summary" href="/llms.txt">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap">
<link rel="stylesheet" href="/assets/site.css?v={ASSET_V['site.css']}">
<script src="/assets/analytics.js?v={ASSET_V['analytics.js']}" defer></script>
<script src="/assets/site.js?v={ASSET_V['site.js']}" defer></script>
{schema}
</head>
<body>
<a class="skip" href="#main">Skip to content</a>
<div class="wrap">
  <header class="site">
    <div class="bar">
      <a class="wordmark" href="/">DESERT PAINTINGS</a>
      <nav class="primary" aria-label="Primary">
        {navlink("paintings", "/paintings/", "Paintings")}
        {navlink("photos", "/reference-photos/", "Reference")}
        {navlink("about", "/about/", "About")}
      </nav>
    </div>
    <div class="dateline meta">Palm Springs, California · Watercolor</div>
  </header>
  <main id="main">
{body}
  </main>
  <footer class="site">
    <div class="bar">
      <span class="label">Desert Paintings</span>
      <span class="meta">Palm Springs, California · {EMAIL} · <a href="{CHANNEL}" rel="me noopener" target="_blank">YouTube @desertpaintings</a> · © 2026 Mark</span>
    </div>
  </footer>
</div>
{VALUE_FILTERS}
</body>
</html>
"""

def card(p):
    return f"""      <a class="card" href="{p['url']}" data-tags="{' '.join(p['tags'])}">
        <div class="frame">{img_tag(p)}</div>
        <div class="cap">
          <span class="no">NO. {pad(p['no'])}</span>
          <span class="title">{e(p['title'])}</span>
          <span class="small">{e(p['size'].replace(' in',''))} watercolor</span>
          <span class="small">{e(p['place']) + ', ' if p['place'] else ''}{p['year']}</span>
        </div>
      </a>"""

def index_section(filters, items=None):
    items = items or BY_GRID
    right = ('<div class="filters" role="group" aria-label="Filter by place">' +
             "".join(f'<button type="button" data-filter="{k}" aria-pressed="{"true" if k=="all" else "false"}">{l}</button>' for k, l in FILTERS) +
             "</div>") if filters else f'<a class="label" href="/paintings/">All {len(P)} paintings →</a>'
    return f"""    <section>
      <div class="sect-head"><span class="label" data-count>{"Index · " + str(len(items)) + " paintings" if filters else "Selected paintings"}</span>{right}</div>
      <div class="index">
{chr(10).join(card(p) for p in items)}
      </div>
    </section>"""

def itemlist():
    return {"@type": "ItemList", "name": "Desert Paintings index", "numberOfItems": len(P),
            "itemListElement": [{"@type": "ListItem", "position": i + 1, "url": f"{SITE}{p['url']}", "name": p["title"]} for i, p in enumerate(BY_GRID)]}

def write(path, content):
    full = os.path.join(OUT, path.lstrip("/"), "index.html") if path.endswith("/") else os.path.join(OUT, path.lstrip("/"))
    os.makedirs(os.path.dirname(full), exist_ok=True)
    open(full, "w").write(content)

BOOKS = [
    dict(title="The Laws Guide to Nature Drawing and Journaling", by="John Muir Laws", pub="Heyday", isbn="9781597143158",
         url="https://heydaybooks.com/?p=14698",
         why="How to look closely at birds, plants and landscapes, and get them down on paper."),
]
CHANNELS = [
    dict(name="Bob Ross", handle="@bobross_thejoyofpainting", url="https://www.youtube.com/@bobross_thejoyofpainting",
         why="The Joy of Painting. Calm, patient, and still the best reminder to keep going."),
    dict(name="@learntopaintwatercolor", handle="", url="https://www.youtube.com/@learntopaintwatercolor",
         why="Watercolor lessons for beginners."),
]
VIDEOS_WATCHED = [
    ("How to Paint with Watercolors: Beginner's Setup and Technique", "With Rajiv Surendra's teacher Marcelo Daldoce", "https://youtu.be/hH10iBvLeXQ"),
    ("Everything You Need to Know About Buying and Using Watercolor Paper", "", "https://youtu.be/n1WL2PxO3A0"),
    ("Our Choices for Watercolor Paints and Palettes", "With Rajiv Surendra and Marcelo Daldoce", "https://youtu.be/Py_kH5DznTs"),
    ("Exploring John Singer Sargent's Watercolor Technique at the Met", "", "https://youtu.be/beKaU1qSv2k"),
]

FAQ = [
    ("Are the original paintings for sale?", f"Yes. Each painting's page says whether the original is available. Write to {EMAIL} to ask about one."),
    ("How are you learning watercolor?", "From books and videos: The Laws Guide to Nature Drawing and Journaling by John Muir Laws (Heyday), Bob Ross, and beginner lessons on YouTube, including videos with Rajiv Surendra and his teacher Marcelo Daldoce."),
    ("Can I paint from your photos?", "Yes. The reference photos page has free photos of Palm Springs skies, mountains, plants and wildlife, dedicated to the public domain (CC0). Download them and use them for anything; credit is appreciated but not required."),
]

VALUE_FILTERS = """<svg width="0" height="0" style="position:absolute" aria-hidden="true" focusable="false">
  <filter id="values3" color-interpolation-filters="sRGB"><feGaussianBlur stdDeviation="1.6"/><feColorMatrix type="saturate" values="0"/>
    <feComponentTransfer><feFuncR type="discrete" tableValues="0.14 0.52 0.93"/><feFuncG type="discrete" tableValues="0.14 0.52 0.93"/><feFuncB type="discrete" tableValues="0.14 0.52 0.93"/></feComponentTransfer></filter>
  <filter id="values5" color-interpolation-filters="sRGB"><feGaussianBlur stdDeviation="1.2"/><feColorMatrix type="saturate" values="0"/>
    <feComponentTransfer><feFuncR type="discrete" tableValues="0.1 0.32 0.54 0.76 0.95"/><feFuncG type="discrete" tableValues="0.1 0.32 0.54 0.76 0.95"/><feFuncB type="discrete" tableValues="0.1 0.32 0.54 0.76 0.95"/></feComponentTransfer></filter>
</svg>"""

def value_switch(scope):
    modes = [("color", "Color"), ("gray", "Grayscale"), ("v3", "3 values"), ("v5", "5 values")]
    btns = "".join(f'<button type="button" data-values="{k}" aria-pressed="{"true" if k == "color" else "false"}">{l}</button>' for k, l in modes)
    return f'<div class="values" role="group" aria-label="Tonal value view for {scope}"><span class="values-label">View</span>{btns}</div>'

def size_text(kb):
    return f"{kb / 1024:.1f} MB" if kb >= 1000 else f"{kb} KB"

def share_links(url, title, media, kind, item):
    pin = ("https://www.pinterest.com/pin/create/button/?url=" + quote(url, safe="") +
           "&media=" + quote(media, safe="") + "&description=" + quote(title, safe=""))
    data = f'data-kind="{kind}" data-id="{e(item)}"'
    return (f'<button type="button" class="share-btn" data-share data-url="{e(url)}" data-title="{e(title)}" {data}>Share</button>'
            f'<span class="sep" aria-hidden="true">·</span>'
            f'<a class="share-btn" href="{e(pin)}" target="_blank" rel="noopener" data-pin {data}>Pin</a>')

def stages_html(p):
    st = p.get("stages") or []
    if not st:
        return ""
    figs = "".join(f"""
          <figure><img class="tonal" src="{x['url']}" width="{x['w']}" height="{x['h']}" alt="{e(p['title'])}, {e(x['label']).lower()}" loading="lazy" decoding="async"><figcaption class="label muted">{e(x['label'])}</figcaption></figure>""" for x in st)
    note = f'<p class="stages-note">{e(p["stages_note"])}</p>' if p.get("stages_note") else ""
    return f"""
        <section class="stages" aria-label="How it was painted"><div class="stages-row">{figs}
        </div>{note}</section>"""

def ref_html(p):
    refs = [ph for ph in PHOTOS if ph.get("painting") == p["slug"]]
    return "".join(f"""
        <figure class="ref"><a href="/reference-photos/#{ph['slug']}"><img class="tonal" src="{ph['thumb']}" width="{ph['tw']}" height="{ph['th']}" alt="Reference photo: {e(ph['alt'])}" loading="lazy" decoding="async"></a>
          <figcaption><span class="label muted">Reference photo</span> <a href="/reference-photos/#{ph['slug']}">{e(ph['title'])}</a> · free to download</figcaption></figure>""" for ph in refs)

def build_pages():
    f = FEATURED
    # home
    body = f"""    <section class="grid hero">
      <div class="hero-text">
        <h1>Desert Paintings</h1>
        <div>
          <p class="lede">Clouds, mountains, and the occasional roadrunner.</p>
        </div>
      </div>
      <figure class="hero-fig">
        <a href="{f['url']}">{img_tag(f, eager=True, sizes="(max-width: 900px) 92vw, 50vw")}</a>
        <figcaption><span><b style="font-weight:600">NO. {pad(f['no'])}</b>&nbsp;&nbsp;{e(f['title'])}</span><span class="muted">{e(f['size'])} · {e(f['date_text'])}</span></figcaption>
      </figure>
    </section>
{index_section(False, HOME_LIST)}"""
    write("/", page("/", "Desert Paintings · Small Watercolors from Palm Springs",
                    "Original small watercolor paintings of Palm Springs and the California desert by Mark: Mount San Jacinto, desert skies, a roadrunner, the Salton Sea. 4×6 and 5×7 originals available.",
                    body, schema=ld(WEBSITE, PERSON, itemlist()), alt_og=FEATURED["alt"]))
    # paintings
    body = f"""    <section class="page-head"><span class="label muted">Paintings</span><h1>The index</h1>
      <p>Each painting is numbered in the order it was made. The originals are small, 4×6 and 5×7, on watercolor cardstock.</p></section>
{index_section(True)}"""
    write("/paintings/", page("/paintings/", "Paintings · Original Desert Watercolors · Desert Paintings",
                              "All twelve original desert watercolors by Mark: Mount San Jacinto, Palm Springs skies, a roadrunner, the Salton Sea, and a few imagined scenes. Small 4×6 and 5×7 originals.",
                              body, nav="paintings",
                              schema=ld({"@type": "CollectionPage", "@id": f"{SITE}/paintings/", "url": f"{SITE}/paintings/", "name": "Paintings", "isPartOf": {"@id": f"{SITE}/#website"}, "mainEntity": itemlist()},
                                        crumbs([("Home", "/"), ("Paintings", "/paintings/")]))))
    # painting pages
    for i, p in enumerate(BY_GRID):
        prev, nxt = (BY_GRID[i - 1] if i else None), (BY_GRID[i + 1] if i + 1 < len(BY_GRID) else None)
        pl = (f'<a href="{prev["url"]}"><span class="label muted">← Previous</span><span class="t">{e(prev["title"])}</span></a>' if prev
              else '<a href="/paintings/"><span class="label muted">← Index</span><span class="t">All paintings</span></a>')
        nl = (f'<a class="next" href="{nxt["url"]}"><span class="label muted">Next →</span><span class="t">{e(nxt["title"])}</span></a>' if nxt
              else '<a class="next" href="/paintings/"><span class="label muted">Index →</span><span class="t">All paintings</span></a>')
        body = f"""    <article class="grid detail">
      <div class="detail-img"><div class="main">{img_tag(p, eager=True, sizes="(max-width: 900px) 92vw, 55vw")}</div>
        {value_switch("this painting")}{stages_html(p)}{ref_html(p)}</div>
      <div class="detail-info">
        <span class="label">Desert Painting No. {pad(p['no'])}</span>
        <h1>{e(p['title'])}</h1>
        <dl class="specs">
          <div><dt>Size</dt><dd>{e(p['size'])}</dd></div>
          <div><dt>Medium</dt><dd>Watercolor on cardstock</dd></div>
          {f"<div><dt>Place</dt><dd>{e(p['place'])}</dd></div>" if p['place'] else ''}
          <div><dt>Painted</dt><dd><time datetime="{p['date']}">{e(p['date_text'])}</time></dd></div>
          <div><dt>Original</dt><dd>{"Available" if p['available'] else "Sold"}</dd></div>
        </dl>
        {f'<p class="story">{e(p["note"])}</p>' if p['note'] else ''}
        {f'<p class="inquire">To ask about this original, write to <span class="email">{EMAIL}</span></p>' if p['available'] else ''}
        {f'<a class="arrow-link" href="{e(p["video"])}" target="_blank" rel="noopener">Watch the painting →</a>' if p['video'] else ''}
        <p class="share-row">{share_links(SITE + p['url'], p['title'] + ', watercolor by Mark · Desert Paintings', SITE + p['img_plain'], 'painting', p['slug'])}</p>
      </div>
    </article>
    <nav class="pager" aria-label="More paintings">
      {pl}
      {nl}
    </nav>"""
        write(p["url"], page(p["url"], p["seo"], desc(p), body, nav="paintings", og_type="article",
                             og_image=SITE + p["og"], alt_og=p["alt"],
                             schema=ld(artwork(p), {"@type": "WebPage", "@id": f"{SITE}{p['url']}", "url": f"{SITE}{p['url']}", "name": p["seo"],
                                                    "isPartOf": {"@id": f"{SITE}/#website"}, "mainEntity": {"@id": f"{SITE}{p['url']}#artwork"},
                                                    "primaryImageOfPage": f"{SITE}/images/{p['file']}.jpg"},
                                       crumbs([("Home", "/"), ("Paintings", "/paintings/"), (p["title"], p["url"])]))))
    # reference photos
    CC0 = "https://creativecommons.org/publicdomain/zero/1.0/"
    by_slug = {p["slug"]: p for p in P}
    def photo_card(ph):
        used = by_slug.get(ph.get("painting"))
        place = f'<span class="small">{e(ph["place"])}</span>' if ph["place"] else ""
        used_html = f'<a class="small used" href="{used["url"]}">Painted as {e(used["title"])} →</a>' if used else ""
        return f"""        <figure class="card photo" id="{ph['slug']}">
          <a class="frame" href="{ph['full']}" aria-label="Open full-size photo: {e(ph['title'])}"><img class="art tonal {ph['orient']}" src="{ph['thumb']}" width="{ph['tw']}" height="{ph['th']}" alt="{e(ph['alt'])}" loading="lazy" decoding="async"></a>
          <figcaption class="cap">
            <span class="title">{e(ph['title'])}</span>
            {place}
            {used_html}
            <span class="actions"><a class="dl" href="{ph['full']}" download>Download <span class="meta">{ph['w']}×{ph['h']} · {size_text(ph['kb'])}</span></a>
            {share_links(SITE + '/reference-photos/#' + ph['slug'], ph['title'] + ', free reference photo · Desert Paintings', SITE + ph['full_plain'], 'photo', ph['slug'])}</span>
          </figcaption>
        </figure>"""
    secs = []
    for key, label in SECTIONS:
        items = [ph for ph in PHOTOS if ph["sec"] == key]
        secs.append(f"""    <section class="photo-sec" id="{key}">
      <div class="sect-head"><h2 class="label">{e(label)} · {len(items)}</h2></div>
      <div class="index photos">
{chr(10).join(photo_card(ph) for ph in items)}
      </div>
    </section>""")
    jump = " ".join(f'<a href="#{k}">{e(l)}</a>' for k, l in SECTIONS)
    body = f"""    <section class="page-head"><span class="label muted">Reference photos</span><h1>Free to paint from</h1>
      <p>Photos I've taken around Palm Springs, mostly for painting. Some became paintings, most are still waiting. Download any of them and use them for anything. Credit is appreciated but not required.</p>
      <p class="license"><a class="arrow-link" href="{CC0}" target="_blank" rel="license noopener">CC0 · Public domain</a></p>
      <nav class="jump" aria-label="Photo sections">{jump}</nav>
      <div class="values-intro">{value_switch("all photos")}<p class="values-note">See each photo as light and dark only. A 3- or 5-value study is a quick way to plan a painting before reaching for color.</p></div>
    </section>
{chr(10).join(secs)}"""
    photo_nodes = [{"@type": "ImageObject", "contentUrl": f"{SITE}{ph['full']}", "thumbnailUrl": f"{SITE}{ph['thumb']}", "name": ph["title"],
                    "description": ph["alt"], "width": ph["w"], "height": ph["h"], "license": CC0,
                    "acquireLicensePage": f"{SITE}/reference-photos/", "creditText": "Mark, Desert Paintings",
                    "copyrightNotice": "Dedicated to the public domain (CC0)", "creator": {"@id": f"{SITE}/#mark"},
                    **({"contentLocation": {"@type": "Place", "name": ph["place"] + ", California"}} if ph["place"] else {})} for ph in PHOTOS]
    write("/reference-photos/", page("/reference-photos/", "Free Reference Photos for Painting · Palm Springs & Desert · Desert Paintings",
                                     f"{len(PHOTOS)} free CC0 reference photos for watercolor painters: Palm Springs sunsets, clouds, Mount San Jacinto, palms, Joshua trees, cactus and roadrunners. Download full size, no sign-up.",
                                     body, nav="photos", og_image=f"{SITE}{IMG['og-photos']}", alt_og="Palm Springs sunset reference photo",
                                     schema=ld({"@type": "CollectionPage", "@id": f"{SITE}/reference-photos/", "url": f"{SITE}/reference-photos/", "name": "Free reference photos",
                                                "isPartOf": {"@id": f"{SITE}/#website"}, "license": CC0, "hasPart": photo_nodes},
                                               crumbs([("Home", "/"), ("Reference photos", "/reference-photos/")]))))
    # videos
    body = f"""    <section class="page-head"><span class="label muted">Videos</span><h1>Painting on camera</h1>
      <p>Videos of these paintings, start to finish, are coming to YouTube.</p></section>
    <section class="vlist"><div class="vrow" style="grid-template-columns:1fr">
      <a class="arrow-link" href="{CHANNEL}" target="_blank" rel="noopener" style="justify-self:start;font-size:20px">YouTube · @desertpaintings →</a>
    </div></section>"""
    write("/videos/", page("/videos/", "Videos · Watercolor Painting on YouTube · Desert Paintings",
                           "Watch Mark paint small desert watercolors of Palm Springs and the San Jacinto Mountains on YouTube at @desertpaintings.",
                           body, nav="videos", schema=ld(crumbs([("Home", "/"), ("Videos", "/videos/")]))))
    # about + FAQ
    books = "\n".join(f'            <li><a href="{b["url"]}" target="_blank" rel="noopener"><cite>{e(b["title"])}</cite></a><span class="by">{e(b["by"])} · {e(b["pub"])}</span><span class="why">{e(b["why"])}</span></li>' for b in BOOKS)
    by_html = lambda t: f'<span class="by">{e(t)}</span>' if t else ""
    chans = "\n".join(f'            <li><a href="{c["url"]}" target="_blank" rel="noopener">{e(c["name"])}</a>{by_html(c["handle"])}<span class="why">{e(c["why"])}</span></li>' for c in CHANNELS)
    vids = "\n".join(f'            <li><a href="{u}" target="_blank" rel="noopener">{e(t)}</a>{by_html(w)}</li>' for t, w, u in VIDEOS_WATCHED)
    faq_html = "\n".join(f"        <dt>{e(q)}</dt><dd>{e(a)}</dd>" for q, a in FAQ)
    body = f"""    <section class="page-head"><span class="label muted">About</span><h1>Mark, Palm Springs</h1></section>
    <section class="grid about">
      <p class="statement">Hi, I'm Mark. I recently retired and moved back to Southern California. I'm avoiding pickleball, so I decided to try painting again after about a 50-year break.</p>
      <div class="body">
        <p>I live at the base of the San Jacinto Mountains, so there's plenty of inspiration. I'm not good enough to paint portraits, so I mostly paint mountains, clouds and roadrunners. I'm hoping to get a good picture of a coyote this fall.</p>
        <p>Most of what I paint comes from a photo I took, or my memory of taking it. About half my photo library seems to be clouds. They never look the way they did when I took them, but painting helps bring a little of that feeling back.</p>
        <p>My first love is sketching, so I usually start with a pencil sketch on dry paper, then do a big wash and start painting. The watercolors don't seem to care about my lines, though. I use basic watercolors and a few brushes, flats and large rounds between half an inch and an inch. I paint wet on wet, let the paper dry, then do some glazing. Still working on that.</p>
        <p>If nothing else, it's 30 minutes of zen.</p>
        <p>Hope you enjoy <a class="inline" href="/paintings/">the paintings</a>. Feel free to use anything in my <a class="inline" href="/reference-photos/">reference library</a> for your own work. I'll try to keep it updated.</p>
        <p>If you have suggestions for what I should paint next, <a class="inline" href="mailto:{EMAIL}?subject=Something%20to%20paint">let me know</a>. Just as long as it's clouds and mountains. :)</p>
      </div>
      <aside>
        <img class="portrait" src="{IMG['portrait']}" width="240" height="240" alt="Mark, watercolor painter in Palm Springs, in front of an Audubon bird print">
        <div class="sect-head" style="margin-bottom:12px"><span class="label">Contact</span></div>
        <div class="contact-line"><span class="email" id="email">{EMAIL}</span><button type="button" class="copy" id="copy-email">Copy</button></div>
        <div class="sect-head" style="margin:32px 0 12px"><span class="label">Elsewhere</span></div>
        <a class="arrow-link" href="{CHANNEL}" target="_blank" rel="me noopener">YouTube · @desertpaintings →</a>
      </aside>
    </section>
    <section class="learning">
      <div class="sect-head"><span class="label">What I'm learning from</span></div>
      <div class="learn-grid">
        <div>
          <h2 class="learn-h">Books</h2>
          <ul class="learn-list">
{books}
          </ul>
        </div>
        <div>
          <h2 class="learn-h">YouTube channels</h2>
          <ul class="learn-list">
{chans}
          </ul>
          <h2 class="learn-h" style="margin-top:36px">Videos worth watching</h2>
          <ul class="learn-list">
{vids}
          </ul>
        </div>
      </div>
    </section>
    <section class="faq">
      <div class="sect-head"><span class="label">Questions</span></div>
      <dl>
{faq_html}
      </dl>
    </section>"""
    write("/about/", page("/about/", "About Mark · Watercolor Painter in Palm Springs · Desert Paintings",
                          "Mark is a watercolor painter in Palm Springs, California. He paints small 4×6 and 5×7 scenes of Mount San Jacinto, desert skies, windmills, roadrunners and the Salton Sea.",
                          body, nav="about",
                          schema=ld(dict(PERSON, description="Watercolor painter in Palm Springs, California, painting small desert scenes."),
                                    {"@type": "AboutPage", "@id": f"{SITE}/about/", "url": f"{SITE}/about/", "name": "About Mark", "mainEntity": {"@id": f"{SITE}/#mark"}},
                                    {"@type": "ItemList", "name": "Books Mark is learning watercolor from", "itemListElement": [
                                        {"@type": "ListItem", "position": i + 1, "item": {"@type": "Book", "name": b["title"], "author": {"@type": "Person", "name": b["by"]}, "publisher": {"@type": "Organization", "name": b["pub"]}, "isbn": b["isbn"], "url": b["url"]}} for i, b in enumerate(BOOKS)]},
                                    {"@type": "FAQPage", "mainEntity": [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in FAQ]},
                                    crumbs([("Home", "/"), ("About", "/about/")]))))
    # 404
    body = """    <section class="page-head"><span class="label muted">404</span><h1>Not here</h1>
      <p>That page doesn't exist. The paintings are all in the <a class="arrow-link" href="/paintings/">index</a>.</p></section>"""
    html404 = page("/404.html", "Page not found · Desert Paintings", "This page could not be found.", body).replace(
        '<meta name="robots" content="index, follow, max-image-preview:large">', '<meta name="robots" content="noindex">')
    write("/404.html", html404)

# ---------- supporting files ----------
def build_files():
    os.makedirs(f"{OUT}/assets", exist_ok=True)
    shutil.copy(os.path.join(ROOT, "site.css"), f"{OUT}/assets/site.css")
    shutil.copy(os.path.join(ROOT, "site.js"), f"{OUT}/assets/site.js")
    shutil.copy(os.path.join(ROOT, "analytics.js"), f"{OUT}/assets/analytics.js")
    # sitemap with images
    urls = [("/", 1.0, None), ("/paintings/", 0.9, None)] + [(p["url"], 0.8, p) for p in BY_GRID] + [("/reference-photos/", 0.7, "photos"), ("/about/", 0.6, None)]
    out = ['<?xml version="1.0" encoding="UTF-8"?>',
           '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">']
    for u, pr, p in urls:
        out.append(f"  <url><loc>{SITE}{u}</loc><lastmod>{TODAY}</lastmod><priority>{pr}</priority>" +
                   ("".join(f"<image:image><image:loc>{SITE}{ph['full']}</image:loc></image:image>" for ph in PHOTOS) if p == "photos"
                    else f"<image:image><image:loc>{SITE}/images/{p['file']}.jpg</image:loc></image:image>" if p else "") + "</url>")
    out.append("</urlset>")
    open(f"{OUT}/sitemap.xml", "w").write("\n".join(out) + "\n")
    open(f"{OUT}/robots.txt", "w").write(f"""# desertpaintings.com
User-agent: *
Allow: /
Disallow: /404.html

# AI search and answer engines are welcome
User-agent: GPTBot
Allow: /
User-agent: OAI-SearchBot
Allow: /
User-agent: ChatGPT-User
Allow: /
User-agent: ClaudeBot
Allow: /
User-agent: Claude-SearchBot
Allow: /
User-agent: PerplexityBot
Allow: /
User-agent: Google-Extended
Allow: /
User-agent: Applebot-Extended
Allow: /

Sitemap: {SITE}/sitemap.xml
""")
    lines = [f"# {SITE_NAME}", "", f"> {TAGLINE} Original 4×6 and 5×7 watercolors by Mark, a painter in Palm Springs, California. All originals are currently available; inquiries go to {EMAIL}.", "",
             "## Pages", "", f"- [Home]({SITE}/): featured painting and the full index",
             f"- [Paintings]({SITE}/paintings/): all paintings, numbered in the order they were made",
             f"- [Reference photos]({SITE}/reference-photos/): free CC0 photos of Palm Springs skies, mountains, plants and wildlife for painters to download and use",
             f"- [About]({SITE}/about/): about Mark, contact, and common questions",
             "", "## Paintings", ""]
    for p in sorted(P, key=lambda p: p["no"]):
        lines.append(f"- [No. {pad(p['no'])} {p['title']}]({SITE}{p['url']}): {p['size']} watercolor on cardstock, {(p['place'] + ', ') if p['place'] else ''}{p['date_text']}. Original available.")
    lines += ["", "## What Mark is learning from", ""] + [f"- Book: {b['title']} by {b['by']} ({b['pub']})" for b in BOOKS] + [f"- YouTube: {c['name']} ({c['url']})" for c in CHANNELS]
    lines += ["", "## Contact", "", f"- Email: {EMAIL}", f"- YouTube: {CHANNEL}", ""]
    open(f"{OUT}/llms.txt", "w").write("\n".join(lines))
    open(f"{OUT}/site.webmanifest", "w").write(json.dumps({
        "name": SITE_NAME, "short_name": SITE_NAME, "start_url": "/", "display": "browser",
        "background_color": "#faf9f6", "theme_color": "#faf9f6",
        "icons": [{"src": "/icon-192.png", "sizes": "192x192", "type": "image/png"}, {"src": "/icon-512.png", "sizes": "512x512", "type": "image/png"}]}, indent=2))
    open(f"{OUT}/humans.txt", "w").write(f"Paintings: Mark, Palm Springs, California\nContact: {EMAIL}\nYouTube: {CHANNEL}\nType: Inter\n")

if __name__ == "__main__":
    if os.path.exists(OUT): shutil.rmtree(OUT)
    os.makedirs(OUT)
    build_images(); build_photos(); build_pages(); build_files()
    print("built", OUT)
