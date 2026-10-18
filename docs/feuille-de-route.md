# Ce qu'il manque pour une machine à contenus monétisable

Classé par impact sur les vues et les revenus. ✅ = fait, 🟡 = partiel, ❌ = à faire.

## 1. Qualité du contenu (ce qui fait les vues)
| | Élément | État |
|---|---|---|
| ✅ | Analyse auto : coups, ralentis, flash, arrêts sur image, membres colorés, articulations, angles, anatomie | fait |
| ✅ | Risques de blessure + placement à chaque analyse | fait (modèles + `--ai claude`) |
| ✅ | Voix off avec ta voix clonée, termes capoeira prononcés en portugais | code fait, **non testé ici faute de clé ElevenLabs** |
| ✅ | Sous-titres FR incrustés + pistes FR / PT-BR / EN + fichiers .srt | FR fait ; PT/EN demandent Claude (`ANTHROPIC_API_KEY`) |
| 🟡 | Vocabulaire capoeira | noms par règles (aú, esquiva, meia-lua…) ; la vraie reconnaissance (armada vs queixada vs bênção) demande `--ai claude` ou un modèle entraîné sur tes vidéos |
| ❌ | **Rendu 4K natif** : aujourd'hui le compositing se fait en 1080p puis agrandi (lanczos). Pour une vraie 4K il faut paramétrer toutes les tailles (×2) | ~1 jour de travail ; rendu 4× plus lent |
| ❌ | Masques de membres précis (SAM 2) au lieu de « segment épais × silhouette » | GPU conseillé |
| ❌ | Suivi des 2 combattants avec ré-identification (qui frappe qui) | |
| ❌ | Flèches animées de trajectoire, comparaison côte à côte (bon / mauvais geste), écran partagé « pro vs élève » | |
| ❌ | Accroche « réaction » (toi en incrustation qui réagis) | |
| ❌ | Bibliothèque de bruitages / musiques réels (ElevenLabs Sound Effects & Music) en option des sons générés | |

## 2. Formats et déclinaisons (ce qui multiplie la portée)
- ❌ **Une vidéo → 5 formats** : short 9:16 (≤ 60 s), version 16:9 longue pour YouTube (compilation de 8–10 analyses), carrousel Instagram (images des arrêts sur image), extrait 15 s pour stories, GIF
- ❌ Séries automatiques « PARTIE 1/2/3 » quand une vidéo contient plus de 6 coups
- ❌ Version PT-BR complète (voix off en portugais avec ta voix, pas seulement sous-titres) pour viser le Brésil

## 3. Publication et monétisation
- ❌ Publication auto : YouTube Data API (upload + sous-titres + miniature), TikTok Content Posting API, Instagram Graph API (compte pro) — toutes demandent une validation d'app
- ❌ Calendrier de publication (1 short/jour, heures FR et BR)
- ❌ Retour des statistiques (YouTube Analytics API) → le skill `feedback-montage` apprend de la rétention réelle, pas seulement de ton avis
- ❌ Tests A/B de miniatures et titres (YouTube « Tester et comparer »)
- ❌ Réponses aux commentaires assistées, épinglage d'un commentaire avec la question du jour
- ❌ Gestion des droits : registre « qui a filmé / qui apparaît / accord », obligatoire pour monétiser sans risque (Content ID, droit à l'image des élèves mineurs)
- ❌ Offres annexes : programme d'entraînement PDF, cours en ligne, liens d'affiliation matériel (tatamis, protections)

## 4. Plateforme
- ✅ Page web téléphone ↔ PC (QR code), dossier surveillé
- ❌ Hébergement cloud (GPU) pour monter sans laisser le PC allumé ; file d'attente, comptes, historique
- ❌ Application installable (PWA) avec partage direct vers TikTok / Instagram
- ❌ Accélération GPU (NVENC pour l'encodage, MediaPipe GPU) : rendu 3–5× plus rapide
- ❌ Kit de marque : logo animé, couleurs, police, intro 1 s, réglables depuis la page

## 5. Ce qu'il faut de ton côté
- **Clés API** : ElevenLabs (voix + transcription), Anthropic (explications + traductions). Mets-les dans un fichier `.env`, jamais dans le dépôt.
- **2–3 minutes de ta voix** pour le clonage (micro proche, pièce calme).
- **Tes propres vidéos brutes** (entraînements, rodas, démonstrations), filmées en 4K 30 i/s si possible, en vertical, plan large fixe, bonne lumière : c'est ce qui fait la qualité finale bien plus que l'export en 8K.
- **Les miniatures de référence** : YouTube est bloqué depuis cet environnement ; envoie 10–15 captures de miniatures de la chaîne modèle dans un dossier.
