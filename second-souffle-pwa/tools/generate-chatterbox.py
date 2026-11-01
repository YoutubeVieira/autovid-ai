#!/usr/bin/env python3
"""Produit les voix off avec Chatterbox (modèle libre, MIT) au lieu de l'API Gemini.

Mêmes textes que tools/generate-audio.js (adaptés au genre de la voix), mêmes noms de fichiers,
dossier de sortie séparé : audio-chatterbox/<langue>/<f|m>/<id>.wav. Aucune clé, aucun quota.

Ce script n'a pas été essayé avec le vrai modèle (il faut Python, PyTorch et le téléchargement du
modèle sur votre PC). Le contrôle des arguments, des textes et de l'assemblage a été essayé avec
--dry-run. Commencez par --test.

  python tools/generate-chatterbox.py --dry-run --lang fr --max 5
  python tools/generate-chatterbox.py --test
  python tools/generate-chatterbox.py --lang fr

Voix de référence (un extrait propre de 10 à 20 secondes, une seule personne, sans musique) :
  voix-reference/f.wav, voix-reference/m.wav          la même voix dans les trois langues
  voix-reference/fr-f.wav, en-m.wav, pt-f.wav, ...    voix propre à une langue (facultatif)
La voix de référence doit être la vôtre, ou celle d'une personne qui a donné son accord écrit
pour qu'on clone sa voix. Écrivez cet accord (nom, date, usage) dans voix-reference/consentement.txt :
le script refuse de cloner sans ce fichier. Sans voix de référence, --voix-par-defaut utilise la voix
intégrée du modèle.

N'utilisez pas comme référence des voix produites par un service dont les conditions l'interdisent.

Chatterbox ajoute à chaque fichier un tatouage inaudible (PerTh) : ne le retirez pas. Indiquez
dans l'application que la voix est synthétique.
"""
import argparse, array, csv, json, math, os, subprocess, sys, tempfile, wave

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
ap.add_argument("--lang", default=None, help="fr, en, pt ou all")
ap.add_argument("--gender", default="both", choices=["f", "m", "both"])
ap.add_argument("--only", default="", help="ne produire que les identifiants qui commencent ainsi")
ap.add_argument("--max", type=int, default=0, help="s'arrêter après N nouveaux fichiers")
ap.add_argument("--out", default="audio-chatterbox")
ap.add_argument("--ref", default="voix-reference", help="dossier des voix de référence")
ap.add_argument("--device", default="auto", help="auto, cuda ou cpu")
ap.add_argument("--exaggeration", type=float, default=0.4, help="0.25 très posé, 0.5 neutre, plus haut plus expressif")
ap.add_argument("--cfg", type=float, default=0.4, help="0.3 à 0.5 : plus bas donne un rythme plus lent et plus régulier")
ap.add_argument("--voix-par-defaut", action="store_true", help="utiliser la voix intégrée du modèle (aucun clonage)")
ap.add_argument("--test", action="store_true", help="une phrase par langue et par voix")
ap.add_argument("--dry-run", action="store_true", help="essai sans modèle : fichiers de test (bip)")
args = ap.parse_args()
if not args.lang and not args.test:
    ap.error("indiquez --lang fr|en|pt|all, ou --test")
LANGS = ["fr", "en", "pt"] if (args.test or args.lang == "all") else [args.lang]
GENDERS = ["f", "m"] if args.gender == "both" else [args.gender]


def load_items():
    tmp = os.path.join(tempfile.gettempdir(), "ss-textes.json")
    node = ["node", os.path.join(HERE, "generate-audio.js"), "--export-texts", tmp, "--lang", "all"]
    try:
        subprocess.run(node, check=True, capture_output=True, cwd=ROOT)
    except (OSError, subprocess.CalledProcessError) as e:
        sys.exit("Node.js est nécessaire pour lire les textes (tools/generate-audio.js) : " + str(e))
    with open(tmp, encoding="utf8") as f:
        items = json.load(f)
    items = [i for i in items if i["lang"] in LANGS and i["gender"] in GENDERS and i["id"].startswith(args.only)]
    if args.test:
        seen = set()
        keep = []
        for i in items:
            k = (i["lang"], i["gender"])
            if k not in seen:
                seen.add(k)
                keep.append(i)
        items = keep
    return items


# ---------- WAV ----------
def write_wav(path, pcm, rate):
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(pcm.tobytes())


def read_wav(path):
    with wave.open(path, "rb") as w:
        pcm = array.array("h")
        pcm.frombytes(w.readframes(w.getnframes()))
        return pcm, w.getframerate()


def silence(sec, rate):
    return array.array("h", bytes(2 * round(sec * rate)))


def tone(sec, rate):
    return array.array("h", (round(3000 * math.sin(2 * math.pi * 440 * i / rate)) for i in range(round(sec * rate))))


def normalize(pcm, target=0.89):
    """Même niveau de crête pour tous les fichiers (environ -1 dB), sans jamais écrêter."""
    peak = max((abs(x) for x in pcm), default=0)
    if peak < 300:
        return pcm
    k = target * 32767 / peak
    return array.array("h", (max(-32768, min(32767, round(x * k))) for x in pcm))


# ---------- voix de référence ----------
def reference_for(lang, g):
    for name in (lang + "-" + g + ".wav", g + ".wav"):
        p = os.path.join(args.ref, name)
        if os.path.exists(p):
            return p
    return None


def check_references(items):
    if args.voix_par_defaut or args.dry_run:
        return
    need = sorted({(i["lang"], i["gender"]) for i in items})
    missing = [lang + "/" + g for lang, g in need if not reference_for(lang, g)]
    if missing:
        sys.exit("Il manque une voix de référence pour : " + ", ".join(missing) + ".\n"
                 "Placez " + os.path.join(args.ref, "f.wav") + " et " + os.path.join(args.ref, "m.wav") +
                 " (10 à 20 secondes, une seule personne), ou utilisez --voix-par-defaut.")
    if not os.path.exists(os.path.join(args.ref, "consentement.txt")):
        sys.exit("Clonage refusé : créez " + os.path.join(args.ref, "consentement.txt") +
                 " avec le nom de la personne, la date et l'usage autorisé (accord écrit de cette personne).")
    for lang, g in need:
        p = reference_for(lang, g)
        try:
            with wave.open(p, "rb") as w:
                sec = w.getnframes() / w.getframerate()
            if sec < 5 or sec > 40:
                print("Attention : la référence " + p + " dure " + format(sec, ".0f") + " s (10 à 20 s conseillées).")
        except Exception:
            print("Note : durée de " + p + " non vérifiée (format WAV non standard).")


# ---------- moteur ----------
model = None


def load_model():
    global model
    if args.dry_run or model is not None:
        return
    try:
        import torch
        from chatterbox.mtl_tts import ChatterboxMultilingualTTS
    except ImportError as e:
        sys.exit("Chatterbox n'est pas installé (" + str(e) + "). Voir docs/CHATTERBOX.md.")
    dev = args.device
    if dev == "auto":
        dev = "cuda" if torch.cuda.is_available() else "cpu"
    if dev == "cpu":
        print("Pas de carte graphique utilisable : la production sera très lente.")
    print("Chargement du modèle sur " + dev + " (le premier lancement télécharge plusieurs Go)...")
    model = ChatterboxMultilingualTTS.from_pretrained(device=dev)


def synth(item):
    rate = 24000
    if args.dry_run:
        return tone(max(0.4, item["est"] - item["pause"]), rate), rate
    load_model()
    kw = dict(language_id=item["lang"], exaggeration=args.exaggeration, cfg_weight=args.cfg)
    ref = None if args.voix_par_defaut else reference_for(item["lang"], item["gender"])
    if ref:
        kw["audio_prompt_path"] = ref
    wav = model.generate(item["text"], **kw)
    pcm = array.array("h")
    pcm.frombytes((wav.squeeze().clamp(-1, 1) * 32767).short().cpu().numpy().tobytes())
    return pcm, model.sr


def main():
    items = load_items()
    check_references(items)
    print(("[essai sans modèle] " if args.dry_run else "") + str(len(items)) + " fichiers à examiner, langues : " + ", ".join(LANGS))
    segs, report = {}, []
    done = skipped = 0
    stopped = False
    for it in items:
        if args.max and done >= args.max:
            stopped = True
            break
        d = os.path.join(args.out, it["lang"], it["gender"])
        os.makedirs(d, exist_ok=True)
        path = os.path.join(d, it["id"] + ".wav")
        if os.path.exists(path) and not args.dry_run:
            pcm, rate = read_wav(path)
            skipped += 1
        else:
            pcm, rate = synth(it)
            pcm = normalize(pcm)
            write_wav(path, pcm, rate)
            done += 1
            sec = len(pcm) / rate
            ratio = sec / max(0.5, it["est"] - it["pause"])
            flag = "" if 0.5 <= ratio <= 1.8 else "durée inhabituelle"
            report.append([it["lang"], it["gender"], it["id"], format(sec, ".1f"), format(it["est"], ".1f"), flag])
            if done % 10 == 0:
                print(str(done) + " fichiers produits")
        if it["cat"] == "bienetre":
            k = (it["lang"], it["gender"], ".".join(it["id"].split(".")[:-1]))
            segs.setdefault(k, []).append((it["id"], pcm, rate, it["pause"]))
    if report:
        os.makedirs(args.out, exist_ok=True)
        with open(os.path.join(args.out, "controle.csv"), "a", newline="", encoding="utf8") as f:
            csv.writer(f).writerows(report)
        odd = [r for r in report if r[5]]
        if odd:
            print(str(len(odd)) + " fichier(s) à réécouter (durée inhabituelle), voir controle.csv")
    if stopped:
        print("Arrêt demandé après " + str(done) + " fichiers (--max). Relancez pour continuer ; les séances de bien-être seront assemblées à la fin.")
        return
    for (lang, g, base), lst in sorted(segs.items()):
        lst.sort(key=lambda s: s[0])
        rate = lst[0][2]
        out = array.array("h")
        for _, pcm, _, pause in lst:
            out.extend(pcm)
            out.extend(silence(pause, rate))
        write_wav(os.path.join(args.out, lang, g, base + ".wav"), out, rate)
        print("séance assemblée : " + lang + "/" + g + "/" + base + ".wav (" + format(len(out) / rate, ".0f") + " s, " + str(len(lst)) + " phrases)")
    print("Terminé : " + str(done) + " produits, " + str(skipped) + " déjà présents. Dossier : " + os.path.abspath(args.out))


main()
