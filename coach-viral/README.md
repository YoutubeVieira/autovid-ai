# Coach Viral

Coach IA et studio vidéo pour les vidéos courtes (TikTok, Instagram Reels, YouTube Shorts). Application web installable sur téléphone (PWA), en français, avec des réponses et des voix aussi en portugais du Brésil et en anglais.

L'IA est Claude (`claude-opus-5-5`). Les vidéos sont fabriquées par le code (FFmpeg), sans logiciel payant. La clé de l'API reste sur le serveur.

## Les onglets

| Onglet | Ce qu'il fait |
|---|---|
| 💡 **Idées** | Idées de vidéos : accroche, script seconde par seconde, légende, hashtags. **Radar de tendances** : un bot cherche chaque jour ce qui monte dans vos niches |
| 🎬 **Studio** | Plusieurs points de départ (lien, fichier, sujet, face caméra) → une vidéo prête (détail ci-dessous) |
| 🎙️ **Voix** | Essai des voix, export MP3/WAV, **clonage de votre propre voix** avec consentement enregistré |
| 🎯 **Score** | Note de viralité sur 100, note par critère, corrections prioritaires, autres accroches |
| 📈 **Profil** | Analyse du compte à partir de captures d'écran, plan sur 7 jours |
| 🚀 **Publier** | Légendes adaptées à chaque plateforme, partage direct depuis le téléphone |

**Points de départ du Studio :**
- **Un lien** (TikTok, Instagram, YouTube) ou **un fichier** : l'IA analyse le style (format, visuel, texte, voix, rythme). Elle dit pourquoi la vidéo marche, puis écrit une **nouvelle version originale et améliorée** dans le même style.
- **Un sujet** : l'IA écrit directement la vidéo.
- **Face caméra** : votre vidéo reçoit des sous-titres mot à mot (le mot prononcé change de couleur) et des titres en boîte aux moments clés.
- **Clips** (comme OpusClip) : une vidéo longue (live, podcast, cours) → les meilleurs moments, découpés en clips verticaux avec sous-titres et titre.
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

## Le radar de tendances (bot)

Pour chaque niche (5 au maximum, réglées dans l'onglet Idées), le bot :

1. **cherche des signaux de la semaine :**
   - la recherche web de Claude : actualités, défis, sons, questions fréquentes, événements à venir ;
   - les YouTube Shorts les plus vus (gratuit avec une clé `YOUTUBE_API_KEY`) ;
   - les posts Reddit les plus votés (gratuit) ;
2. **propose 5 à 8 thèmes à filmer**, chacun avec une note de potentiel, le niveau de concurrence, 3 accroches et les sources ;
3. **ne repropose pas** les thèmes des 10 derniers passages.

Un bouton « Créer la vidéo » envoie le thème au Studio.

**Quand il tourne :**
- à la demande, avec le bouton « Chercher les tendances » ;
- chaque jour à `RADAR_HEURE` si le serveur reste allumé ;
- chaque matin grâce au robot GitHub `.github/workflows/coach-viral-radar.yml`, qui réveille le serveur même s'il est en veille. Réglez les secrets `COACH_URL` et `RADAR_JETON` dans GitHub.

## Les robots de test

`.github/workflows/coach-viral-tests.yml` lance tous les tests, puis les deux parcours dans un vrai navigateur :
- à chaque modification ;
- chaque nuit, pour repérer une dépendance qui casse.

Les captures d'écran sont jointes au résultat. Sur un dépôt privé, GitHub offre 2 000 minutes par mois, et un passage dure quelques minutes.

## Combien ça coûte vraiment

**L'abonnement Claude (claude.ai Pro ou Max) ne couvre pas l'application.** L'application appelle l'API Claude, facturée à part sur console.anthropic.com, avec des crédits prépayés.

| Poste | Coût |
|---|---|
| API Claude (`claude-opus-5-5` : 4 $ par million de jetons en entrée, 20 $ en sortie) | ≈ 0,05 à 0,15 $ par analyse, idée, score ou vidéo écrite |
| Recherche web du radar | 10 $ pour 1 000 recherches, soit ≈ 0,05 $ par niche et par passage, plus les jetons |
| Radar quotidien, 3 niches | ≈ 5 à 10 $ par mois (moins en hebdomadaire, ou avec `RADAR_WEB=0`) |
| Hébergement | 0 € sur votre ordinateur ; un serveur toujours allumé avec disque coûte quelques dollars par mois (offre gratuite de Render trop petite pour les voix) |
| Voix Kokoro, transcription Whisper, YouTube, Reddit, polices | 0 € |
| Clonage Chatterbox sur votre carte graphique | 0 € ; via fal.ai ≈ 0,02 $ par minute de voix |
| Images Pollinations | 0 € (conditions commerciales à vérifier) |
| Stripe | seulement sur les ventes (≈ 0,29 € par abonnement à 1,99 €) |

En usage personnel (≈ 50 actions par mois et un radar quotidien sur 3 niches), comptez environ 10 à 20 $ par mois d'API Claude. Pour dépenser moins, `COACH_MODEL=claude-sonnet-5-5` divise environ par deux le prix des jetons, et `claude-haiku-5-5` le divise par environ 40, avec une qualité moindre. Fixez une limite de dépense dans la console Anthropic.

## Installer sur un PC Windows (gratuit)

Dans PowerShell :

```powershell
irm https://raw.githubusercontent.com/YoutubeVieira/autovid-ai/ccr-ee8a77f1-5c7kmx/coach-viral/installer/installer.ps1 | iex
```

**Clonage de votre voix (Chatterbox, gratuit), en option :**

```powershell
irm https://raw.githubusercontent.com/YoutubeVieira/autovid-ai/ccr-ee8a77f1-5c7kmx/coach-viral/installer/ajouter-chatterbox.ps1 | iex
```

Chatterbox s'installe dans un environnement Python séparé, car il impose torch 2.6.0. Avec une carte NVIDIA, il prend quelques secondes par phrase ; sans, il est lent mais il fonctionne.

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
| `COACH_MODEL` | Modèle Claude | `claude-opus-5-5` |
| `RADAR_NICHES` | Niches de départ, séparées par `;` | — |
| `RADAR_HEURE` | Heure du passage quotidien du radar (0-23) | désactivé |
| `RADAR_JETON` | Jeton secret pour le robot GitHub qui lance le radar | — |
| `RADAR_WEB` | `0` pour couper la recherche web (radar gratuit, moins précis) | activée |
| `YOUTUBE_API_KEY` | Clé gratuite YouTube Data API | — |

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
npm test                         # 31 tests : coach, rendu vidéo, sous-titres, voix, abonnement, studio, radar, clips (fausse IA)
node tests/smoke.mjs             # parcours navigateur : idées, score, profil, publier
node tests/smoke-studio.mjs      # parcours navigateur : radar, studio, image de référence, clips, voix
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
| `lib/radar.mjs` | Radar de tendances (web, YouTube, Reddit → thèmes) |
| `lib/billing.mjs` | Stripe, clés d'abonnement, quotas (SQLite) |
| `voix/*.py` | Kokoro, Chatterbox, transcription Whisper |
| `assets/fonts/` | Police Inter (licence OFL, incluse) |
| `web/` | Application (HTML, CSS, JavaScript) |
