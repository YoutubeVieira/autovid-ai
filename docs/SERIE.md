# Série « Le monde se peuple » - méthode et monétisation

## Principe
Chaque épisode (25 à 30 s) ajoute des habitants au monde. **La quantité d'habitants et qui ils sont viennent des commentaires** (« Prénom, métier »). Épisode 1 : *La fin des dinosaures* (le monde est vide). Épisode 2 : *Les premiers habitants*, etc. Le monde est un registre persistant (`monde/etat.json`) : les habitants des épisodes précédents sont toujours là.

## Fabriquer un épisode (≈ 15 min de travail + rendu)
1. Coller les commentaires dans un fichier texte (une ligne par spectateur : `Léa, boulangère`).
2. `python3 monde/monde.py ajouter --episode N --titre "..." --commentaires fichier.txt` → `monde/episodes/epNN/script.txt` (voix off calée pour 25-30 s, carton de fin compris), `episode.json` (qui, métier, apparence, expression de visage), liste des commentaires écartés.
3. Voix : `python3 packs/voices/tts.py monde/episodes/epNN/script.txt --out voix/ --engine supertonic --speaker 9 --speed 1.05` (voir `docs/VOIX.md` pour les 15 voix).
4. Scènes 3D : `python3 blender/blocky/episode_monde.py -- --spec monde/episodes/epNN/episode.json --voice voix/ --out frames/` (≈ 4-6 s par image sur 4 cœurs).
5. Montage : `python3 -m autoeditor run frames/ --preset monde_tiktok --events frames/events.json --audio voix/voice.wav --srt voix/voice.srt --out-dir out/`.
6. Correcteur : `python3 -m autoeditor check out/final.mp4 --preset monde_tiktok --duree 25 30` (puis `fix` si besoin).
7. `python3 monde/monde.py etat` pour voir où en est le monde et le prochain palier (15 conseillers, 100 habitants = élection du maire).

Vie privée : seul le **prénom** est utilisé (pas de pseudo, lien, e-mail ni numéro), les insultes sont écartées, aucun genre n'est deviné d'après un prénom, les habitants sont déjà ajoutés une seule fois. Demande l'accord des spectateurs (mention « en commentant tu acceptes d'apparaître dans la série »).

## Monétisation : ce qu'il faut savoir (à reverifier, ces règles changent souvent)
- **TikTok Creator Rewards** (le programme qui paie à la vue) demande, d'après ce que je sais, des vidéos **de plus d'une minute**, un compte avec un nombre minimal d'abonnés et de vues récentes et un pays éligible. **Des épisodes de 25-30 s ne sont donc probablement pas éligibles à ce programme.** Vérifie les conditions actuelles dans l'application (Paramètres > Creator Rewards).
- Stratégie : épisodes de 25-30 s pour **grandir** (abonnés, commentaires = habitants), puis un **« résumé de saison » de plus d'une minute** (3-4 épisodes assemblés) pour les revenus à la vue. Ajouter aussi : cadeaux en direct, partenariats, TikTok Shop, version YouTube Shorts (conditions d'abonnés et de vues différentes) ou compilations longues.
- Contenu original : tout est généré par scripts (personnages, décors, sons, musiques). **Étiquette « contenu généré par IA »** si TikTok la demande pour la voix synthétique.
- Licences : voix `siwis` (mention obligatoire, CC BY 4.0) et Supertonic (modèle OpenRAIL-M d'après tes notes) : à reverifier ; voix `tom` (AGPLv3) à éviter en monétisation sans vérification. Sons et musiques du dépôt : CC0, synthétisés. Aucune musique commerciale de TikTok dans le fichier : l'ajouter dans l'application si besoin.
- Ne jamais présenter un faux chiffre d'abonnés comme réel ; les habitants affichés doivent correspondre à de vrais commentaires (l'exemple `exemple_commentaires.txt` est fictif).

## Après : en fonction du nombre d'abonnés
- < 1 000 : 3 épisodes par semaine, objectif palier « 15 conseillers » ; chercher l'engagement (commentaires) plutôt que les revenus.
- 1 000 - 10 000 : ajouter le résumé de saison de plus d'une minute, tester les voix d'enfants/animaux pour les habitants.
- > 10 000 : candidater aux programmes de revenus, planifier l'élection du maire (100 habitants) comme épisode événement.
