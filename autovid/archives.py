"""Recherche automatique d'images et de vidéos d'archives LIBRES (domaine public ou licence Creative Commons).

Sources (toutes gratuites, sans clé) :
  - Wikimedia Commons (photos, documents, coupures de presse anciennes)
  - Library of Congress (photos « No known restrictions »)
  - Openverse (agrégateur d'images sous licence CC)
  - Internet Archive (films du domaine public, collection Prelinger)
Chaque média gardé est noté avec son auteur, sa licence et sa page : `credits.json`, puis le générique de fin.
Les licences « NC » (pas d'usage commercial) et « ND » (pas de modification) sont refusées : une chaîne monétisée
fait un usage commercial, et le zoom / recadrage est une modification.
"""
import hashlib
import json
import re
from pathlib import Path

UA = "AutoVid-Documentaire/1.0 (montage video educatif; contact via GitHub)"
# jamais de corps, de scène de crime, d'autopsie : YouTube démonétise, et c'est irrespectueux pour les familles
INTERDIT = re.compile(r"(corpse|cadav|dead body|bodies|autopsy|morgue|crime scene photo|gore|blood|murdered body|"
                      r"cadavre|scène de crime|autopsie|sang)", re.I)


def _get(url, params=None, timeout=25):
    import requests
    r = requests.get(url, params=params, timeout=timeout, headers={"User-Agent": UA})
    r.raise_for_status()
    return r


def licence_ok(text):
    """Domaine public, CC0, CC BY, CC BY-SA : oui. NC, ND, « tous droits réservés », inconnue : non."""
    t = (text or "").lower()
    if re.search(r"public domain|domaine public|cc0|\bpdm\b|no known restrictions", t):
        return True
    if re.search(r"\bnc\b|-nc|noncommercial|non-commercial|\bnd\b|-nd|noderiv|all rights reserved|fair use", t):
        return False
    return bool(re.search(r"cc[- ]?by|attribution", t))


def _clean(html):
    return re.sub(r"<[^>]+>", "", html or "").strip()


# --------------------------------------------------------------------------- moteurs de recherche

def commons(query, n=8):
    data = _get("https://commons.wikimedia.org/w/api.php", {
        "action": "query", "format": "json", "generator": "search", "gsrsearch": f"{query} filetype:bitmap",
        "gsrnamespace": 6, "gsrlimit": n, "prop": "imageinfo", "iiprop": "url|extmetadata|mime|size",
        "iiurlwidth": 2400}).json()
    out = []
    for page in (data.get("query", {}).get("pages") or {}).values():
        ii = (page.get("imageinfo") or [{}])[0]
        meta = ii.get("extmetadata") or {}
        lic = _clean(meta.get("LicenseShortName", {}).get("value"))
        out.append({"source": "Wikimedia Commons", "titre": page.get("title", "").replace("File:", ""),
                    "url": ii.get("thumburl") or ii.get("url"), "page": ii.get("descriptionurl"),
                    "auteur": _clean(meta.get("Artist", {}).get("value"))[:120] or "inconnu", "licence": lic,
                    "largeur": ii.get("thumbwidth") or ii.get("width", 0), "type": "image",
                    "description": _clean(meta.get("ImageDescription", {}).get("value"))[:300]})
    return out


def loc(query, n=8):
    data = _get("https://www.loc.gov/photos/", {"q": query, "fo": "json", "c": n}).json()
    out = []
    for it in data.get("results", []):
        imgs = it.get("image_url") or []
        rights = " ".join(it.get("rights_advisory") or []) if isinstance(it.get("rights_advisory"), list) \
            else str(it.get("rights_advisory") or it.get("rights") or "")
        if not imgs:
            continue
        out.append({"source": "Library of Congress", "titre": it.get("title", ""), "url": imgs[-1].split("#")[0],
                    "page": it.get("url") or it.get("id"), "auteur": ", ".join(it.get("contributor") or [])[:120] or "LOC",
                    "licence": rights or "inconnue", "largeur": 1200, "type": "image",
                    "description": " ".join(it.get("description") or [])[:300]})
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


MOTEURS = {"commons": commons, "loc": loc, "openverse": openverse}


# --------------------------------------------------------------------------- sélection + téléchargement

class Archives:
    """Cherche, filtre (licence, contenu interdit, déjà utilisé), télécharge et tient les crédits."""

    def __init__(self, dossier, local=None, video=True):
        self.dir = Path(dossier)
        self.dir.mkdir(parents=True, exist_ok=True)
        self.credits, self.used, self.errors = [], set(), set()
        self.local = sorted(p for p in Path(local).iterdir() if p.suffix.lower() in (".jpg", ".jpeg", ".png", ".webp", ".mp4", ".mov")) \
            if local else []
        self.video = video

    def _candidates(self, query):
        for name, fn in MOTEURS.items():
            if name in self.errors:
                continue
            try:
                yield from fn(query)
            except Exception as e:                # réseau bloqué, API changée : on passe à la source suivante
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
            if not c.get("url") or c["url"] in self.used or INTERDIT.search(text) or not licence_ok(c["licence"]):
                continue
            if c["type"] == "image" and c.get("largeur", 0) and c["largeur"] < 640:
                continue
            path = self._download(c)
            if path:
                self.used.add(c["url"])
                credit = {k: c[k] for k in ("titre", "auteur", "licence", "source", "page")}
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
            else:
                path.write_bytes(_get(c["url"], timeout=60).content)
            return path
        except Exception:
            return None

    def save_credits(self, path):
        Path(path).write_text(json.dumps(self.credits, ensure_ascii=False, indent=1), encoding="utf-8")
