# Coach Viral

Coach IA et studio vidéo pour les vidéos courtes (TikTok, Instagram Reels, YouTube Shorts). Application web installable sur téléphone (PWA), en français, avec des réponses et des voix aussi en portugais du Brésil et en anglais.

L'IA est Claude (`claude-opus-5-5`). Les vidéos sont fabriquées par le code (FFmpeg), sans logiciel payant. La clé de l'API reste sur le serveur.

## Les onglets

| Onglet | Ce qu'il fait |
|---|---|
| 💡 **Idées** | Idées de vidéos : accroche, script seconde par seconde, légende, hashtags |
| 🎬 **Studio** | Plusieurs points de départ (lien, fichier, sujet, face caméra) → une vidéo prête (détail ci-dessous) |
| 🎙️ **Voix** | Essai des voix, export MP3/WAV, **clonage de votre propre voix** avec consentement enregistré |
| 🎯 **Score** | Note de viralité sur 100, note par critère, corrections prioritaires, autres accroches |
| 📈 **Profil** | Analyse du compte à partir de captures d'écran, plan sur 7 jours |
| 🚀 **Publier** | Légendes adaptées à chaque plateforme, partage direct depuis le téléphone |

**Points de départ du Studio :**
- **Un lien** (TikTok, Instagram, YouTube) ou **un fichier** : l'IA analyse le style (format, visuel, texte, voix, rythme). Elle dit pourquoi la vidéo marche, puis écrit une **nouvelle version originale et améliorée** dans le même style.
- **Un sujet** : l'IA écrit directement la vidéo.
- **Face caméra** : votre vidéo reçoit des sous-titres mot à mot (le mot prononcé change de couleur) et des titres en boîte aux moments clés.
- **Images de référence** : l'IA mesure les couleurs, les tailles et les positions d'un style que vous aimez, et règle le modèle pour vous.

Le Studio fabrique ensuite la vidéo : images, voix off, musique de fond facultative et montage en 1080×1920. Vous téléchargez la vidéo et la voix off.

Les deux modèles de vidéo sont écrits en code :
- `lib/render.mjs`, modèle **citation** : image au centre qui zoome lentement, fond flou, texte blanc en haut et en bas, voix off, fondus enchaînés.
- `lib/captions.mjs`, modèle **face caméra** : sous-titres mot à mot et titres en boîte.

## Les voix (licences vérifiées)

| Moteur | Prix | Clonage | Vente autorisée ? | Machine |
|---|---|---|---|---|
| **Kokoro-82M** | gratuit | non | oui (Apache-2.0) | processeur ordinaire |
| **Chatterbox Multilingual** (Resemble AI) | gratuit | **oui**, à partir de 10 s de votre voix | oui (MIT) | carte graphique conseillée |
| **fal.ai** (Chatterbox hébergé) | environ 0,025 $ pour 1 000 caractères | oui | oui | aucune |
| **Edge TTS** | gratuit | non | **non** : usage personnel seulement | aucune |

Notes sur les voix :
- Edge TTS est retiré automatiquement quand la vente est activée (`VENTE=1`).
- Chatterbox ajoute un filigrane inaudible qui signale une voix générée.
- Le clonage exige de lire une phrase de consentement contenant un code, et de cocher une case. Seule votre propre voix est autorisée.
- XTTS-v2 et F5-TTS ont été écartés : leur licence interdit l'usage commercial.

## Ce qui n'est pas encore fait ou vérifié

- **Les vraies voix et la transcription n'ont pas été essayées ici** : leurs modèles se téléchargent depuis Hugging Face, inaccessible depuis l'environnement de développement. Le code suit l'API des paquets `kokoro` 0.7.16, `chatterbox-tts` 0.1.7 et `faster-whisper`, lue dans leur code source. Faites un premier essai après l'installation.
- **Les noms des champs de l'API fal.ai** (`text`, `audio_url`, `custom_audio_language`) ne sont pas confirmés. Ils se changent sans toucher au code avec `FAL_CHAMP_TEXTE`, `FAL_CHAMP_AUDIO` et `FAL_CHAMP_LANGUE`.
- **Les images des scènes** viennent de Pollinations (gratuit, sans clé), dont les conditions d'usage commercial sont à vérifier. Sinon, ajoutez vos propres images, scène par scène. Sans image, le studio met un fond dégradé.
- **Les liens TikTok ou Instagram** : les conditions de ces sites interdisent l'extraction automatique. Utilisez vos propres vidéos, ou téléversez le fichier.
- **La lecture automatique des statistiques et la publication automatique** demandent les accès officiels des plateformes, non obtenus.
- **L'image Docker n'a pas été construite** dans l'environnement de développement.

## Lancer en local

```bash
cd coach-viral
npm install
pip install yt-dlp faster-whisper kokoro soundfile   # + espeak-ng (apt/brew)
pip install chatterbox-tts                            # facultatif : clonage, avec carte graphique
export ANTHROPIC_API_KEY=sk-ant-...
npm start                                             # http://localhost:8080
```

Ou avec Docker : `docker build -t coach-viral . && docker run -p 8080:8080 -e ANTHROPIC_API_KEY=... -v $PWD/donnees:/data coach-viral`.

## Réglages (variables d'environnement)

| Variable | Rôle | Par défaut |
|---|---|---|
| `ANTHROPIC_API_KEY` | Clé de l'API Claude | — |
| `CODE_ACCES` | Code à saisir dans Réglages (usage personnel) | aucun |
| `VOIX_MOTEURS` | Moteurs proposés : `kokoro,chatterbox,fal,edge` | `kokoro,chatterbox,edge` |
| `FAL_KEY` | Clé fal.ai (clonage hébergé) | — |
| `IMAGES` | `pollinations` ou `aucun` | `pollinations` |
| `TRANSCRIPTION` | `0` pour ne pas transcrire l'audio | activée |
| `WHISPER_MODELE` | Taille du modèle de transcription | `small` |
| `DOSSIER_DONNEES` | Fichiers, voix, base des abonnés | `./donnees` |
| `RENDUS_SIMULTANES` | Vidéos fabriquées en même temps | 1 |
| `LIMITE_PAR_HEURE` | Demandes par adresse et par heure | 60 |

## Vendre à 1,99 € par mois

Mettez `VENTE=1`, puis renseignez les variables suivantes :

| Variable | Contenu |
|---|---|
| `STRIPE_SECRET_KEY` | Votre clé secrète Stripe |
| `STRIPE_PRIX` | L'identifiant du prix (un produit Stripe avec un prix récurrent de 1,99 €/mois) |
| `STRIPE_WEBHOOK_SECRET` | Le secret du point d'écoute (webhook) |
| `URL_PUBLIQUE` | L'adresse de votre site |

Dans Stripe, créez le point d'écoute `https://votre-site/api/stripe/webhook` pour les événements `customer.subscription.updated` et `customer.subscription.deleted`.

**Comment ça marche :**
- Le client paie sur la page Stripe. À son retour, l'application reçoit sa **clé d'abonnement** (visible dans Réglages, à copier pour un autre appareil).
- Il gère ou résilie son abonnement depuis le portail Stripe.
- Quotas par mois, réglables : 60 analyses (`QUOTA_ANALYSES`), 30 vidéos (`QUOTA_VIDEOS`), 60 essais de voix (`QUOTA_VOIX`).

**Ce qui reste pour un client à 1,99 € TTC :**

| Canal | Net estimé |
|---|---|
| Stripe (1,5 % + 0,25 € + Billing 0,7 %, TVA française déduite) | ≈ 1,37 € |
| App Store / Google Play (15 %) | ≈ 1,41 € |
| Paddle / Lemon Squeezy (5 % + 0,50 $) | ≈ 1,06 € : à éviter |

Un abonnement annuel (par exemple 19,99 €/an) réduit l'effet des frais fixes de Stripe.

**Coûts par client :** une analyse Claude avec images coûte quelques centimes, une voix clonée via fal.ai environ 0,02 $ par minute de voix. Les quotas protègent la marge. Surveillez vos coûts réels le premier mois.

**Obligations :** déclarer l'activité, gérer la TVA (guichet OSS pour les clients européens), publier des conditions générales de vente et une politique de confidentialité. Les voix clonées sont des données personnelles : supprimez-les sur demande (bouton « Supprimer ma voix »).

## Mettre en ligne

Le fichier `render.yaml` à la racine du dépôt déploie l'image Docker sur Render, avec un disque pour les données. Choisissez New > Blueprint sur render.com, puis remplissez les variables. Pour le clonage Chatterbox gratuit, il faut une machine avec carte graphique. Sinon, utilisez fal.ai.

## Tests

```bash
npm test                         # 24 tests : coach, rendu vidéo, sous-titres, voix, abonnement, studio (fausse IA)
node tests/smoke.mjs             # parcours navigateur : idées, score, profil, publier
node tests/smoke-studio.mjs      # parcours navigateur : studio, image de référence, voix
```

## Organisation

| Fichier | Rôle |
|---|---|
| `server.mjs` | Serveur : pages, accès, abonnement, studio, voix, file d'attente des fabrications |
| `lib/coach.mjs` | Consignes données à Claude et formats des réponses |
| `lib/studio.mjs` | Téléchargement, analyse de style, nouvelle version, style d'après une image, fabrication |
| `lib/render.mjs` | Modèle vidéo « citation » |
| `lib/captions.mjs` | Modèle « face caméra » (sous-titres mot à mot, titres en boîte) |
| `lib/voice.mjs` | Moteurs de voix, échantillon de clonage, consentement |
| `lib/billing.mjs` | Stripe, clés d'abonnement, quotas (SQLite) |
| `voix/*.py` | Kokoro, Chatterbox, transcription Whisper |
| `assets/fonts/` | Police Inter (licence OFL, incluse) |
| `web/` | Application (HTML, CSS, JavaScript) |
