# Testeurs automatiques

20 profils de joueurs (voir `profiles.js`) qui jouent à Néon Bay avec les règles d'un humain :
même vitesse de marche et de conduite, même tir, même police, mêmes chronos, sans téléportation.
Le jeu tourne en simulation accélérée (sans rendu) : une partie complète prend quelques minutes.

```
node tools/bots/run.js                       # les 20 testeurs, niveaux 1 à 30
node tools/bots/run.js --bots 2,3 --to 5     # quelques testeurs, quelques niveaux
node tools/bots/report.js                    # écrit reports/bots/RAPPORT.md
```

Limites : les testeurs conduisent et visent moins bien qu'un bon joueur. Leurs temps sont des ordres
de grandeur ; leurs échecs montrent où le jeu est dur. Rien ne remplace 5 à 10 vrais joueurs.
