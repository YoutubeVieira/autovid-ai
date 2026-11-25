# Origine des sons par défaut

Générés avec [earshot](https://github.com/Leonxlnx/earshot) 1.0.0 (commit 7a7f7c5, licence MIT ; « every sound it makes is yours to use » — aucun crédit obligatoire), convertis en MP3 44,1 kHz stéréo.

| Fichier | Événement | Commande |
|---------|-----------|----------|
| `transition.mp3` | début d'exercice | `earshot make --sound whoosh/soft` |
| `repos.mp3` | début de repos | `earshot make "a soft gentle chime"` → `notify/pair` (marimba, 2 notes) |
| `cloche.mp3` | fin de séance | `earshot make --sound logo/bloom` (accord de piano feutré, ≈ 4 s) |

Chaque appel rend une nouvelle prise : relancer la commande donne un son proche, pas identique (`--seed N` pour le figer).
