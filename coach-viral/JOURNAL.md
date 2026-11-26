# Journal de travail partagé

Ce fichier sert de carnet de bord commun aux assistants qui travaillent sur Coach Viral
(Claude Code dans le cloud, l'assistant d'Antigravity sur le PC, ou tout autre).
**Chacun lit ce fichier avant de commencer et y ajoute une entrée quand il a fini.**
Les entrées les plus récentes sont en haut.

## Comment travailler à plusieurs

1. Avant de commencer : `git pull` sur la branche `ccr-ee8a77f1-5c7kmx`, puis lire ce journal et `AGENTS.md`.
2. Faire une seule chose à la fois, avec ses tests (`npm test`).
3. À la fin : ajouter une entrée ci-dessous (fait / vérifié / pas vérifié / à faire), `git commit`, puis `git push`.
4. Si un `git push` est refusé : `git pull` (fusion), relancer `npm test`, puis repousser. Ne jamais forcer (`--force`).
5. Une tâche prise : l'écrire dans « À faire » avec son nom (« en cours : Antigravity ») pour éviter de travailler à deux sur la même chose.

---

## 2026-11-26 — Claude Code (cloud)

**Fait**
- Fiche Play Store (`store/`) : icône 512, bannière 1024×500, 6 captures 1080×1920 tirées de l'application (`node store/generer-visuels.mjs`),
  textes FR / PT-BR / EN dans `store/textes.json` (longueurs vérifiées).

**À faire avant publication** (détail dans `store/README.md`)
- Serveur en ligne permanent (HTTPS, adresse fixe), paquet Android (Bubblewrap / PWABuilder), compte Google Play.
- Paiement : Google Play Billing ou programme de facturation alternative (Stripe seul non autorisé en principe dans une appli Play).
- Politique de confidentialité, formulaire Sécurité des données, bouton « Signaler » sur les contenus IA.

---

## 2026-11-25 — Claude Code (cloud)

**Fait**
- Serveur de voix permanent (`voix/serveur_voix.py`, `lib/voiceworker.mjs`) : Kokoro et Chatterbox restent chargés en mémoire au lieu de se recharger à chaque phrase. Retour automatique à l'ancien script si le serveur ne démarre pas (`VOIX_SERVEUR=0` pour le couper).
- Galerie « Mes vidéos » (`lib/gallery.mjs`, onglet Studio) : vidéos gardées 30 jours en usage personnel (`CONSERVATION_JOURS`), visibles après un redémarrage, supprimables.
- Raccourci « Mettre à jour Coach Viral » sur le Bureau.
- Transcription Whisper sous Windows : lecture du WAV par soundfile au lieu de PyAV (erreur `metadata_errors` relevée par le robot Windows).
- Code d'accès : plus demandé sur le PC lui-même ; demandé par une fenêtre sur le téléphone ; lien avec `?code=`.

**Vérifié**
- 41 tests (`npm test`) et les deux parcours navigateur.
- Robot Windows réel (`.github/workflows/coach-viral-windows.yml`), passages n°4 et n°5 **entièrement verts** :
  installation, Chatterbox, voix Kokoro FR/PT et Edge, vidéo citation, transcription Whisper + sous-titres, clonage Chatterbox.
- Serveur de voix permanent mesuré sur Windows (n°4 sans → n°5 avec, machines différentes donc à prendre comme ordre de grandeur) :
  Kokoro 1re phrase 120 s → 36 s ; Kokoro phrase suivante 12 s → 6 s ; vidéo citation 30 s → 24 s ; clonage Chatterbox 91 s → 82 s ;
  étape d'essais complète 4 min 34 → 2 min 49.

**Pas vérifié**
- Appels réels à Gemini (ajouter le secret `GEMINI_API_KEY` sur GitHub pour que le robot le teste).

**À faire (idées)**
- Musique de fond libre de droits intégrée (bibliothèque locale gratuite).
- Sous-titres synchronisés avec la voix dans le modèle citation.
- Modèle « avant / après » et modèle « liste top 3 » pour la niche capoeira / sport.
