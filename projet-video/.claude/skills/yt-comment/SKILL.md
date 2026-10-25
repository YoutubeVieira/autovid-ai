---
name: yt-comment
description: "Trie et répond aux commentaires d'une vidéo — réponses dans la voix du créateur, idées de vidéos envoyées au backlog, spam ignoré. Utiliser pour « réponds aux commentaires », « gère les commentaires », « comentários »."
---

# /yt-comment — les commentaires

Entrée : commentaires collés ou exportés (CSV/JSON). Ne publie jamais rien toi-même : tu proposes, l'utilisateur publie.

Classe chaque commentaire dans une colonne :
| Colonne | Action |
|---------|--------|
| **Question** | réponse courte (≤ 2 phrases) dans la voix de `profil/voice.md` |
| **Demande de vidéo** | ajoute une ligne à `profil/backlog.md` avec le nombre de demandes similaires |
| **Mot-clé du CTA** (ex. CLONE) | liste des pseudos à contacter en DM, avec le message à envoyer |
| **Critique utile** | réponse + note pour `/yt-retention` |
| **Spam / haine** | ignoré, ne pas répondre |

Sortie : un tableau par colonne, puis « Top 3 des demandes de la semaine » (alimente `/yt-plan`).
