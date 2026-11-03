---
name: emballage-youtube
description: Préparer l'emballage d'une vidéo longue ou d'un short : titres (avec tests A/B), miniature, description, tags, commentaire épinglé, avis légal, et le lien entre le short et la vidéo longue. À utiliser avant publication, une fois la vidéo contrôlée.
---

# Emballage YouTube (titre, miniature, SEO, lien long ↔ short)

## Titres
- 3 variantes : question (« pourquoi… »), tension (« ta banque n'a rien décidé… »), bénéfice (« comprendre en 10 min… »). 45 à 60 caractères, le début porte l'idée.
- Un titre ne promet que ce que la vidéo démontre. Pas de chiffre dans le titre s'il n'est pas dans le registre de faits ; un chiffre d'exemple porte « exemple » dans la miniature ou la description.
- Tester les variantes sur la durée de visionnage, pas seulement sur les clics. La viralité n'est pas garantie : on formule des hypothèses.

## Miniature (1280×720 pour la longue, 1080×1920 pour le short)
- 3 à 4 mots maximum, gros contour, un visage de situation ou un objet fort (carte, flèche, chiffre « exemple »). Générer avec les compositions `Thumbnail` du moteur (`ThumbWide`, `ThumbTall`, variantes) ; les regarder réduites avant de valider.
- Images tierces : seulement avec licence connue et mention.

## Description
Accroche avec le mot-clé (2 lignes) → ce qu'on voit → détail des exemples chiffrés avec leurs hypothèses → **avis** (contenu éducatif, aucune obligation d'achat ou de souscription, pas un conseil en investissement) → sources et crédits médias → 3 hashtags utiles (`#Shorts` pour un short).

## Lien long ↔ short
- **Chaque short renvoie vers sa longue** : phrase de chute « la suite complète est en vidéo longue », lien en description et en commentaire épinglé, et fonction « vidéo associée » de YouTube Shorts quand elle est disponible.
- **Chaque longue annonce son short** dans sa description et son commentaire épinglé.
- Même vocabulaire et même visuel d'accroche, pour que l'audience reconnaisse la série ; playlist commune.
- Tenir `serie/serie.json` à jour (`short_lie`, `long_lie`).

## Contrôle
Chiffres de l'emballage = chiffres de la vidéo = registre de faits. Mentions légales présentes. Voix de synthèse : vérifier la case « contenu modifié ou synthétique » et les règles de monétisation au moment de l'envoi.
Ne rien publier ni envoyer à l'extérieur : l'emballage est livré dans `projects/<slug>.seo.md`, l'utilisateur publie.
