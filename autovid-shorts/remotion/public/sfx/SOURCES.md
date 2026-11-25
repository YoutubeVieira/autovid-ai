# Origine des sons par défaut

Générés avec [earshot](https://github.com/Leonxlnx/earshot) 1.0.0 (commit 7a7f7c5, licence MIT ; « every sound it makes is yours to use » — aucun crédit obligatoire), convertis en MP3 44,1 kHz stéréo.

| Fichier | Commande |
|---------|----------|
| `whoosh.mp3` | `earshot make --sound whoosh/fast` |
| `pop.mp3` | `earshot make "a soft UI pop"` → `ui_pop/soft` |
| `click.mp3` | `earshot make "a single mechanical keyboard key press"` → `keyboard/mechanical` |
| `impact.mp3` | `earshot make "a deep cinematic impact hit"` → `boom/deep` |

Chaque appel rend une nouvelle prise : relancer la commande donne un son proche, pas identique (`--seed N` pour le figer).
