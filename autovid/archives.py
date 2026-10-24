"""Recherche automatique d'images et de vidéos d'archives LIBRES (domaine public ou licence Creative Commons).

Sources (toutes gratuites, sans clé) :
  - Wikimedia Commons (photos, documents, coupures de presse anciennes)
  - Library of Congress (photos « No known restrictions »)
  - Openverse (agrégateur d'images sous licence CC)
  - Internet Archive (films du domaine public, collection Prelinger)
  - Pexels et Pixabay (plans d'ambiance) si les clés gratuites PEXELS_API_KEY / PIXABAY_API_KEY sont définies
Les photos de l'Agência Brasil (CC BY 4.0) et de l'Arquivo Nacional sont en grande partie sur Wikimedia Commons :
la recherche Commons les trouve (leurs propres sites bloquent les robots).
Chaque média gardé est noté avec son auteur, sa licence et sa page : `credits.json`, puis le générique de fin.
Les licences « NC » (pas d'usage commercial) et « ND » (pas de modification) sont refusées : une chaîne monétisée
fait un usage commercial, et le zoom / recadrage est une modification.
"""
import hashlib
import json
import re
from pathlib import Path

UA = "AutoVid-Documentaire/1.0 (https://github.com/youtubevieira/autovid-ai; montage video educatif)"
# jamais de corps, de scène de crime, d'autopsie : YouTube démonétise, et c'est irrespectueux pour les familles
INTERDIT = re.compile(r"(corpse|cadav|dead body|bodies|autopsy|morgue|crime scene photo|gore|blood|murdered body|"
                      r"cadavre|scène de crime|autopsie|sang)", re.I)


def _get(url, params=None, timeout=(10, 20), tries=3):
    """GET poli : respecte « Retry-After » quand un site limite le débit (Wikimedia renvoie souvent 429)."""
    import time

    import requests
    for k in range(tries):
        r = requests.get(url, params=params, timeout=timeout, headers={"User-Agent": UA})
        if r.status_code in (429, 503) and k + 1 < tries:
            time.sleep(min(float(r.headers.get("Retry-After") or 5 * (k + 1)), 30))
            continue
        r.raise_for_status()
        return r


def licence_ok(text):
    """Domaine public, CC0, CC BY, CC BY-SA : oui. NC, ND, « tous droits réservés », inconnue : non."""
    t = (text or "").lower()
    if t in ("pexels license", "pixabay content license"):   # licences maison : usage commercial et montage permis
        return True
    if re.search(r"public domain|domaine public|cc0|\bpdm\b|no known restrictions", t):
        return True
    if re.search(r"\bnc\b|-nc|noncommercial|non-commercial|\bnd\b|-nd|noderiv|all rights reserved|fair use", t):
        return False
    return bool(re.search(r"cc[- ]?by|attribution", t))


GENERIQUES = {"street", "streets", "photo", "photograph", "image", "picture", "view", "old", "vintage", "people",
              "scene", "historic", "historical", "black", "white", "the", "and", "with", "from", "rue", "foto"}
RECORDS = re.compile(r"\breel\b|written records|microfilm|catalog card|negative sleeve|\bpage \d+", re.I)


def _norm(t):
    import unicodedata
    return unicodedata.normalize("NFKD", t or "").encode("ascii", "ignore").decode().lower()


def pertinence(query, c):
    """L'image correspond-elle à la recherche ? Mots importants présents dans le titre / la description, époque
    proche (±3 ans) quand une année est demandée et connue. Mieux vaut un plan neutre qu'une image fausse."""
    q = _norm(query)
    text = _norm(f"{c.get('titre', '')} {c.get('description', '')} {c.get('date', '')}")
    if RECORDS.search(text) and not RECORDS.search(q):
        return False
    words = [w for w in re.findall(r"[a-z]{4,}", q) if w not in GENERIQUES]
    if words:
        hits = sum(1 for w in words if re.search(rf"\b{w[:-1] if len(w) > 5 else w}", text))
        if hits < (len(words) if len(words) <= 2 else -(-2 * len(words) // 3)):
            return False
    years_q = [int(y) for y in re.findall(r"\b(1[5-9]\d\d|20[0-2]\d)\b", q)]
    decade = re.search(r"\b(1[5-9]\d|20[0-2])0s\b", q)
    years_c = [int(y) for y in re.findall(r"\b(1[5-9]\d\d|20[0-2]\d)\b", text)]
    if years_c and (years_q or decade):
        lo, hi = (years_q[0] - 3, years_q[0] + 3) if years_q else (int(decade.group(1)) * 10, int(decade.group(1)) * 10 + 9)
        if not any(lo <= y <= hi for y in years_c):
            return False
    return True


def _clean(html):
    return re.sub(r"<[^>]+>", "", html or "").strip()


# --------------------------------------------------------------------------- moteurs de recherche

def commons(query, n=8):
    data = _get("https://commons.wikimedia.org/w/api.php", {
        "action": "query", "format": "json", "generator": "search", "gsrsearch": f"{query} filetype:bitmap",
        "gsrnamespace": 6, "gsrlimit": n, "prop": "imageinfo", "iiprop": "url|extmetadata|mime|size",
        "iiurlwidth": 1920}).json()   # taille de vignette standard : moins limitée par Wikimedia
    out = []
    for page in (data.get("query", {}).get("pages") or {}).values():
        ii = (page.get("imageinfo") or [{}])[0]
        meta = ii.get("extmetadata") or {}
        lic = _clean(meta.get("LicenseShortName", {}).get("value"))
        out.append({"source": "Wikimedia Commons", "titre": page.get("title", "").replace("File:", ""),
                    "url": ii.get("thumburl") or ii.get("url"), "page": ii.get("descriptionurl"),
                    "auteur": _clean(meta.get("Artist", {}).get("value"))[:120] or "inconnu", "licence": lic,
                    "largeur": ii.get("thumbwidth") or ii.get("width", 0), "type": "image",
                    "description": _clean(meta.get("ImageDescription", {}).get("value"))[:300],
                    "date": _clean(meta.get("DateTimeOriginal", {}).get("value"))[:40]})
    return out


def loc(query, n=8):
    data = _get("https://www.loc.gov/photos/", {"q": query, "fo": "json", "c": n}).json()
    out = []
    for it in data.get("results", []):
        # les droits sont dans « item.rights_advisory » ; on prend la plus grande image JPEG proposée
        imgs = [u.split("#")[0] for u in it.get("image_url") or [] if ".jpg" in u.split("#")[0]]
        ra = (it.get("item") or {}).get("rights_advisory") or it.get("rights_advisory") or ""
        rights = " ".join(ra) if isinstance(ra, list) else str(ra)
        if not imgs:
            continue
        out.append({"source": "Library of Congress", "titre": it.get("title", ""), "url": imgs[-1],
                    "page": it.get("url") or it.get("id"), "auteur": ", ".join(it.get("contributor") or [])[:120] or "LOC",
                    "licence": rights or "inconnue", "largeur": 1200, "type": "image",
                    "description": " ".join(it.get("description") or [])[:300], "date": str(it.get("date") or "")})
    return out


def openverse(query, n=8):
    data = _get("https://api.openverse.org/v1/images/", {"q": query, "page_size": n,
                                                         "license_type": "commercial,modification"}).json()
    return [{"source": f"Openverse ({r.get('provider', '?')})", "titre": r.get("title") or "", "url": r.get("url"),
             "page": r.get("foreign_landing_url"), "auteur": r.get("creator") or "inconnu",
             "licence": f"{r.get('license', '')} {r.get('license_version', '')}".strip().upper().replace("BY", "CC BY")
             if r.get("license") not in ("cc0", "pdm") else "Public domain",
             "largeur": r.get("width") or 0, "type": "image", "description": ""} for r in data.get("results", [])]


def archive_films(query, n=5):
    q = f"({query}) AND mediatype:movies AND (licenseurl:*publicdomain* OR collection:prelinger)"
    data = _get("https://archive.org/advancedsearch.php", {"q": q, "fl[]": ["identifier", "title", "licenseurl"],
                                                           "rows": n, "output": "json"}).json()
    out = []
    for d in data.get("response", {}).get("docs", []):
        meta = _get(f"https://archive.org/metadata/{d['identifier']}").json()
        mp4 = next((f["name"] for f in meta.get("files", []) if f.get("name", "").endswith(".mp4")), None)
        if mp4:
            out.append({"source": "Internet Archive", "titre": d.get("title", ""), "type": "video",
                        "url": f"https://archive.org/download/{d['identifier']}/{mp4}",
                        "page": f"https://archive.org/details/{d['identifier']}", "auteur": "Internet Archive",
                        "licence": d.get("licenseurl") or "Public domain (Prelinger)", "largeur": 640, "description": ""})
    return out


def pexels(query, n=6):
    """Pexels (clé gratuite PEXELS_API_KEY) : photos et vidéos d'ambiance, licence Pexels (usage commercial permis)."""
    import os
    key = os.environ.get("PEXELS_API_KEY")
    if not key:
        return []
    import requests
    r = requests.get("https://api.pexels.com/v1/search", params={"query": query, "per_page": n},
                     headers={"Authorization": key, "User-Agent": UA}, timeout=25)
    r.raise_for_status()
    return [{"source": "Pexels", "titre": ph.get("alt") or query, "url": ph["src"]["large2x"], "page": ph["url"],
             "auteur": ph.get("photographer") or "Pexels", "licence": "Pexels License", "largeur": ph.get("width", 0),
             "type": "image", "description": ""} for ph in r.json().get("photos", [])]


def pixabay(query, n=6):
    """Pixabay (clé gratuite PIXABAY_API_KEY) : licence Pixabay (usage commercial permis, sans attribution exigée)."""
    import os
    key = os.environ.get("PIXABAY_API_KEY")
    if not key:
        return []
    data = _get("https://pixabay.com/api/", {"key": key, "q": query, "per_page": max(n, 3), "safesearch": "true"}).json()
    return [{"source": "Pixabay", "titre": h.get("tags") or query, "url": h.get("largeImageURL"), "page": h.get("pageURL"),
             "auteur": h.get("user") or "Pixabay", "licence": "Pixabay Content License", "largeur": h.get("imageWidth", 0),
             "type": "image", "description": ""} for h in data.get("hits", [])]


MOTEURS = {"commons": commons, "loc": loc, "openverse": openverse, "pexels": pexels, "pixabay": pixabay}


# --------------------------------------------------------------------------- sélection + téléchargement

class Archives:
    """Cherche, filtre (licence, contenu interdit, déjà utilisé), télécharge et tient les crédits."""

    def __init__(self, dossier, local=None, video=True, verifier=None):
        self.dir = Path(dossier)
        self.dir.mkdir(parents=True, exist_ok=True)
        self.credits, self.used, self.errors = [], set(), set()
        self.local = sorted(p for p in Path(local).iterdir() if p.suffix.lower() in (".jpg", ".jpeg", ".png", ".webp", ".mp4", ".mov")) \
            if local else []
        self.video = video
        self.verifier = verifier                   # (requête, image) → bool ; ex. ai.image_pertinente si clé Anthropic

    def _candidates(self, query):
        for name, fn in MOTEURS.items():
            if name in self.errors:
                continue
            try:
                yield from fn(query)
            except Exception as e:                # réseau bloqué, API changée : on passe à la source suivante
                code = getattr(getattr(e, "response", None), "status_code", None)
                if code in (429, 503):             # débit limité : on saute cette recherche, la source reste active
                    print(f"   archives : {name} limite le débit, recherche suivante")
                    continue
                self.errors.add(name)
                print(f"   archives : {name} indisponible ({e.__class__.__name__})")

    def find(self, query, kind="image"):
        """Un média libre pour `query` : {chemin, type, credit} ou None (le montage met alors un fond d'ambiance)."""
        if self.local:                             # images fournies par l'utilisateur : on les prend dans l'ordre
            for p in self.local:
                if str(p) not in self.used:
                    self.used.add(str(p))
                    return {"chemin": str(p), "type": "video" if p.suffix.lower() in (".mp4", ".mov") else "image",
                            "credit": {"titre": p.name, "auteur": "fourni par la chaîne", "licence": "droits de la chaîne",
                                       "source": "local", "page": ""}}
            return None
        cands = list(self._candidates(query))
        if kind == "video" and self.video and "archive" not in self.errors:
            try:
                cands = archive_films(query) + cands
            except Exception as e:
                self.errors.add("archive")
                print(f"   archives : Internet Archive indisponible ({e.__class__.__name__})")
        for c in cands:
            text = f"{c['titre']} {c['description']}"
            if not c.get("url") or c["url"] in self.used or c.get("page") in self.used or INTERDIT.search(text) \
                    or not licence_ok(c["licence"]) \
                    or not pertinence(query, c):
                continue
            if c["type"] == "image" and c.get("largeur", 0) and c["largeur"] < 640:
                continue
            path = self._download(c)
            if path and self.verifier and not self.verifier(query, path):
                continue                           # Claude a regardé l'image : elle ne montre pas ce qu'on cherche
            if path:
                self.used.update({c["url"], c.get("page")})   # même image jamais deux fois, même en autre taille
                credit = {k: c[k] for k in ("titre", "auteur", "licence", "source", "page")}
                credit["licence"] = re.split(r"[.;]| For ", credit["licence"])[0].strip()[:40]
                self.credits.append(credit)
                return {"chemin": str(path), "type": c["type"], "credit": credit}
        return None

    def _download(self, c):
        ext = ".mp4" if c["type"] == "video" else (Path(c["url"].split("?")[0]).suffix.lower() or ".jpg")
        path = self.dir / (hashlib.sha1(c["url"].encode()).hexdigest()[:16] + ext)
        if path.exists():
            return path
        try:
            if c["type"] == "video":               # 40 premières secondes suffisent pour un plan d'illustration
                import subprocess
                subprocess.run(["ffmpeg", "-y", "-v", "error", "-user_agent", UA, "-t", "40", "-i", c["url"],
                                "-c", "copy", str(path)], check=True, timeout=180)
            else:                                  # téléchargement borné : 45 s et 25 Mo au maximum par image
                import time

                import requests
                t0, size = time.time(), 0
                time.sleep(1.0)                    # politesse : une image par seconde au plus
                with requests.get(c["url"], stream=True, timeout=(10, 20), headers={"User-Agent": UA}) as r:
                    if r.status_code == 429:       # serveur saturé : on le signale, l'image suivante sera tentée
                        print(f"   archives : {c['source']} demande d'attendre ({r.headers.get('Retry-After', '?')} s)")
                    r.raise_for_status()
                    with open(path, "wb") as f:
                        for chunk in r.iter_content(65536):
                            size += len(chunk)
                            if time.time() - t0 > 45 or size > 25 * 1024 * 1024:
                                raise TimeoutError("image trop lente ou trop lourde")
                            f.write(chunk)
                from PIL import Image
                with Image.open(path) as im:       # fichier vérifié : vraie image lisible
                    im.verify()
            return path
        except Exception:
            path.unlink(missing_ok=True)
            return None

    def save_credits(self, path):
        Path(path).write_text(json.dumps(self.credits, ensure_ascii=False, indent=1), encoding="utf-8")
