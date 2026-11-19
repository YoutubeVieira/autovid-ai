# Dépôts GitHub open source utiles (2025-2026) : montage vidéo auto, publication, moteurs de jeu, publication sur les stores

> Notes de recherche du 19/11/2026 pour un créateur indépendant français (vidéos courtes automatisées + jeu navigateur three.js « Néon Bay » à publier sur web, Android et iOS).
>
> **Méthode et limites :**
> - Étoiles et licences relevées sur la page GitHub de chaque dépôt (via WebFetch) le 19/11/2026.
> - « Dernière activité » relevée dans les flux Atom GitHub (`releases.atom` ou `commits/<branche>.atom`) le même jour.
> - L'API GitHub (`gh`, api.github.com) était bloquée dans cette session, d'où des chiffres arrondis comme sur la page (ex. « 74,2k »).
> - Les domaines remotion.dev et developers.tiktok.com ne répondaient pas depuis la session. Pour Remotion, j'ai lu le LICENSE.md du dépôt. Pour TikTok, Instagram et YouTube, j'ai utilisé la recherche web, dont les extraits renvoient à la doc officielle.
> - Toute ligne marquée **[non vérifié]** vient de connaissances générales et n'a pas été confirmée par une source cette session.

## 1. Montage vidéo automatisé et génération de vidéos courtes

### Takeaway
La base solide est FFmpeg (rendu), avec MoviePy (Python) ou Remotion (React) pour composer, et faster-whisper ou WhisperX pour les sous-titres. Pour la voix française gratuite et locale, Piper (fork GPL actif) ou Kokoro (Apache-2.0, français supporté). Pièges de licence : Remotion devient payant au-delà de 3 salariés, et les poids XTTS-v2 sont non commerciaux.

### Cited Findings

**Moteurs de rendu / composition**

| Dépôt | Licence | Étoiles | Dernière activité | Rôle | Réserves |
|---|---|---|---|---|---|
| [FFmpeg/FFmpeg](https://github.com/FFmpeg/FFmpeg) (miroir) | LGPL/GPL (multiples) | ~67,6k | commit 19/11/2026 ([atom](https://github.com/FFmpeg/FFmpeg/commits/master.atom)) | Boîte à outils multimédia : encodage, découpe, sous-titres incrustés | Activer des modules GPL (ex. libx264) rend le binaire GPL : rien de gênant en ligne de commande, mais à surveiller si on le redistribue dans une app |
| [Zulko/moviepy](https://github.com/Zulko/moviepy) | MIT | ~15,2k | commit 26/08/2026 ([atom](https://github.com/Zulko/moviepy/commits/master.atom)) | Montage vidéo en Python | La v2 casse l'API de la v1 : beaucoup de tutos sont obsolètes. Le dernier commit visible porte sur l'alignement du tutoriel avec la v2 |
| [remotion-dev/remotion](https://github.com/remotion-dev/remotion) | **Licence Remotion (propriétaire, code source visible)** | ~74,2k | v4.0.545, 18/11/2026 ([atom](https://github.com/remotion-dev/remotion/releases.atom)) | Vidéos générées par code en React | Voir l'encadré licence plus bas |
| [redotvideo/revideo](https://github.com/redotvideo/revideo) | MIT | ~4,2k | commit 15/07/2026 ([atom](https://github.com/redotvideo/revideo/commits/main.atom)) | Fork de Motion Canvas orienté rendu « headless » par API (TypeScript) | Communauté petite. Une alternative MIT à Remotion |
| [motion-canvas/motion-canvas](https://github.com/motion-canvas/motion-canvas) | MIT | ~20,1k | dernière release v3.18.0-alpha.0, 16/02/2025 ([atom](https://github.com/motion-canvas/motion-canvas/releases.atom)) | Animations vectorielles en TypeScript, calées sur une voix off | Aucune release depuis février 2025. Pensé pour l'éditeur interactif plus que pour l'automatisation en masse |
| [WyattBlue/auto-editor](https://github.com/WyattBlue/auto-editor) | Unlicense (domaine public) | ~6,0k | v31.9.0, 14/11/2026 ([atom](https://github.com/WyattBlue/auto-editor/releases.atom)) | Coupe automatiquement les silences et les temps morts | Réécrit en Nim selon la page du dépôt. Exporte aussi vers Premiere, Resolve et FCP |

**Encadré licence Remotion** (source : [LICENSE.md](https://github.com/remotion-dev/remotion/blob/main/LICENSE.md)) :
- Gratuit pour un particulier, une entreprise à but lucratif de 3 salariés maximum, une association, ou pour une évaluation.
- Au-delà, une « Company License » est obligatoire. Le fichier ne donne pas de prix et renvoie à remotion.dev.
- Le fichier annonce : « In Remotion 5.0, the license will slightly change ». Au 18/11/2026, la version publiée est encore la 4.0.x.
- Conséquence : un créateur seul (auto-entrepreneur ou SASU sans salarié) entre dans la licence gratuite.
- Prix de la licence entreprise **[non vérifié]** (site inaccessible depuis la session).

**Sous-titres (reconnaissance vocale)**

| Dépôt | Licence | Étoiles | Dernière activité | Rôle | Réserves |
|---|---|---|---|---|---|
| [SYSTRAN/faster-whisper](https://github.com/SYSTRAN/faster-whisper) | MIT | ~26,9k | release 1.2.1, 31/10/2025 ([atom](https://github.com/SYSTRAN/faster-whisper/releases.atom)) | Whisper réimplémenté sur CTranslate2 : plus rapide, moins de mémoire | Pas de release depuis plus d'un an |
| [m-bain/whisperX](https://github.com/m-bain/whisperX) | BSD-2-Clause | ~25,5k | 3.8.7rc1, 26/06/2026 ([atom](https://github.com/m-bain/whisperX/releases.atom)) | Horodatage mot par mot (idéal pour les sous-titres « karaoké ») et diarisation | La diarisation demande un jeton Hugging Face et l'acceptation des conditions du modèle pyannote `speaker-diarization-community-1` (CC-BY-4.0) |
| [ggml-org/whisper.cpp](https://github.com/ggml-org/whisper.cpp) | MIT | ~55,3k | non relevé | Whisper en C/C++ (CPU, Apple Silicon) | — |

**Générateurs de vidéos courtes « tout-en-un »**

| Dépôt | Licence | Étoiles | Dernière activité | Rôle | Réserves |
|---|---|---|---|---|---|
| [harry0703/MoneyPrinterTurbo](https://github.com/harry0703/MoneyPrinterTurbo) | MIT | ~144,6k | v1.3.10, 07/11/2026 ([atom](https://github.com/harry0703/MoneyPrinterTurbo/releases.atom)) | Un sujet en entrée, une vidéo courte en sortie : script par LLM, images d'archive, TTS, sous-titres | LLM au choix (OpenAI, Claude, Gemini, DeepSeek, Ollama…). Images d'archive : Pexels, Pixabay, Coverr. TTS : Edge TTS gratuit, Azure, ElevenLabs… Rendu FFmpeg, sous-titres faster-whisper en option. Edge TTS passe par un service Microsoft non officiel. Le contenu générique d'archive risque d'être classé « contenu réutilisé / non original » par YouTube **[non vérifié]** |
| [RayVentura/ShortGPT](https://github.com/RayVentura/ShortGPT) | MIT | ~8,2k | dernier commit 10/02/2025 ([atom](https://github.com/RayVentura/ShortGPT/commits/stable.atom)) | Framework « expérimental » d'automatisation Shorts et TikTok | Semble à l'abandon : pas de commit depuis février 2025, 74 issues ouvertes |
| [FujiwaraChoki/MoneyPrinterV2](https://github.com/FujiwaraChoki/MoneyPrinterV2) | **AGPL-3.0** | ~32,5k | non relevé | Automatisation Shorts YouTube, Twitter, affiliation, avec planification cron | L'AGPL contamine les services déployés. Méthode d'upload des Shorts non précisée sur la page (Selenium probable **[non vérifié]**) |

**Synthèse vocale (TTS) open source**

| Dépôt | Licence | Étoiles | Dernière activité | Rôle | Réserves |
|---|---|---|---|---|---|
| [rhasspy/piper](https://github.com/rhasspy/piper) | MIT | ~11,3k | **archivé le 06/10/2025** | TTS neuronal local rapide | Le développement continue sur OHF-Voice/piper1-gpl |
| [OHF-Voice/piper1-gpl](https://github.com/OHF-Voice/piper1-gpl) | **GPL-3.0** | ~6,3k | v1.8.0, 04/09/2026 ([atom](https://github.com/OHF-Voice/piper1-gpl/releases.atom)) | Suite active de Piper | Passage de MIT à GPL. Voix françaises listées dans docs/VOICES.md (non consulté). Chaque voix a sa propre licence de modèle **[non vérifié]** |
| [hexgrad/kokoro](https://github.com/hexgrad/kokoro) | Apache-2.0 | ~10,2k | commit 06/08/2025 ([atom](https://github.com/hexgrad/kokoro/commits/main.atom)) | Bibliothèque d'inférence pour Kokoro-82M (léger) | Français supporté (code `'f'`, fr-fr). Peu de voix françaises et qualité moindre qu'en anglais **[non vérifié]** |
| [remsky/Kokoro-FastAPI](https://github.com/remsky/Kokoro-FastAPI) | Apache-2.0 | ~5,7k | non relevé | Serveur Docker pour Kokoro, compatible API OpenAI, avec légendes horodatées | — |
| [idiap/coqui-ai-TTS](https://github.com/idiap/coqui-ai-TTS) | MPL-2.0 (code) | ~2,4k | v0.28.0, 19/10/2026 ([atom](https://github.com/idiap/coqui-ai-TTS/releases.atom)) | Fork maintenu de Coqui TTS (XTTS, VITS…) | Les **poids XTTS-v2 sont sous Coqui Public Model License, non commerciale**. Coqui a fermé fin 2023 / début 2024 et plus personne ne vend de licence commerciale ([discussion coqui-ai/TTS #4145](https://github.com/coqui-ai/TTS/discussions/4145), [AIM](https://analyticsindiamag.com/deep-tech/conversational-ai-startup-coqui-shuts-down/), [HF XTTS-v2 #33](https://huggingface.co/coqui/XTTS-v2/discussions/33)). XTTS-v2 est donc à éviter sur une chaîne monétisée |

### Inferences
- Chaîne conseillée pour un indépendant :
  - script par LLM, puis voix (Piper FR, Kokoro, ou une voix cloud déjà en place) ;
  - faster-whisper ou WhisperX pour les horodatages mot à mot ;
  - composition avec Remotion (gratuit tant qu'on a 3 salariés ou moins) ou Revideo (MIT) ;
  - rendu final FFmpeg ;
  - auto-editor pour nettoyer les rushes parlés.
- MoneyPrinterTurbo est le générateur le plus populaire et le plus actif. Il vaut mieux s'en servir comme base de code ou comme source d'idées que comme usine à contenu « stock », que les plateformes repèrent facilement.
- Licences : MoneyPrinterV2 (AGPL) et piper1-gpl (GPL) sont sans risque en usage local, mais à éviter si on veut intégrer le code dans une app ou un SaaS propriétaire.

### Gaps
- Dates de dernière activité de whisper.cpp, MoneyPrinterV2 et Kokoro-FastAPI : non relevées.
- Prix actuel de la licence entreprise Remotion et contenu des changements de Remotion 5.0 : remotion.dev inaccessible.
- Liste et qualité des voix Piper françaises (ex. « siwis », « upmc ») et licences de chaque voix : non vérifiées.
- Autres TTS (F5-TTS, Fish Speech, Chatterbox…) : non examinés faute de budget.

## 2. Publication automatisée sur YouTube, TikTok et Instagram

### Takeaway
Les trois plateformes ont une API officielle. Chacune impose une **validation (audit) avant toute publication publique** : sans audit, les vidéos envoyées via YouTube ou TikTok restent privées. Postiz (AGPL, ~41,9k ⭐, très actif) est le planificateur auto-hébergé le plus complet, mais il faut créer ses propres applis développeur sur chaque plateforme. Les uploaders non officiels (navigateur automatisé + cookies) enfreignent les CGU et exposent le compte.

### Cited Findings

**YouTube Data API v3**
- [youtube/api-samples](https://github.com/youtube/api-samples) : ~6,0k ⭐, non archivé, exemples en Apps Script, .NET, Go, Java, JS, PHP, Python et Ruby.
  - Licence non affichée sur la page relevée (Apache-2.0 probable **[non vérifié]**).
  - Présence d'un exemple `upload_video.py` non confirmée sur la page **[non vérifié]**.
- [porjo/youtubeuploader](https://github.com/porjo/youtubeuploader) (Go, Apache-2.0, ~895 ⭐) passe par l'API officielle avec OAuth2 (`client_secrets.json`). Sa page indique :
  - quota par défaut d'environ « 6 vidéos par 24 h » ;
  - vidéos privées par défaut pour les projets non vérifiés créés après le 28/07/2020, jusqu'à l'audit Google.
- Quota : la page officielle [determine_quota_cost](https://developers.google.com/youtube/v3/determine_quota_cost) annonce historiquement 1600 unités par `videos.insert` sur 10 000 unités/jour, soit environ 6 envois par jour ([Google Groups](https://groups.google.com/g/google-cloud-dev/c/R_2wdYQj7Sw)).
  - Des sources secondaires affirment qu'en 2025-2026 Google aurait baissé ce coût (vers environ 100 unités) ou créé un compteur séparé pour `videos.insert` ([singhamandeep.com](https://singhamandeep.com/?p=1574), [postproxy.dev](https://postproxy.dev/blog/automate-youtube-uploads/)).
  - **Contradiction non résolue** : vérifier directement sur la page officielle.

**TikTok Content Posting API**
- Selon la référence officielle Direct Post ([developers.tiktok.com](https://developers.tiktok.com/doc/content-posting-api-reference-direct-post)), tout contenu publié par un client non audité est **limité à une visibilité privée**. Seul un audit de conformité lève cette limite.
- [Content Sharing Guidelines](https://developers.tiktok.com/docs/en/content-sharing-guidelines) :
  - un client non audité peut faire publier au maximum **5 utilisateurs par 24 h** ;
  - ces comptes doivent être en mode privé au moment de la publication.
- La validation d'appli (scope `video.publish`) et l'audit Content Posting sont deux étapes distinctes. Les posts faits avant l'audit ne redeviennent pas publics ensuite ([bundle.social](https://bundle.social/blog/tiktok-api-approval), [adaptlypost](https://adaptlypost.com/fr/blog/why-does-my-app-need-approval-post-tiktok)).
  - Délais d'audit cités : de quelques jours à 6 semaines. Ce sont des sources tierces qui se contredisent.
- Mode « Upload » (brouillon envoyé dans la boîte TikTok, que l'utilisateur finalise lui-même) : alternative à la publication directe **[non vérifié en doc officielle cette session]**.

**Instagram (API Graph / Instagram Platform)**
- La publication passe par des « containers ». Le quota officiel est de **50 publications via API par 24 h glissantes**, consultable via `GET /{ig-user-id}/content_publishing_limit` ([référence Meta](https://developers.facebook.com/docs/instagram-platform/instagram-graph-api/reference/ig-user/content_publishing_limit)).
- Certaines versions de la doc indiquent 100 ([Content Publishing](https://developers.facebook.com/docs/instagram-platform/content-publishing/)) : divergence à noter.
- Limite de 400 containers par 24 h, et chaque container expire après 24 h ([IG User Media](https://developers.facebook.com/docs/instagram-platform/instagram-graph-api/reference/ig-user/media)).
- Réservé aux comptes professionnels. Selon un guide tiers, les comptes Créateur ne seraient pas supportés : **à vérifier**, d'autres sources disent l'inverse ([bundle.social](https://bundle.social/blog/instagram-graph-api)).
- Le dépôt GitHub d'exemples officiels Instagram n'a pas été trouvé ni vérifié.

**Planificateurs open source**

| Dépôt | Licence | Étoiles | Dernière activité | Rôle | Réserves |
|---|---|---|---|---|---|
| [gitroomhq/postiz-app](https://github.com/gitroomhq/postiz-app) | **AGPL-3.0** | ~41,9k | v2.26.0, 13/11/2026 ([atom](https://github.com/gitroomhq/postiz-app/releases.atom)) | Planificateur multi-réseaux (Instagram, YouTube, TikTok, Facebook, LinkedIn, X, Threads, Pinterest, Bluesky…) | Auto-hébergement via Docker, avec Postgres, Redis et stockage. Il faut créer ses propres applis développeur et passer leur validation (donc l'audit TikTok aussi). Doc TikTok : [docs.postiz.com](https://docs.postiz.com/providers/tiktok) |
| [inovector/mixpost](https://github.com/inovector/mixpost) | MIT (version « Lite ») | ~3,9k | 2.6.0, 16/03/2026 ([atom](https://github.com/inovector/mixpost/releases.atom)) | Planificateur PHP/Laravel | Version Lite d'un produit payant (Pro/Enterprise). Réseaux couverts par la Lite non précisés sur la page. Peu actif en 2026 |

**Uploaders non officiels (risque CGU)**
- [wkaisertexas/tiktok-uploader](https://github.com/wkaisertexas/tiktok-uploader) (MIT, ~787 ⭐) : navigateur automatisé (Playwright/Selenium) avec réutilisation des cookies, qui « fait croire » à TikTok qu'on est connecté. L'auteur prévient que l'outil n'est « pas infaillible ».
- MoneyPrinterV2 automatise aussi l'upload de Shorts, méthode non précisée.
- Ces outils contournent l'API et enfreignent les conditions d'utilisation des plateformes sur l'automatisation non autorisée **[CGU non relues cette session]**. Risques : blocage de compte, perte de monétisation, casse à chaque changement d'interface.

### Inferences
- Pour un créateur solo, le chemin le plus sûr :
  - **YouTube** : une appli Google Cloud perso et un script officiel (Python `google-api-python-client` ou youtubeuploader). Demander l'audit pour les envois publics, ou envoyer en privé puis passer en public à la main.
  - **Instagram** : compte professionnel, puis API Graph.
  - **TikTok** : rester en publication manuelle ou en « brouillon » tant que l'audit n'est pas obtenu (un audit pour un usage personnel risque d'être refusé **[non vérifié]**).
- Postiz centralise tout, mais il ne contourne aucun audit : il en hérite.
- Autre option : un service tiers déjà audité (Buffer, Later, Metricool…). Hors périmètre open source, non évalué.

### Gaps
- Coût quota actuel exact de `videos.insert` et règle actuelle sur les vidéos privées non auditées : sources contradictoires, doc Google à relire.
- Critères d'audit TikTok (usage personnel accepté ? usage interne ?) : developers.tiktok.com inaccessible.
- Dépôt officiel d'exemples Instagram Graph : non identifié.

## 3. Moteurs de jeu web et mobiles

### Takeaway
three.js reste le choix naturel pour Néon Bay : MIT, ~118,9k ⭐, release r187 le 30/10/2026, mises à jour mensuelles. Babylon.js et PlayCanvas sont des alternatives 3D plus « moteur complet », Phaser pour la 2D. Godot (MIT) exporte nativement vers web, Android et iOS. Defold a une licence maison qui interdit de revendre le moteur, mais autorise les jeux commerciaux.

### Cited Findings

| Dépôt | Licence | Étoiles | Dernière activité | Rôle | Réserves |
|---|---|---|---|---|---|
| [mrdoob/three.js](https://github.com/mrdoob/three.js) | MIT | ~118,9k | r187, 30/10/2026 ; commit 19/11/2026 ([releases](https://github.com/mrdoob/three.js/releases.atom), [commits](https://github.com/mrdoob/three.js/commits/dev.atom)) | Bibliothèque 3D WebGL/WebGPU | Bibliothèque de rendu, pas un moteur complet : physique, audio et UI à ajouter. Ruptures d'API fréquentes entre versions rNNN, donc figer la version |
| [BabylonJS/Babylon.js](https://github.com/BabylonJS/Babylon.js) | Apache-2.0 | ~26,4k | 9.37.1, 18/11/2026 ([atom](https://github.com/BabylonJS/Babylon.js/releases.atom)) | Moteur 3D web complet (physique, GUI, éditeur) | Plus lourd que three.js |
| [playcanvas/engine](https://github.com/playcanvas/engine) | MIT | ~17,3k | v2.25.0-beta.9, 19/11/2026 ([atom](https://github.com/playcanvas/engine/releases.atom)) | Moteur 3D WebGL/WebGPU | L'éditeur en ligne PlayCanvas est un service commercial distinct du moteur MIT **[non vérifié]** |
| [phaserjs/phaser](https://github.com/phaserjs/phaser) | MIT | ~40,7k | Phaser v4.2.1, 09/07/2026 ([atom](https://github.com/phaserjs/phaser/releases.atom)) | Moteur 2D HTML5 | Phaser 4 change le pipeline de rendu, les filtres, le tint et l'éclairage (guide de migration v3 → v4) |
| [godotengine/godot](https://github.com/godotengine/godot) | MIT | ~120,4k | 4.7.2-stable, 22/08/2026 ([atom](https://github.com/godotengine/godot/releases.atom)) | Moteur 2D/3D complet avec export web, Android et iOS | L'export iOS demande macOS et Xcode **[non vérifié]**. L'export web de Godot 4 utilise des threads (SharedArrayBuffer et en-têtes COOP/COEP), avec une option sans threads selon les versions **[non vérifié]** |
| [defold/defold](https://github.com/defold/defold) | **Defold License 1.0** (source disponible, pas OSI) | ~6,5k | v1.14.2-alpha, 19/11/2026 ([atom](https://github.com/defold/defold/releases.atom)) | Moteur 2D/3D léger, très bon export HTML5 et mobile | [LICENSE.txt](https://github.com/defold/defold/blob/dev/LICENSE.txt), section 4(a) : interdit de commercialiser le moteur lui-même « as a Game Engine Product ». Les jeux faits avec Defold restent libres d'exploitation commerciale |
| [pixijs/pixijs](https://github.com/pixijs/pixijs) | — | — | — | Rendu 2D | **[non vérifié]**, non consulté |

### Inferences
- Rester sur three.js pour Néon Bay est cohérent : aucune contrainte de licence, écosystème énorme et activité quotidienne.
- Changer de moteur (Godot ou Babylon) ne vaudrait le coût que pour des outils intégrés (éditeur, physique) ou un export natif mobile plus performant qu'une WebView.
- Godot exporte en natif, ce qui écarte le risque de rejet Apple « simple site web emballé » (voir §4).

### Gaps
- Contraintes précises de l'export web de Godot 4.7 (threads, poids du build) et besoin de Mac pour iOS : non vérifiés cette session.
- PixiJS, Excalibur, react-three-fiber : non relevés.

## 4. Publier une appli web ou un jeu sur Google Play et l'App Store

### Takeaway
Capacitor (MIT, ~17,1k ⭐, v8.6.2 le 12/11/2026) est l'outil principal pour emballer le jeu three.js en appli Android et iOS. Bubblewrap ou PWABuilder (TWA) sont plus légers, mais ne visent qu'Android. Fastlane automatise signature et envoi aux stores. Tauri 2 sait aussi viser le mobile. Deux contraintes non techniques dominent :
- Google Play : test fermé de 12 testeurs pendant 14 jours pour les comptes personnels récents ;
- Apple : risque de rejet 4.2 (« Minimum Functionality ») pour les applis web emballées.

### Cited Findings

| Dépôt | Licence | Étoiles | Dernière activité | Rôle | Réserves |
|---|---|---|---|---|---|
| [ionic-team/capacitor](https://github.com/ionic-team/capacitor) | MIT | ~17,1k | 8.6.2, 12/11/2026 ([atom](https://github.com/ionic-team/capacitor/releases.atom)) | Emballe une appli web dans une WebView native Android/iOS, avec plugins natifs | La compilation iOS demande un Mac avec Xcode, ou un service CI macOS **[non vérifié]** |
| [GoogleChromeLabs/bubblewrap](https://github.com/GoogleChromeLabs/bubblewrap) | Apache-2.0 | ~3,2k | v1.27.0, 09/10/2026 ([atom](https://github.com/GoogleChromeLabs/bubblewrap/releases.atom)) | CLI qui génère une Trusted Web Activity (PWA vers APK/AAB Play) | Android uniquement. Demande une PWA valide (manifest, service worker) et la vérification Digital Asset Links **[non vérifié]** |
| [pwa-builder/PWABuilder](https://github.com/pwa-builder/PWABuilder) | MIT | ~3,8k | commit 17/11/2026 ([atom](https://github.com/pwa-builder/PWABuilder/commits/main.atom)) | Empaquette une PWA pour Google Play et le Microsoft Store | La page confirme les procédures Play et Microsoft Store. Le support iOS n'est suggéré que par un tag « app-store » : **[non vérifié]** |
| [fastlane/fastlane](https://github.com/fastlane/fastlane) | MIT | ~42,4k | 2.242.0, 16/11/2026 ([atom](https://github.com/fastlane/fastlane/releases.atom)) | Automatise build, signature, captures d'écran et envoi vers App Store Connect et Play Console | Ruby. S'utilise en complément de Capacitor |
| [tauri-apps/tauri](https://github.com/tauri-apps/tauri) | Apache-2.0 / MIT | ~113,0k | tauri v2.12.7, 18/11/2026 ([atom](https://github.com/tauri-apps/tauri/releases.atom)) | Applis desktop et mobiles (iOS 9+, Android 8+ selon le README) avec front web et back Rust | Écosystème de plugins mobiles plus jeune que celui de Capacitor **[non vérifié]** |
| [apache/cordova-android](https://github.com/apache/cordova-android) | Apache-2.0 | ~3,8k | 15.1.0, 22/07/2026 ([atom](https://github.com/apache/cordova-android/releases.atom)) | Ancêtre de Capacitor | Toujours maintenu (release en juillet 2026), mais Capacitor est son successeur recommandé par Ionic **[non vérifié]** |
| [apache/cordova-ios](https://github.com/apache/cordova-ios) | Apache-2.0 | ~2,2k | non relevé | Plateforme iOS de Cordova | — |

**Contraintes des stores**
- **Google Play** ([aide officielle](https://support.google.com/googleplay/android-developer/answer/14151465)) :
  - les comptes développeur **personnels créés après le 13/11/2023** doivent mener un test fermé avec **au moins 12 testeurs inscrits sans interruption pendant 14 jours** avant de demander l'accès à la production ;
  - Android Authority note que ce seuil est passé de 20 à 12 testeurs ([source](https://www.androidauthority.com/google-play-app-testing-requirement-3510580)) ;
  - les comptes « organisation » en seraient exemptés, mais il faut un numéro D-U-N-S ([dev.to](https://dev.to/theionproject/the-12-tester-rule-that-quietly-adds-two-weeks-to-your-first-google-play-launch-4bp3)).
- **Apple** : la règle 4.2 rejette les applis « pas assez différentes d'une navigation web ».
  - Des développeurs Capacitor rapportent des rejets 4.2, même avec des plugins natifs (géolocalisation, presse-papiers) ([forum Apple](https://developer.apple.com/forums/thread/812889), [retour d'expérience](https://scribe.disroot.org/post/7369014)).
  - Les relecteurs testeraient le mode avion : une page d'erreur navigateur trahit le wrapper ([capgo](https://capgo.app/blog/how-to-pass-app-store-review-2026/), avis d'éditeur).
  - Aucune source trouvée sur l'application de la règle 4.2 aux **jeux**.

### Inferences
- Pour Néon Bay :
  - **Web** : PWA (manifest + service worker) pour jouer hors ligne.
  - **Android** : Capacitor (ou Bubblewrap si la PWA suffit). Prévoir environ 3 semaines pour le test fermé 12 × 14 jours.
  - **iOS** : Capacitor + fastlane.
- Atouts à soigner pour éviter le rejet 4.2 :
  - jeu entièrement embarqué et jouable hors ligne (assets dans l'app, pas d'URL distante) ;
  - retour haptique et Game Center ou achats intégrés via plugins.
- Un jeu complet et autonome est généralement moins visé qu'un « site emballé », mais cela reste à confirmer **[inférence]**.
- Cordova n'a plus d'intérêt pour un nouveau projet face à Capacitor. Tauri mobile est viable, mais moins éprouvé pour un jeu WebGL.

### Gaps
- Exigences actuelles de SDK cible Play (target API level 2026) et version minimale de Xcode : non vérifiées.
- Support iOS réel de PWABuilder (paquet Xcode) : non confirmé.
- Performance WebGL/WebGPU dans la WebView Android et dans WKWebView pour un jeu three.js : non étudiée.
- capacitorjs.com non consulté : domaine non testé, budget d'appels épuisé.
