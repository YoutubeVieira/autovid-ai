"""Correcteur de narration : texte lisible par la voix, graphie phonétique, puis contrôle de l'audio à l'oreille.

Trois étapes, en français, portugais du Brésil et anglais :
1. `ecrire(texte, langue)` — texte propre pour les sous-titres : nombres, années, dates, heures, ordinaux,
   pourcentages et monnaies écrits en toutes lettres (« 1919 » → « mille neuf cent dix-neuf »).
2. `dire(texte, langue)` — même texte en graphie phonétique pour la voix, mot pour mot (« dix-neuf » → « dize-neuf »,
   « dix » en fin de phrase → « disse ») ; le lexique `lexique_phonetique.json` est modifiable et s'enrichit.
3. `controler(audio, attendu, langue)` — Whisper (hors ligne) réécoute la voix et liste les mots mal dits ;
   `narration.voice_segments` relance alors avec une autre graphie ou un débit plus lent.
Règles trouvées en testant Supertonic 3 + Whisper : « mil neuf cent dix-neuf » est entendu « 1969 » et
« dix-neuf » seul « 1999 », alors que « dize-neuf » donne bien 1919.
"""
import difflib
import json
import os
import re
import unicodedata
from pathlib import Path

LEXIQUE = Path(__file__).with_name("lexique_phonetique.json")
N2W = {"fr": "fr", "pt": "pt_BR", "en": "en"}
WHISPER = "sherpa-onnx-whisper-small"
WHISPER_URL = f"https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models/{WHISPER}.tar.bz2"
MOIS = {"fr": "janvier février mars avril mai juin juillet août septembre octobre novembre décembre",
        "pt": "janeiro fevereiro março abril maio junho julho agosto setembro outubro novembro dezembro",
        "en": "January February March April May June July August September October November December"}


def _n2w(n, langue, to="cardinal"):
    from num2words import num2words
    txt = num2words(n, lang=N2W.get(langue, "fr"), to=to)
    return txt.replace(",", "")            # pt_BR écrit « mil, novecentos e dezenove »


def _annee(y, langue):
    if langue == "en":
        return _n2w(y, langue, "year")
    return _n2w(y, langue)


# --------------------------------------------------------------------------- 1. texte écrit en toutes lettres

def ecrire(texte, langue="fr"):
    """Nombres et symboles en toutes lettres, sans toucher aux balises [pt]…[/pt] ni au reste du texte."""
    t = texte
    mois = MOIS.get(langue, MOIS["fr"]).split()
    # dates 25/02/1922
    def date(m):
        j, mo, a = int(m.group(1)), int(m.group(2)), int(m.group(3))
        if not 1 <= mo <= 12:
            return m.group(0)
        if langue == "en":
            return f"{mois[mo - 1]} {_n2w(j, langue, 'ordinal')}, {_annee(a, langue)}"
        jour = "premier" if (langue == "fr" and j == 1) else ("primeiro" if langue == "pt" and j == 1 else _n2w(j, langue))
        de = " de " if langue == "pt" else " "
        return f"{jour}{de}{mois[mo - 1]}{de}{_annee(a, langue)}"
    t = re.sub(r"\b(\d{1,2})/(\d{1,2})/(\d{4})\b", date, t)
    # heures 14h30 / 14:30
    def heure(m):
        h, mi = int(m.group(1)), int(m.group(2) or 0)
        mot = {"fr": "heure", "pt": "hora", "en": "o'clock"}[langue] + ("s" if h > 1 and langue != "en" else "")
        if langue == "en":
            return f"{_n2w(h, langue)} {_n2w(mi, langue)}" if mi else f"{_n2w(h, langue)} {mot}"
        return f"{_n2w(h, langue)} {mot}" + (f" {_n2w(mi, langue)}" if mi else "")
    t = re.sub(r"\b(\d{1,2})\s?[h:]\s?(\d{2})?\b(?!\s?%)", lambda m: heure(m) if "h" in m.group(0) or m.group(2) else m.group(0), t)
    # monnaies
    devise = {"fr": {"€": "euros", "$": "dollars", "R$": "réais"}, "pt": {"€": "euros", "$": "dólares", "R$": "reais"},
              "en": {"€": "euros", "$": "dollars", "R$": "reais"}}[langue]
    t = re.sub(r"(R\$|\$|€)\s?(\d+(?:[.,]\d+)?)", lambda m: f"{m.group(2)} {devise[m.group(1)]}", t)
    t = re.sub(r"(\d+(?:[.,]\d+)?)\s?(€)", lambda m: f"{m.group(1)} {devise[m.group(2)]}", t)
    # pourcentages
    pc = {"fr": "pour cent", "pt": "por cento", "en": "percent"}[langue]
    t = re.sub(r"(\d+(?:[.,]\d+)?)\s?%", lambda m: f"{m.group(1)} {pc}", t)
    # ordinaux 1er, 2e, 1º, 1st
    t = re.sub(r"\b(\d+)(er|re|ère|e|ème|º|ª|°|st|nd|rd|th)\b",
               lambda m: _n2w(int(m.group(1)), langue, "ordinal") if not (langue == "fr" and m.group(1) == "1"
                                                                           and m.group(2) in ("er", "re", "ère"))
               else ("premier" if m.group(2) == "er" else "première"), t)
    # années (1000 à 2099) puis autres nombres, décimaux compris
    t = re.sub(r"\b(1\d{3}|20\d{2})\b", lambda m: _annee(int(m.group(1)), langue), t)
    def nombre(m):
        s = m.group(0).replace(" ", "")
        if re.search(r"[.,]\d{1,2}$", s) and not re.search(r"[.,]\d{3}$", s):
            return _n2w(float(s.replace(",", ".")), langue)
        return _n2w(int(re.sub(r"[.,\s]", "", s)), langue)
    t = re.sub(r"\b\d{1,3}(?:[ .,]\d{3})+(?:[.,]\d+)?\b|\b\d+(?:[.,]\d+)?\b", nombre, t)
    # abréviations courantes
    abr = {"fr": {r"\bM\.\s": "Monsieur ", r"\bMme\b": "Madame", r"\bn°\s?": "numéro ", r"\bkm\b": "kilomètres",
                  r"\bkg\b": "kilos", r"\bSt\b": "Saint", r"\bDr\b": "Docteur", "&": " et "},
           "pt": {r"\bSr\.\s": "Senhor ", r"\bSra\.\s": "Senhora ", r"\bnº\s?": "número ", r"\bkm\b": "quilômetros",
                  r"\bkg\b": "quilos", r"\bDr\.\s": "Doutor ", "&": " e "},
           "en": {r"\bMr\.\s": "Mister ", r"\bMrs\.\s": "Missus ", r"\bDr\.\s": "Doctor ", r"\bkm\b": "kilometers",
                  r"\bkg\b": "kilograms", r"\bSt\.\s": "Saint ", "&": " and "}}[langue]
    for k, v in abr.items():
        t = re.sub(k, v, t)
    return re.sub(r"\s{2,}", " ", t).strip()


# --------------------------------------------------------------------------- 2. graphie phonétique pour la voix

def lexique():
    try:
        return json.loads(LEXIQUE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def apprendre(langue, mot, graphie):
    """Ajoute une prononciation trouvée par le contrôle audio (ou demandée par l'utilisateur) au lexique."""
    lex = lexique()
    lex.setdefault(langue, {}).setdefault("mots", {})[mot.lower()] = graphie
    LEXIQUE.write_text(json.dumps(lex, ensure_ascii=False, indent=1), encoding="utf-8")


TAG = re.compile(r"\[(pt|fr|en)\](.*?)\[/\1\]", re.S)


def marquer(texte, langue="fr"):
    """Entoure les mots d'une autre langue connus du lexique (noms, lieux, termes de capoeira) de balises
    [pt]…[/pt], [fr]…[/fr] ou [en]…[/en] : la voix les lit avec la prononciation de leur pays."""
    etr = lexique().get(langue, {}).get("etrangers", {})
    if not etr:
        return texte
    parts = re.split(r"(\[(?:pt|fr|en)\].*?\[/(?:pt|fr|en)\])", texte, flags=re.S)   # zones déjà balisées : intactes
    pat = re.compile(r"(?<![\w-])(" + "|".join(re.escape(m) for m in sorted(etr, key=len, reverse=True)) + r")(?![\w-])", re.I)
    low = {k.lower(): v for k, v in etr.items()}
    for i in range(0, len(parts), 2):
        parts[i] = pat.sub(lambda m: f"[{low[m.group(1).lower()]}]{m.group(1)}[/{low[m.group(1).lower()]}]"
                           if low[m.group(1).lower()] != langue else m.group(1), parts[i])
    return "".join(parts)


def morceaux(texte, langue):
    """Texte balisé → [(morceau, langue)] dans l'ordre."""
    out, pos = [], 0
    for m in TAG.finditer(texte):
        if texte[pos:m.start()].strip():
            out.append((texte[pos:m.start()].strip(), langue))
        out.append((m.group(2).strip(), m.group(1)))
        pos = m.end()
    if texte[pos:].strip():
        out.append((texte[pos:].strip(), langue))
    return out


def sans_balises(texte):
    return TAG.sub(lambda m: m.group(2), texte)


def dire(texte, langue="fr", variantes=None):
    """Texte → graphie phonétique pour la voix, MOT POUR MOT (même nombre de mots que le texte affiché, pour caler
    les sous-titres). `variantes` : {mot: graphie} à essayer en plus (relance après un contrôle raté)."""
    lex = lexique().get(langue, {})
    mots = {**lex.get("mots", {}), **(variantes or {})}
    regles = lex.get("regles", [])
    out = texte
    for r in regles:                       # règles contextuelles : [motif, remplacement], majuscule gardée
        out = re.sub(r[0], lambda m, rep=r[1]: _casse(m.group(0), m.expand(rep)), out, flags=re.I)
    if mots:
        pat = re.compile(r"(?<![\w-])(" + "|".join(re.escape(m) for m in sorted(mots, key=len, reverse=True)) + r")(?![\w-])",
                         re.I)
        out = pat.sub(lambda m: _casse(m.group(1), mots[m.group(1).lower()]), out)
    return out


def _casse(orig, new):
    return new[:1].upper() + new[1:] if orig[:1].isupper() else new


# --------------------------------------------------------------------------- 3. contrôle de l'audio (Whisper)

_REC = {}


def _sans_accents(s):
    return unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()


def normaliser(texte, langue):
    """Forme de comparaison : nombres en lettres, minuscules, sans accents ni ponctuation, mots séparés."""
    t = sans_balises(texte)
    t = ecrire(t, langue).lower().replace("-", " ").replace("'", " ").replace("’", " ")
    return [w for w in re.findall(r"[a-z0-9]+", _sans_accents(t))]


def whisper_disponible():
    import importlib.util
    return importlib.util.find_spec("sherpa_onnx") is not None and importlib.util.find_spec("num2words") is not None


def _recognizer(langue):
    if langue not in _REC:
        import tarfile
        import urllib.request

        import sherpa_onnx as so
        root = Path(os.environ.get("AUTOVID_CACHE", Path.home() / ".cache" / "autovid")) / "asr"
        d = root / WHISPER
        if not (d / "small-encoder.int8.onnx").exists():
            root.mkdir(parents=True, exist_ok=True)
            print("  téléchargement de Whisper small pour le contrôle des voix (une seule fois)…")
            arc = root / f"{WHISPER}.tar.bz2"
            urllib.request.urlretrieve(WHISPER_URL, arc)
            with tarfile.open(arc) as t:
                t.extractall(root, filter="data")
            arc.unlink()
        _REC[langue] = so.OfflineRecognizer.from_whisper(
            encoder=str(d / "small-encoder.int8.onnx"), decoder=str(d / "small-decoder.int8.onnx"),
            tokens=str(d / "small-tokens.txt"), language=langue, task="transcribe", num_threads=max(os.cpu_count() or 2, 2))
    return _REC[langue]


def transcrire(audio, sr, langue):
    import numpy as np
    mono = audio.mean(axis=1) if audio.ndim > 1 else audio
    rec = _recognizer(langue)
    s = rec.create_stream()
    s.accept_waveform(sr, np.ascontiguousarray(mono, dtype=np.float32))
    rec.decode_stream(s)
    return s.result.text.strip()


def comparer(attendu, entendu, langue, ignorer=()):
    """Mots mal dits : [(attendu, entendu)]. Tolère les petites différences d'orthographe (« dez » / « deis »).
    `ignorer` : mots à ne pas juger (termes capoeira en portugais dans un texte français)."""
    a, e = normaliser(attendu, langue), normaliser(entendu, langue)
    ign = {w for x in ignorer for w in normaliser(x, langue)}
    erreurs = []
    for op, i1, i2, j1, j2 in difflib.SequenceMatcher(None, a, e, autojunk=False).get_opcodes():
        if op == "equal":
            continue
        att, ent = " ".join(a[i1:i2]), " ".join(e[j1:j2])
        rest = [w for w in a[i1:i2] if w not in ign]       # mots étrangers retirés : jugés à part
        if att and not rest:
            continue
        if rest and len(rest) < i2 - i1 and all(
                any(difflib.SequenceMatcher(None, w, x).ratio() >= 0.75 for x in e[j1:j2]) for w in rest):
            continue
        voisin = any(w in ign for w in a[max(i1 - 1, 0): i2 + 1])
        if rest and voisin and e[j1:j2]:      # à côté d'un mot étranger, Whisper colle souvent les mots
            r, h = "".join(rest), "".join(e[j1:j2])
            if sum(b.size for b in difflib.SequenceMatcher(None, r, h).get_matching_blocks()) >= 0.7 * len(r):
                continue
        att = " ".join(rest) if rest else att
        if att and ent:
            r = difflib.SequenceMatcher(None, att, ent).ratio()
            if r >= 0.75 or (len(att) <= 4 and r >= 0.5):     # « dez » / « deis » : même mot, autre graphie
                continue
        if not att and len(ent) <= 3:          # petit mot en trop (« et », « que ») : on laisse passer
            continue
        if not att:                            # mot en trop : on montre les mots autour pour situer
            att = "(" + " ".join(a[max(i1 - 2, 0): i2 + 2]) + ")"
        erreurs.append((att, ent))
    return erreurs


def score(erreurs):
    return sum(max(len(a.split()), 1) for a, _ in erreurs)
