# Second Souffle

Application web installable (PWA) pour reprendre le sport après 40 ans, sans douleur.
Français, anglais et portugais du Brésil. Aucun outil de compilation : du HTML, du CSS et du JavaScript.

## Ce qui fonctionne

- Bienvenue, choix de la langue et de l'ambiance (Second Souffle, Aube, Ardoise), clair et sombre
- Questionnaire en 3 étapes et carte du corps (zones sensibles)
- Séance de 5 mouvements composée selon les zones signalées, avec minuteur
- Contrôles de séance : précédent, suivant, refaire, pause, +10 s, sauter la pause, saut direct à un exercice
- Niveaux de durée (20, 30, 45, 60, 90 s), pause entre exercices, 1 à 3 tours, sons de décompte, écran maintenu allumé
- Retour de séance, semaine « de lumière » (une séance ou un repos choisi comptent), repos choisi
- Bibliothèque des 28 exercices à filmer (19 pour la version 1)
- Guide d'anatomie simplifié (calques muscles et os, zones cliquables)
- Objectifs (jusqu'à 3 parmi 8) qui orientent la séance, objectif de jours de lumière, suivi du poids facultatif
- Onglet Repas : repères alimentaires, cases du jour, idées de repas par langue
- Coach IA et coach privé (avec relais en cas de non-réponse), en démonstration
- Écran d'abonnement en démonstration
- Réglages : langue, ambiance, taille du texte, démonstrateur, effacement des données
- Données enregistrées sur l'appareil (localStorage), hors connexion après la première visite

## Ce qui est une démonstration

- Le **coach IA** répond avec des phrases écrites d'avance. Il faudra un serveur qui garde la clé de l'API.
- Le **coach privé** n'envoie aucun message. Il faudra un serveur, des comptes et un espace de gestion pour le responsable.
- L'**abonnement** ne fait aucun paiement. Les prix sont des propositions.
- Les **vidéos** des exercices sont des emplacements « Vidéo à tourner ».
- Les **textes en portugais** doivent être relus par une personne de langue maternelle brésilienne.
- Les **exercices et le guide d'anatomie** doivent être validés par un kinésithérapeute ou un enseignant en activité physique adaptée.
- **Léo**, le guide en illustration, n'est pas un vrai coach. Vérifiez les conditions d'usage commercial de l'outil qui a généré les images.

## Lancer en local

```bash
cd second-souffle-pwa
python3 -m http.server 8000      # puis ouvrir http://localhost:8000
node tests/logic.test.js         # tests de la logique
node tests/gemini.test.js        # tests du module Gemini (réservé au futur serveur), sans réseau
node tests/smoke.js              # parcours complet dans un navigateur (Playwright)
```

Le service worker ne fonctionne que sur `localhost` ou en HTTPS.

## Mettre en ligne

N'importe quel hébergement de fichiers statiques convient (GitHub Pages, Netlify, Cloudflare Pages).
Publiez le dossier `second-souffle-pwa` tel quel. En HTTPS, le navigateur propose « Ajouter à l'écran d'accueil ».
À chaque mise à jour des fichiers, changez `VERSION` dans `sw.js` pour renouveler le cache.

Pour un aperçu en une seule page : `python3 tools/build-artifact.py sortie.html`.

## Organisation

| Fichier | Rôle |
|---|---|
| `index.html` | Page unique |
| `css/styles.css` | Styles et ambiances (jeux de couleurs nommés) |
| `js/i18n.js` | Tous les textes, dans les trois langues |
| `js/data.js` | Exercices, zones, fiches du coach, anatomie |
| `js/logic.js` | Logique pure : séance, semaine, réponses, tri d'urgence |
| `js/gemini.js` | Requête et lecture de réponse de l'IA Gemini (fonctions pures, non utilisé par l'application : réservé au futur serveur du coach IA) |
| `js/app.js` | Écrans et actions |
| `sw.js`, `manifest.webmanifest` | Installation et hors connexion |
| `tests/logic.test.js`, `tests/gemini.test.js`, `tests/smoke.js` | Tests de la logique et parcours de bout en bout |
| `docs/avant-publication.md` | Revue et liste de contrôle avant publication |
| `docs/guide-tournage-posture.pdf`, `tools/build-guide.py`, `tools/print-pdf.js` | Guide de tournage et de posture (PDF de 25 pages) |
| `docs/production-data.json` | Fiches de tournage et scripts de voix off des 19 exercices (FR, EN, PT-BR) |
| `tools/build-production.py` | Génère la page « Dossier de tournage » |
| `docs/voiceover.json`, `docs/voiceover-manifest.csv` | Tous les textes de voix off (137 par langue) et le manifeste des fichiers audio |
| `tools/gen-voiceover.py`, `tools/voiceover_content.py` | Génèrent les fichiers de voix off à partir du contenu écrit |
| `tools/build-voiceover.py` | Génère la page « Voix off » |
| `tools/generer-audio.ps1` | Assistant Windows : pose les questions et lance la production des voix (clé en saisie masquée) |
| `tools/generate-audio.js` | Produit les fichiers audio (WAV) depuis le manifeste ; `--audition` compare des voix, `--dry-run` essaie sans clé |

## Prochaines étapes

1. Relecture du portugais et validation des exercices par un professionnel.
2. Serveur (clé de l'API du coach IA, messages du coach privé, comptes).
3. Voix off : générer les fichiers audio par langue et les enregistrer, plutôt que d'appeler le service à chaque séance.
4. Vidéos réelles, avec contrats de droit à l'image.
5. Modèle 3D d'anatomie : vérifier la licence avant de l'intégrer.
6. Publication sur le Play Store : à étudier (page enveloppée dans une application Android).
