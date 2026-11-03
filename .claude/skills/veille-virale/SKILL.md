---
name: veille-virale
description: Chercher chaque jour ce qui fonctionne sur YouTube/TikTok dans la niche « finance mondiale → conséquences pour la France » : formats, accroches, titres, durées, sujets qui montent. Extrait des PATTERNS, ne copie jamais un contenu. À utiliser en début de journée de production ou quand on demande « qu'est-ce qui marche en ce moment ».
---

# Veille virale (patterns, pas copie)

## Ce qu'on cherche
Pour 5 à 10 vidéos récentes de la niche (finance, géopolitique, économie du quotidien, en français puis en pt-BR/en pour les idées) :
- **Accroche** (3 premières secondes) : question, chiffre choc, contradiction, scène concrète ?
- **Titre** : structure (question, « pourquoi », chiffre + bénéfice, tension), longueur, mots-clés.
- **Format** : durée, rythme de montage, présence de cartes / compteurs / sous-titres.
- **Promesse et relances** : boucles ouvertes (« à la fin je te montre… »), questions aux commentaires.
- **Signaux** : vues, âge de la vidéo, commentaires récurrents (« explique X »), reprises par d'autres chaînes.

## Méthode
1. `WebSearch` (mode standard ; « extended » seulement pour un sujet rare). Requêtes en français sur le sujet du jour + « explication », « pourquoi », « conséquences ».
2. `WebFetch` seulement sur les domaines autorisés. **Depuis la session de développement, YouTube, TikTok, Google Trends et Reddit sont bloqués** : dire ce qui n'a pas pu être consulté, ne pas inventer de chiffres de vues.
3. Remplir `veille/AAAA-MM-JJ-viral.md` : tableau `source | titre | format | accroche | ce qu'on en retient` + 3 « patterns » réutilisables + 3 sujets qui montent.
4. Croiser avec `veille-sujets-finance` (score sur 30) : un pattern fort sur un sujet sans impact France ne passe pas.

## Règles
- **Aucune copie** de script, de plan détaillé, de visuels, de miniature, de voix d'une autre chaîne. On garde la mécanique (par exemple « question + chiffre + promesse »), on écrit un contenu original.
- Pas de fausse urgence ni d'affirmation non sourcée pour gagner des vues. Un titre ne promet que ce que la vidéo démontre.
- Distinguer **donnée observée** (vue pendant la veille, avec lien et date) et **hypothèse**.
- La viralité n'est pas garantie : donner des hypothèses à tester (A/B de titres, durée de visionnage), pas des promesses.
