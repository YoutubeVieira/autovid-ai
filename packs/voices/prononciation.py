"""Correction de prononciation francaise pour les voix qui lisent les lettres (Supertonic) : 'habitant' -> 'abitan'.

Principe: espeak-ng (via piper-tts) connait la bonne prononciation. Pour chaque mot, on cherche l'orthographe la plus
courte (lettres muettes finales retirees) dont les phonemes espeak sont IDENTIQUES a ceux du mot d'origine.
Un dictionnaire de cas particuliers (prononciation.json) a priorite. Aucune donnee externe.

    from prononciation import fix
    fix("Ici, chaque abonné devient habitant de Caraguá")   # -> "Ici, chaque abonné devient abitan de Caragoua"
"""
import json
import os
import re

_here = os.path.dirname(os.path.abspath(__file__))
_ph = None
_cache = {}
OVERRIDES = {}
_p = os.path.join(_here, "prononciation.json")
if os.path.exists(_p):
    OVERRIDES = {k.lower(): v for k, v in json.load(open(_p, encoding="utf-8")).items() if not k.startswith("_")}

KEEP = {"et", "est", "un", "une", "de", "du", "la", "le", "les", "des", "ce", "ces", "se", "me", "te", "ma", "ta", "sa",
        "si", "ne", "ni", "ou", "où", "au", "en", "on", "il", "tu", "je", "à", "a", "y"}  # mots courts: on ne touche pas


def _phon(word):
    global _ph
    if _ph is None:
        from piper.phonemize_espeak import EspeakPhonemizer
        _ph = EspeakPhonemizer()
    out = "".join("".join(s) for s in _ph.phonemize("fr", word))
    return re.sub(r"[ˈˌ.\s]", "", out)


VOWELS = "aeiouyàâäéèêëîïôöùûüœ"


def _candidates(w):
    """Orthographes plus 'phonetiques' d'un mot (lettres muettes de fin retirees), de la plus simple a la plus courte."""
    out = []
    # h muet initial: habiter -> abiter
    if w.startswith("h") and len(w) > 3 and w[1] in VOWELS:
        out.append(w[1:])
    # terminaisons muettes
    for end, rep in (("ers", "é"), ("er", "é"), ("ez", "é"), ("ent", "e"), ("ant", "an"), ("ants", "an"), ("ent", "en"),
                     ("ents", "en"), ("ont", "on"), ("ons", "on"), ("ins", "in"), ("int", "in"), ("ain", "in"), ("aint", "in")):
        if w.endswith(end) and len(w) > len(end) + 1:
            out.append(w[: -len(end)] + rep)
    # consonnes muettes finales (une par une): t s x d p z
    for k in range(1, 3):
        if len(w) > 3 and w[-k] in "tsxdpz" and (k == 1 or w[-1] in "tsxdpz") and w[-k - 1] not in "tsxdpz":
            out.append(w[:-k])
    # combinaisons (h muet + fin muette)
    comb = []
    for c in out:
        if c.startswith("h") and len(c) > 3 and c[1] in VOWELS:
            comb.append(c[1:])
    return out + comb


def respell(word):
    low = word.lower()
    if low in OVERRIDES:
        return OVERRIDES[low]
    if low in KEEP or len(low) <= 3 or not low.isalpha() or low.endswith("e") and not low.endswith("ent"):
        return word
    if low in _cache:
        return _cache[low]
    target = _phon(low)
    best, changed = low, True
    for _ in range(3):  # plusieurs passes: "habitants" -> "habitant" -> "abitan"
        changed = False
        for c in sorted(_candidates(best), key=len):
            if c != best and _phon(c) == target:
                best, changed = c, True
                break
        if not changed:
            break
    _cache[low] = best
    return best


def _light(word):
    """Version legere: seulement les fins en -ant(s) / -ent(s) et les cas particuliers (le reste est laisse tel quel)."""
    low = word.lower()
    if low in OVERRIDES:
        return OVERRIDES[low]
    return respell(word) if re.search(r"(ants?|ents?)$", low) else word


_U = "zéro un deux trois quatre cinq six sept huit neuf dix onze douze treize quatorze quinze seize".split()
_D = {20: "vingt", 30: "trente", 40: "quarante", 50: "cinquante", 60: "soixante"}


def num_fr(n):
    """Nombre entier (0-999999) -> lettres, français de France (soixante-dix, quatre-vingts, quatre-vingt-dix)."""
    if n < 17:
        return _U[n]
    if n < 20:
        return "dix-" + _U[n - 10]
    if n < 70:
        d, u = n // 10 * 10, n % 10
        return _D[d] + ("" if u == 0 else " et un" if u == 1 else "-" + _U[u])
    if n < 80:
        return "soixante" + (" et onze" if n == 71 else "-" + num_fr(n - 60))
    if n < 100:
        return "quatre-vingts" if n == 80 else "quatre-vingt-" + num_fr(n - 80)
    if n < 1000:
        c, r = divmod(n, 100)
        return ("cent" if c == 1 else _U[c] + " cent") + ("s" if (c > 1 and r == 0) else "") + ("" if r == 0 else " " + num_fr(r))
    m, r = divmod(n, 1000)
    return ("mille" if m == 1 else num_fr(m) + " mille") + ("" if r == 0 else " " + num_fr(r))


def nombres(text):
    """Les chiffres sont dits en toutes lettres (la voix lit mal « 13 », « 10 000 »)."""
    text = re.sub(r"(?<=\d)[ \u202f\u00a0](?=\d{3}\b)", "", text)
    return re.sub(r"\d+", lambda m: num_fr(int(m.group(0))), text)


def fix(text, level="full"):
    """level='full': toutes les lettres muettes de fin; 'light': -ant(s)/-ent(s) + dictionnaire; 'overrides': dictionnaire seul."""
    text = nombres(text)
    fn = {"full": respell, "light": _light, "overrides": lambda w: OVERRIDES.get(w.lower(), w)}[level]

    def sub(m):
        w = m.group(0)
        r = fn(w)
        if r == w.lower() or r == w:
            return w
        return r.capitalize() if w[0].isupper() else r
    return re.sub(r"[A-Za-zÀ-ÿ]+", sub, text)


def _old_fix(text):
    def sub(m):
        w = m.group(0)
        r = respell(w)
        if r == w.lower():
            return w
        return r.capitalize() if w[0].isupper() else r
    return re.sub(r"[A-Za-zÀ-ÿ]+", sub, text)
