# Coach Viral

Coach IA pour les vidéos courtes (TikTok, Instagram Reels, YouTube Shorts). Application web installable sur téléphone (PWA), en français, avec des réponses possibles en portugais du Brésil ou en anglais.

L'IA utilisée est Claude (modèle `claude-opus-5-5`). La clé de l'API reste sur le serveur, jamais dans le téléphone.

## Ce qui fonctionne

| Onglet | Ce que fait le coach |
|---|---|
| **Idées** | Idées de vidéos selon votre niche : accroche, texte à l'écran, script seconde par seconde, appel à l'action, légende et hashtags |
| **Score** | Vous choisissez une vidéo. Le téléphone en extrait 6 images (la vidéo elle-même n'est pas envoyée). Le coach donne une note sur 100, une note sur 10 par critère (accroche, texte à l'écran, rythme…), les 3 corrections prioritaires et 3 autres accroches. Historique des scores sur l'appareil |
| **Profil** | Vous envoyez des captures d'écran de votre profil et de vos statistiques, ou vous collez vos chiffres. Le coach donne vos forces, vos faiblesses, les formats conseillés et un plan sur 7 jours |
| **Publier** | Le coach adapte le titre, la légende et les hashtags pour chaque plateforme. Sur téléphone, « Partager » ouvre TikTok, Instagram ou YouTube avec la vidéo, et la légende est copiée |

Autres points :

- Réglages : langue des réponses, thème clair ou sombre, code d'accès.
- L'interface reste disponible hors connexion, mais l'IA a besoin d'Internet.

## Ce qui n'est pas encore fait

- **Lecture automatique des statistiques TikTok ou Instagram.** Il faut l'accès officiel de chaque plateforme (TikTok for Developers, Meta). L'application doit être validée par la plateforme, ce qui prend plusieurs semaines. En attendant, les captures d'écran donnent les mêmes chiffres.
- **Publication 100 % automatique.** Elle demande aussi ces accès officiels (TikTok Content Posting API, Instagram Graph API, YouTube Data API) et des comptes utilisateurs sur le serveur. Pour l'instant, la publication se fait en deux gestes avec le bouton « Partager ».
- **Le son de la vidéo n'est pas analysé.** Collez le texte prononcé dans « Ce qui est dit » pour une meilleure analyse.
- **Les scores sont des estimations** fondées sur les bonnes pratiques connues. Personne ne peut garantir qu'une vidéo deviendra virale.

## Lancer en local

```bash
cd coach-viral
npm install
export ANTHROPIC_API_KEY=sk-ant-...   # votre clé, sur https://console.anthropic.com
npm start                              # puis ouvrir http://localhost:8080
```

Variables facultatives :

| Variable | Rôle | Par défaut |
|---|---|---|
| `CODE_ACCES` | Code à saisir dans Réglages pour utiliser l'IA. Il évite que des inconnus utilisent votre clé | aucun |
| `LIMITE_PAR_HEURE` | Nombre de demandes à l'IA par adresse et par heure | 30 |
| `PORT` | Port du serveur | 8080 |
| `COACH_MODEL` | Modèle Claude | `claude-opus-5-5` |

## Mettre en ligne

Il faut un hébergement qui fait tourner Node.js 20 ou plus (Render, Railway, Fly.io…). GitHub Pages ne suffit pas, car il faut un serveur pour garder la clé.

Avec Render, le fichier `render.yaml` à la racine du dépôt fait la configuration :

1. Sur render.com, choisissez **New > Blueprint**, puis ce dépôt.
2. Renseignez `ANTHROPIC_API_KEY` et `CODE_ACCES` quand Render les demande.
3. Ouvrez l'adresse en HTTPS sur votre téléphone, puis « Ajouter à l'écran d'accueil ».

À chaque mise à jour des fichiers de `web/`, changez `VERSION` dans `web/sw.js`.

## Coût

Chaque analyse est un appel payant à l'API Claude. Une analyse avec 6 images coûte quelques centimes. Les tarifs à jour sont sur la page de prix d'Anthropic.

## Tests

```bash
npm test               # serveur et demandes à l'IA, sans réseau (fausse IA)
node tests/smoke.mjs   # parcours complet dans un navigateur (Playwright), avec une vraie vidéo
```

## Organisation

| Fichier | Rôle |
|---|---|
| `server.mjs` | Serveur : pages, vérification des entrées, code d'accès, limite de débit, erreurs |
| `lib/coach.mjs` | Consignes données à l'IA et format des réponses |
| `web/` | Application (HTML, CSS, JavaScript, sans outil de compilation) |
| `web/js/media.js` | Extraction des images de la vidéo et réduction des captures, dans le navigateur |
| `tests/` | Tests |
