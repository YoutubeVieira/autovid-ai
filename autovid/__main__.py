"""AutoVid — monteur vidéo automatique.

  python -m autovid analyze  ref.mp4 -o analyse/            ADN de montage d'une vidéo de référence
  python -m autovid auto     rushs/ -o out.mp4 [--music m.mp3] [--reference ref.mp4] [--style bincombat]
  python -m autovid render   brief.yaml -o out.mp4         montage piloté par un brief (titres, étapes, cercles…)
  python -m autovid fun      clip.mp4 -o out.mp4          clip d'humour / animaux / IA : accroche, ralenti, bruitages
  python -m autovid talk     face_cam.mp4 -o out.mp4       coupe des silences + « euh » + sous-titres ElevenLabs
  python -m autovid combat   combat.mp4 -o out.mp4         short éducatif analysé (squelette, anatomie, sons)
  python -m autovid serve                                   plateforme web (téléphone ↔ PC)
  python -m autovid watch    dossier_sync/ sorties/         traite chaque vidéo déposée
"""
import argparse
import json
import os
import tempfile
from pathlib import Path

from .analyze import analyze, summary
from .planner import auto_brief, resolve
from .render import render
from .styles import STYLES
from .talk import talk


def _load_brief(path):
    text = Path(path).read_text(encoding="utf-8")
    if path.endswith((".yaml", ".yml")):
        import yaml
        return yaml.safe_load(text)
    return json.loads(text)


def _workdir(args, out):
    return args.workdir or tempfile.mkdtemp(prefix=f"autovid_{Path(out).stem}_")


def main(argv=None):
    ap = argparse.ArgumentParser(prog="autovid", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    a = sub.add_parser("analyze", help="extraire l'ADN d'une vidéo")
    a.add_argument("videos", nargs="+")
    a.add_argument("-o", "--out", default="analyse")

    au = sub.add_parser("auto", help="montage autonome d'un dossier de rushs")
    au.add_argument("clips_dir")
    au.add_argument("-o", "--out", required=True)
    au.add_argument("--style", choices=list(STYLES), default="bincombat")
    au.add_argument("--music")
    au.add_argument("--reference", help="vidéo dont on copie le rythme et la mise en page")
    au.add_argument("--watermark")
    au.add_argument("--cta", help="texte d'appel à l'action final, ex. « SAVE AND TRY »")
    au.add_argument("--save-brief", help="écrit le brief généré (JSON) pour le retoucher ensuite")
    au.add_argument("--workdir")

    r = sub.add_parser("render", help="rendre un brief YAML/JSON")
    r.add_argument("brief")
    r.add_argument("-o", "--out", required=True)
    r.add_argument("--workdir")

    t = sub.add_parser("talk", help="vidéo face caméra : cut des silences + sous-titres")
    t.add_argument("video")
    t.add_argument("-o", "--out", required=True)
    t.add_argument("--language", help="code langue ISO, ex. fra")
    t.add_argument("--noise-db", type=float, default=-35)
    t.add_argument("--min-silence", type=float, default=0.4)
    t.add_argument("--workdir")

    c = sub.add_parser("combat", help="short combat éducatif 100 % automatique")
    c.add_argument("video")
    c.add_argument("-o", "--out", required=True)
    c.add_argument("--music", help="musique de fond (sinon beat généré, libre de droits)")
    c.add_argument("--handle", help="ton @ affiché en filigrane")
    c.add_argument("--max-impacts", type=int, default=6)
    c.add_argument("--resolution", choices=["1080", "1440", "4k", "8k"], default="1080")
    c.add_argument("--ai", choices=["claude"], help="explications rédigées par Claude à partir des images")
    c.add_argument("--no-hook", action="store_true")
    c.add_argument("--original-audio", type=float, default=0.7, help="volume du son d'origine (0 = coupé)")
    c.add_argument("--discipline", choices=["combat", "capoeira"], default="combat",
                   help="capoeira : noms brésiliens (ginga, meia-lua, rasteira, aú…) prononcés en portugais")
    c.add_argument("--voice-id", help="voix ElevenLabs (par défaut : celle créée par « voice-clone »)")
    c.add_argument("--subs", default="fr,pt,en", help="langues des sous-titres (fr, pt = portugais du Brésil, en)")
    c.add_argument("--burn", default="fr", help="langue incrustée dans l'image (fr, pt, en ou none)")
    c.add_argument("--no-extras", action="store_true", help="sans miniatures ni fichier SEO")
    c.add_argument("--no-motion", action="store_true",
                   help="sans intro HyperFrames ni carte de fin Remotion (sinon utilisées si motion/ est installé)")
    c.add_argument("--framing", choices=["auto", "blur", "cover"], default="auto",
                   help="vidéo paysage : blur = entière sur fond flouté, cover = recadrée au centre (sujets plus grands)")
    c.add_argument("--tts", choices=["auto", "elevenlabs", "kokoro", "none"], default="auto",
                   help="voix off : ElevenLabs (ta voix), Kokoro (voix locale de test), none")
    c.add_argument("--style", choices=["fluide", "analyse"], default="fluide",
                   help="fluide : sans pause, traits et zoom sur le membre ; analyse : arrêts sur image commentés")
    c.add_argument("--kit", choices=["reaction", "classique"], default="reaction",
                   help="sons : reaction = phonk 808 (comme la vidéo réaction), classique = beat d'origine")
    c.add_argument("--music-from", help="reprendre la bande-son d'une vidéo (seulement si tu en as les droits)")
    c.add_argument("--workdir")

    c.add_argument("--force", action="store_true",
                   help="analyser même si aucune vraie personne n'est reconnue (créature d'IA, animal, dessin…)")

    fu = sub.add_parser("fun", help="clip court d'humour, d'animaux ou d'IA (sans analyse anatomique)")
    fu.add_argument("video")
    fu.add_argument("-o", "--out", required=True)
    fu.add_argument("--texte", action="append", metavar="LIGNE1/LIGNE2",
                    help="texte à l'écran (3 fois max : début, ralenti, fin), ex. --texte \"LA DINDE A PRIS/SA REVANCHE\"")
    fu.add_argument("--ai", choices=["claude"], help="textes écrits par Claude à partir des images")
    fu.add_argument("--ia", action="store_true", help="ajoute la mention « VIDÉO GÉNÉRÉE PAR IA »")
    fu.add_argument("--handle")
    fu.add_argument("--music")
    fu.add_argument("--workdir")

    vc = sub.add_parser("voice-clone", help="clone ta voix (ElevenLabs) à partir de tes enregistrements")
    vc.add_argument("samples", nargs="+", help="1 à 3 min de ta voix, sans musique (mp3/wav/m4a)")
    vc.add_argument("--name", default="Ma voix AutoVid")
    vc.add_argument("--i-own-this-voice", action="store_true", required=True,
                    help="obligatoire : tu confirmes que c'est TA voix (ou que tu as l'accord écrit de la personne)")

    th = sub.add_parser("thumbs", help="ADN d'un dossier de miniatures de référence")
    th.add_argument("folder")
    th.add_argument("-o", "--out", default="analyse/miniatures.json")

    sk = sub.add_parser("skills", help="installer un skill .zip (vérifié) ou exporter nos skills en .zip")
    sk_sub = sk.add_subparsers(dest="skills_cmd", required=True)
    ski = sk_sub.add_parser("install")
    ski.add_argument("zip")
    ski.add_argument("--overwrite", action="store_true")
    skp = sk_sub.add_parser("pack")
    skp.add_argument("-o", "--out", default="dist/skill-montage-video.zip")

    s = sub.add_parser("serve", help="plateforme web locale")
    s.add_argument("--port", type=int, default=8765)
    s.add_argument("--host", default="0.0.0.0")
    s.add_argument("--data", default="donnees")

    w = sub.add_parser("watch", help="dossier surveillé (Drive, iCloud, Syncthing…)")
    w.add_argument("in_dir")
    w.add_argument("out_dir")
    w.add_argument("--mode", choices=["combat", "fun", "talk"], default="combat")
    w.add_argument("--handle")

    args = ap.parse_args(argv)
    if args.cmd == "combat":
        from .combat import PasHumain
        try:
            return _run(args)
        except PasHumain as e:
            raise SystemExit(f"✘ {e}")
    return _run(args)


def _run(args):
    if args.cmd == "analyze":
        for v in args.videos:
            out = Path(args.out) / Path(v).stem[:40]
            dna = analyze(v, out)
            (out / "resume.md").write_text(summary(dna) + "\n", encoding="utf-8")
            print(summary(dna), f"\n→ {out}/adn.json, planche.jpg\n")
    elif args.cmd == "auto":
        brief = auto_brief(args.clips_dir, args.style, args.music, args.reference, args.watermark, args.cta)
        if args.save_brief:
            Path(args.save_brief).write_text(json.dumps(brief, indent=2, ensure_ascii=False), encoding="utf-8")
        resolved = resolve(brief)
        print(f"  {len(resolved['segments'])} plans, {resolved['total_duration']:.2f} s @ {resolved['bpm']} BPM")
        print("→", render(resolved, args.out, _workdir(args, args.out)))
    elif args.cmd == "render":
        resolved = resolve(_load_brief(args.brief), Path(args.brief).parent)
        print(f"  {len(resolved['segments'])} plans, {resolved['total_duration']:.2f} s @ {resolved['bpm']} BPM")
        print("→", render(resolved, args.out, _workdir(args, args.out)))
    elif args.cmd == "combat":
        from .combat import combat
        langs = [x.strip() for x in args.subs.split(",") if x.strip()]
        print("→", combat(args.video, args.out, _workdir(args, args.out), args.music, args.handle, args.max_impacts,
                          args.resolution, args.ai, not args.no_hook, args.original_audio, None, args.discipline,
                          args.voice_id, langs, args.burn, not args.no_extras, not args.no_motion, args.framing,
                          args.tts, args.style, args.kit, args.music_from, args.force))
    elif args.cmd == "fun":
        from .fun import fun
        texts = [tuple((t.split("/", 1) + [""])[:2]) for t in (args.texte or [])[:3]]
        print("→", fun(args.video, args.out, _workdir(args, args.out), texts or None, args.handle, args.ai,
                       True if args.ia else None, args.music))
    elif args.cmd == "voice-clone":
        from .narration import CONFIG, clone_voice
        print("voix créée :", clone_voice(args.samples, args.name), f"(enregistrée dans {CONFIG})")
    elif args.cmd == "thumbs":
        from .thumbs import analyze_folder
        dna = analyze_folder(args.folder, args.out)
        print(json.dumps({"style": dna["style"], "moyenne": dna["moyenne"]}, indent=2, ensure_ascii=False))
        print("→", args.out)
    elif args.cmd == "skills":
        from . import skillpack
        if args.skills_cmd == "pack":
            out, n = skillpack.pack(args.out)
            print(f"{n} skills → {out}")
        else:
            for sk in skillpack.install(args.zip, overwrite=args.overwrite):
                print(f"✔ {sk['name']} : {sk['description']}")
                if sk["scripts"]:
                    print(f"   ⚠ scripts à relire avant usage : {', '.join(sk['scripts'])}")
    elif args.cmd == "serve":
        from .server import serve
        serve(args.port, args.host, args.data)
    elif args.cmd == "watch":
        from .server import watch
        watch(args.in_dir, args.out_dir, args.mode, {"handle": args.handle})
    elif args.cmd == "talk":
        print("→", talk(args.video, args.out, _workdir(args, args.out), os.environ.get("ELEVENLABS_API_KEY"),
                        args.language, args.noise_db, args.min_silence))


if __name__ == "__main__":
    main()
