---
name: replica-diff
description: Compare le clone à l'original et note la couverture — ce qui est fait, ce qui manque encore, ce qui est mieux. Utiliser pour « qu'est-ce qui manque », « compare avec l'original », « replica-diff ».
---

# /replica-diff — ce qui manque encore

Compare `replica/recon.md` (l'original) avec l'app réelle (lance-la, parcours les écrans) et `replica/reviews.md`.

Sortie `replica/diff.md` :

| Écran / fonctionnalité | Original | Clone | Statut |
|------------------------|----------|-------|--------|
| E02 Agenda | ✓ | ✓ | ok |
| Rappel SMS | ✓ | — | **manque** |
| Fuseau horaire | confus | explicite | **mieux** |

Puis : **score de couverture** = *Must* faits / *Must* total (objectif 100 % avant lancement), la liste « ce qui manque encore » triée par impact, et la prochaine commande `/replica-build` à lancer.
