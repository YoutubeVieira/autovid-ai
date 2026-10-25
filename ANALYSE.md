# Analyse des deux vidéos de référence

Deux Reels/Shorts verticaux (1080×1920, 60 i/s, en portugais du Brésil), même créateur, même recette. Chacun fait la promo d'un **pack gratuit de 11 skills Claude Code**.

| | Vidéo 1 | Vidéo 2 |
|---|---|---|
| Durée | 46 s | 43 s |
| Sujet | **YouTube Agent** : 11 skills `/yt-*` qui font tourner une chaîne YouTube | **Replica** : 11 skills `/replica-*` qui clonent n'importe quelle app |
| Hook (0–3 s) | « O Claude acabou de *matar* o YouTube » | « Agora é só você *clonar* qualquer app usando o Claude » |
| Formule de hook | Annonce de mort (« X vient de tuer Y ») | Promesse impossible |
| Preuve | page GitHub du pack, « totalmente de graça » | page GitHub « The Replica skill », « de graça » |
| Corps | une skill = un visuel = 2–4 s : script (21 formules de hook), package (titre + miniature notés /100), edit (coupes), comment, plan (semaine), viral (démonte et recrée) | recon (démonte), build (reconstruit), test (cherche les erreurs), diff (ce qui manque), puis « l'entrepreneur » : lit 140 avis et résout les problèmes, paiement PIX « PAGO » |
| Virage | « Você já recebe um vídeo viral, escrito na sua voz » | « um clone de qualquer app » → l'entrepreneur va plus loin |
| CTA | « abre o Claude Code e cola esse link » | « comenta CLONE que eu te envio na DM » (lead magnet) |
| Fond graphique | beige clair `#EDEBE7`, mascotte pixel rouge | gris anthracite `#1C1C1C`, personnages en papier découpé |

## Grammaire visuelle commune
- **Split-screen** : motion design sur ~52 % du haut, facecam sur le bas. Ponctuellement plein écran facecam (émotion) ou plein écran graphique (gros chiffre « 11 », « 140 »).
- **Sous-titres mot à mot** dans une pastille noire posée sur la ligne de coupe ; **un seul mot en rouge** `#E8392B` par segment (le mot qui porte le sens : *matar*, *11*, *Replica*, *CLONE*).
- **Un changement visuel toutes les 2 à 4 s**, jamais de plan fixe plus long.
- Objets récurrents : fenêtres de terminal « Claude Code », compteurs animés, grilles d'icônes (une par skill), barres, classements, cartes notées.
- Petits libellés gris en capitales au-dessus des visuels (« ELA TE AJUDA A DECIDIR », « COLA NO CLAUDE CODE »).

## Structure (gabarit réutilisable)
```
0–3 s    HOOK      promesse choc, 1 mot rouge
3–8 s    PREUVE    nom du produit + « gratuit »
8–11 s   COMPTE    « ce n'est pas 1 skill, c'est 11 »
11–38 s  CORPS     1 skill / 2–4 s, chacune avec son visuel
38–42 s  PAYOFF    le résultat final pour le spectateur
42–46 s  CTA       une seule action (coller un lien / commenter un mot)
```

## Ce que ce dépôt en tire
- [`projet-video/`](projet-video/) — le pack **AutoVid YouTube Agent** (11 skills `/yt-*` en français) + un gabarit **Remotion** qui rend des vidéos dans ce format exact à partir d'un JSON.
- [`projet-app/`](projet-app/) — le pack **Replica** (11 skills `/replica-*` en français) pour concevoir, construire, tester, monétiser et lancer une application.
