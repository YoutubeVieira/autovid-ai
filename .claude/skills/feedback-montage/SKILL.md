---
name: feedback-montage
description: Après un montage, recueille les retours de l'utilisateur et les enregistre pour que les prochains montages soient meilleurs. À utiliser quand l'utilisateur commente un rendu (« trop long », « textes trop petits », « mauvais coup », « j'aime le flash »…).
---

# Boucle d'amélioration

1. Demande en une fois : ce qui marche, ce qui ne va pas, ce qu'il faut garder ou changer (rythme, textes, couleurs, sons, durée).
2. Classe chaque retour :
   - **réglage** (durée de l'arrêt sur image, nombre d'analyses, couleur, volume…) → modifie la valeur par défaut dans le code (`autovid/combat.py`, `autovid/styles.py`) ou une option CLI, puis relance le rendu ;
   - **préférence** (ton, vocabulaire, style d'accroche) → ajoute une ligne datée dans `.claude/skills/montage-combat/APPRENTISSAGES.md` ;
   - **bug** (mauvais coup détecté, texte qui déborde) → corrige-le et ajoute un test dans `tests/`.
3. Relance le montage, refais la planche contact, et montre la différence.
4. Ne supprime jamais une ligne des apprentissages sans l'accord de l'utilisateur.
