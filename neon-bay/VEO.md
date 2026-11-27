# Générer des plans de bande-annonce avec Google Veo

Les outils sont dans `tools/veo/` :

| Fichier | Rôle |
|---|---|
| `shots.json` | les 12 plans à générer (3 par pays), avec leurs prompts en anglais |
| `veo.js` | envoie chaque plan à Google, attend la vidéo et la télécharge dans `marketing/veo/` |
| `assemble.sh` | colle les plans, la vraie capture du jeu, un carton titre, un carton de fin et la musique dans une vidéo verticale 1080x1920 |

Le dossier `marketing/veo/` n'est pas envoyé sur Git (il est dans `.gitignore`), parce que les vidéos sont lourdes.

---

## 0. À lire avant de payer : où en est Veo en novembre 2026

Ce guide a été écrit le 21 novembre 2026. Ce qu'on a pu vérifier :

- Les modèles Veo de l'**API Gemini** (la clé gratuite de Google AI Studio) s'appelaient `veo-3.1-generate-preview`, `veo-3.1-fast-generate-preview` et `veo-3.1-lite-generate-preview`. Plusieurs sources indiquent que Google les a **arrêtés le 22 octobre 2026** sur l'API Gemini (une autre source parle du 14 novembre). Le remplaçant annoncé est **Gemini Omni Flash** (`gemini-omni-1.1-flash`, puis `gemini-omni-1.2-flash`), qui passe par une autre interface (l'« Interactions API ») et n'utilise donc pas les mêmes requêtes.
- Veo 3.1 reste disponible sur **Google Cloud** (Vertex AI, devenu « Gemini Enterprise Agent Platform ») sous les noms `veo-3.1-generate-001` et `veo-3.1-fast-generate-001`. Il faut alors un projet Google Cloud avec la facturation activée, pas une simple clé AI Studio.

C'est pour cela que `veo.js` sait parler aux deux :
- `--backend gemini` (par défaut) : clé `GEMINI_API_KEY`. Avant de dépenser quoi que ce soit, l'outil demande à Google si le modèle existe encore. S'il a disparu, il s'arrête avec un message clair.
- `--backend vertex` : projet Google Cloud (voir section 3 bis).

Les pages officielles de Google n'étaient pas accessibles depuis la machine qui a préparé l'outil. Les noms, paramètres et tarifs viennent des extraits de ces pages et de sites tiers qui les recopient. **Avant la première génération, ouvre les pages officielles (liste en bas du document) et vérifie le nom du modèle et le prix.**

---

## 1. Obtenir une clé (API Gemini)

1. Va sur <https://aistudio.google.com> et connecte-toi avec un compte Google.
2. Clique sur **Get API key**, puis **Create API key**. Choisis ou crée un projet.
3. **Active la facturation** sur ce projet (bouton « Set up billing »). Veo n'a pas d'offre gratuite : sans facturation, toutes les requêtes sont refusées.
4. Copie la clé. Ne la colle **jamais** dans un fichier du projet, dans un message ou dans Git.

Pour l'utiliser, tape-la dans le terminal juste avant la commande. Elle ne vit que dans cette fenêtre :

```bash
export GEMINI_API_KEY="colle-ta-clé-ici"
```

Conseil : dans la console Google Cloud, rubrique **Budgets et alertes**, fixe un budget (par exemple 20 €) avec une alerte par email.

---

## 2. Combien ça coûte

Google facture **à la seconde de vidéo produite**. Une vidéo bloquée par le filtre de sécurité n'est en principe pas facturée.

Tarifs relevés (dollars par seconde, vidéo avec son) :

| Modèle | 720p | 1080p | 4K |
|---|---|---|---|
| Veo 3.1 Fast (`…fast-generate…`) | 0,10 $ | 0,12 $ | 0,30 $ |
| Veo 3.1 Standard (`…generate…`) | 0,40 $ | 0,40 $ | 0,60 $ |
| Veo 3.1 Lite (API Gemini seulement) | 0,05 $ | 0,08 $ | - |
| Gemini Omni 1.2 Flash (remplaçant, non géré par `veo.js`) | environ 0,07 $ | | |

Sur Google Cloud, la vidéo **sans son** est moins chère. `shots.json` demande des plans muets (`"generateAudio": false`), puisque la musique est ajoutée au montage.

**Les 12 plans de `shots.json`** font 4 s (ville), 6 s (poursuite) et 4 s (personnage) par pays, soit **56 secondes** au total :

| Modèle | Par plan (4 à 6 s) | Les 12 plans |
|---|---|---|
| Veo 3.1 Fast 720p (réglage par défaut) | 0,40 à 0,60 $ | **5,60 $** (environ 5,20 €) |
| Veo 3.1 Standard 720p | 1,60 à 2,40 $ | 22,40 $ |
| Veo 3.1 Lite 720p | 0,20 à 0,30 $ | 2,80 $ |

Compte en pratique **le double** : un plan sur deux doit souvent être régénéré (visage raté, voiture qui se déforme). Prévois donc 10 à 12 $ en Fast, 45 $ en Standard.

L'outil affiche toujours le coût estimé et **demande confirmation** avant de lancer des générations payantes.

---

## 3. Les commandes

Toutes les commandes se lancent depuis le dossier `neon-bay/`.

**Voir ce qui serait envoyé, sans rien payer.** C'est le mode par défaut tant qu'il n'y a pas de clé :

```bash
node tools/veo/veo.js --dry-run
```

**Générer un seul plan pour tester** (commence toujours par là) :

```bash
export GEMINI_API_KEY="…"
node tools/veo/veo.js --only nb-ville
```

**Générer les 12 plans** (ceux déjà téléchargés sont sautés) :

```bash
node tools/veo/veo.js
```

Autres options :

| Option | Effet |
|---|---|
| `--only nb-ville,ma-perso` | seulement ces plans |
| `--aspect 16:9` | format paysage (YouTube) au lieu du vertical 9:16 |
| `--model veo-3.1-generate-preview` | changer de modèle |
| `--backend vertex` | passer par Google Cloud (voir 3 bis) |
| `--force` | régénérer un plan déjà présent |
| `--yes` | ne pas demander de confirmation |

Chaque génération prend en général 1 à 6 minutes. L'outil interroge Google toutes les 10 secondes. Les MP4 arrivent dans `marketing/veo/<id>.mp4`, avec un `rapport.json` qui dit ce qui a marché ou échoué.

**Monter la bande-annonce :**

```bash
# format court : 3 s max par plan IA, capture du jeu, musique libre de droits
bash tools/veo/assemble.sh -t 3 -m audio/ma-musique.mp3

# sans la capture du jeu, avec un autre titre
bash tools/veo/assemble.sh -G -T "NÉON BAY" -S "Bientôt sur ton téléphone"
```

Résultat : `marketing/bande-annonce-veo.mp4`, en 1080x1920 et 30 images/s, avec un son normalisé à -16 LUFS. Ordre du montage : carton titre, plans IA dans l'ordre de `shots.json`, vraie capture du jeu, carton « Le niveau 1 est gratuit ». Avec `-t 3`, 12 plans IA, la capture de 16 s et les cartons, la vidéo fait environ 58 s, la limite haute d'un format court.

### 3 bis. Passer par Google Cloud (si l'API Gemini n'a plus Veo)

1. Crée un projet sur <https://console.cloud.google.com>, active la facturation et l'API **Vertex AI**.
2. Installe Google Cloud CLI, puis connecte-toi : `gcloud auth login`.
3. Lance :

```bash
export VERTEX_PROJECT="identifiant-de-ton-projet"
node tools/veo/veo.js --backend vertex --only nb-ville
```

Le modèle utilisé est alors `veo-3.1-fast-generate-001` (réglable dans `shots.json`, champ `vertexModel`).

---

## 4. Ce qui peut mal tourner

| Message | Cause | Que faire |
|---|---|---|
| `GEMINI_API_KEY absente : passage automatique en --dry-run` | pas de clé dans le terminal | `export GEMINI_API_KEY="…"` |
| `HTTP 403` / clé refusée | clé fausse, ou facturation non activée | vérifier dans AI Studio |
| `n'existe pas (ou plus) sur l'API Gemini` | modèle retiré par Google | `--backend vertex` ou un autre `--model` |
| `quota atteint, nouvel essai dans…` | trop de requêtes d'un coup | l'outil attend et réessaie seul (4 fois) ; sinon relancer plus tard |
| `bloquée par le filtre de sécurité` | Google a jugé le prompt trop violent ou trop proche d'une personne réelle | adoucir le prompt dans `shots.json`, puis `--only <id>` |
| `Téléchargement refusé` | la vidéo a plus de 2 jours | la régénérer (Google ne garde les vidéos que 2 jours) |

Ce que Veo refuse ou rate souvent : la violence réaliste, le sang, les armes braquées sur quelqu'un, les célébrités, les marques et logos, le texte lisible (enseignes, plaques). Les prompts de `shots.json` les évitent déjà : poursuites, explosions de voitures, ambiance, personnages fictifs.

Règles pour écrire de nouveaux plans : jamais de nom de jeu existant ou d'éditeur, de ville réelle connue d'un autre jeu, de marque de voiture, de personne réelle.

---

## 5. L'honnêteté : ce que Veo a le droit de montrer

**Les images Veo ne sont pas des images du jeu.** Elles sont plus belles, plus réalistes, et rien de ce qu'elles montrent n'est jouable tel quel. Les présenter comme du gameplay, c'est de la publicité trompeuse :

- **Google Play** interdit les visuels de fiche qui ne représentent pas l'application réelle. Une vidéo trompeuse peut faire refuser ou retirer la fiche.
- **L'App Store** demande que les aperçus vidéo soient des captures de l'app elle-même. Une vidéo générée par IA y est refusée.
- **Meta, TikTok et Google Ads** sanctionnent les pubs dont le contenu ne correspond pas au produit, et demandent de signaler les contenus réalistes générés par IA.
- En France, la publicité trompeuse est une pratique commerciale interdite (Code de la consommation).

Bon usage :
- Veo pour un **teaser d'ambiance** (« bienvenue à Néon Bay »), une intro de vidéo, une miniature animée, un fond de page de vente.
- Toujours **montrer le vrai gameplay** dans la même vidéo. `assemble.sh` ajoute la capture du jeu et écrit par défaut « Images générées par IA, pas du gameplay » sur les plans Veo et « Gameplay réel » sur la capture. Garde ces mentions (`-L` les retire, ce qui est déconseillé).
- Sur les fiches store, **uniquement des captures du jeu** (`marketing/bande-annonce-verticale.mp4` et des captures d'écran).

---

## Sources

Pages officielles (à vérifier avant de payer) :
- Génération vidéo avec Veo 3.1, API Gemini : <https://ai.google.dev/gemini-api/docs/video> et <https://ai.google.dev/gemini-api/docs/veo>
- Gemini Omni Flash, le remplaçant : <https://ai.google.dev/gemini-api/docs/omni>
- Tarifs de l'API Gemini : <https://ai.google.dev/gemini-api/docs/pricing>
- Modèles retirés : <https://ai.google.dev/gemini-api/docs/deprecations>
- Référence Veo sur Vertex AI (paramètres `aspectRatio`, `durationSeconds` 4/6/8, `resolution` 720p/1080p/4k, `negativePrompt`, `personGeneration`, `generateAudio`, modèles `-001`) : <https://docs.cloud.google.com/vertex-ai/generative-ai/docs/model-reference/veo-video-generation>
- Annonce de Veo 3.1 dans l'API Gemini : <https://developers.googleblog.com/en/introducing-veo-3-1-and-new-creative-controls-in-the-gemini-api>
- Baisse de prix Veo 3 / Veo 3 Fast : <https://developers.googleblog.com/en/veo-3-and-veo-3-fast-new-pricing-new-configurations-and-better-resolution>
- Veo 3.1 Lite : <https://blog.google/innovation-and-ai/technology/ai/veo-3-1-lite/>

Sources tierces sur l'arrêt des modèles et les prix (à recouper) :
- <https://github.com/yincongcyincong/MuseBot/issues/70>
- <https://www.layer3labs.io/guides/gemini-model-deprecations>
- <https://www.developersdigest.tech/models/video-generation/google-gemini-api>
- <https://costgoat.com/pricing/google-veo>
- <https://ppl.studio/blog/veo-vs-gemini-omni-flash>
