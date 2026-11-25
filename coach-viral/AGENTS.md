# Consignes pour les agents IA (Antigravity, Claude Code, Codex…)

Coach Viral : coach IA et studio vidéo pour vidéos courtes. Interface et textes en **français**, réponses de l'IA en FR / PT-BR / EN.

## Travail à plusieurs (Claude Code + Antigravity)

Plusieurs assistants modifient ce projet. **Avant de commencer, lisez `JOURNAL.md`** (ce qui a été fait, ce qui reste à faire, qui fait quoi),
faites `git pull` sur la branche `ccr-ee8a77f1-5c7kmx`, et **à la fin ajoutez une entrée dans `JOURNAL.md`** puis `git commit` et `git push`.

## Lancer

```bash
cd coach-viral
npm install
IA=gemini GEMINI_API_KEY=... npm start      # ou ANTHROPIC_API_KEY=... pour Claude
```

Sous Windows : `installer/installer.ps1` installe tout ; `installer/lancer.ps1` démarre le serveur et le tunnel Cloudflare.
Dépendances système : Node 22.5+, FFmpeg, Python 3.12 (`voix/*.py` : Kokoro, Chatterbox, faster-whisper).

## Tester (obligatoire avant chaque commit)

```bash
npm test                      # 41 tests, sans réseau (fausse IA)
node tests/smoke.mjs          # parcours navigateur (Playwright)
node tests/smoke-studio.mjs   # radar, studio, clips, voix
```

## Organisation

- `server.mjs` : routes HTTP, accès, quotas, file d'attente des fabrications.
- `lib/coach.mjs` : consignes et formats (zod) des réponses ; `ask()` choisit Claude ou Gemini.
- `lib/gemini.mjs` : client Gemini REST (responseJsonSchema).
- `lib/studio.mjs` : analyse de vidéo, nouvelle version, style d'après image, clips.
- `lib/render.mjs` (modèle citation) et `lib/captions.mjs` (face caméra) : rendu FFmpeg 1080x1920.
- `lib/voice.mjs` : moteurs de voix ; `lib/voiceworker.mjs` + `voix/serveur_voix.py` : serveur de voix permanent ; `lib/gallery.mjs` : « Mes vidéos » ; `lib/radar.mjs` : tendances ; `lib/billing.mjs` : Stripe.
- `web/` : PWA sans compilation (HTML/CSS/JS). Changer `VERSION` dans `web/sw.js` à chaque modification de `web/`.

## Règles

- Pas de chemin absolu dans un filtre FFmpeg : travailler dans un dossier temporaire avec des noms relatifs (compatibilité Windows).
- Toute réponse de l'IA passe par un schéma zod ; ajouter un test pour chaque nouveau format.
- Ne jamais copier les vidéos, textes ou marques d'autres créateurs : le studio écrit des versions originales.
- Voix clonée : uniquement la voix de l'utilisateur, avec la phrase de consentement.
- Ne jamais écrire de clé API dans le code, les tests ou les commits.
