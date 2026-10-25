---
name: yt-viral
description: Trouve les vidéos les plus virales de la niche, démonte leur titre, leur hook et leur structure, et les recrée pour la chaîne de l'utilisateur. Utiliser pour « vidéos virales », « qu'est-ce qui marche dans ma niche », « recrée cette vidéo », « outlier ».
---

# /yt-viral — démonter ce qui marche et le recréer

## 1. Trouver les outliers
- Cherche (WebSearch, ou liste fournie par l'utilisateur) les vidéos de la niche des 90 derniers jours.
- **Outlier** = vues ≥ 3× la moyenne de la chaîne qui l'a publiée. Le ratio compte plus que le nombre brut.
- Classe par ratio ; garde les 5 premières.

## 2. Démonter (pour chacune)
| Élément | Ce qu'on note |
|---------|---------------|
| Titre | formule (cf. `yt-script/formules.md`), longueur, mot concret |
| Miniature | sujet, texte, émotion |
| Hook (0–5 s) | phrase exacte, formule n / 21 |
| Structure | blocs et leur durée, où est le virage |
| CTA | type et position |

## 3. Recréer
Ne copie jamais le texte. Garde la **mécanique** (formule, structure, rythme), change le sujet, l'exemple et la voix. Produis le brief puis enchaîne sur `/yt-script` avec la formule identifiée.

Sortie : classement (vidéo · vues · ratio) + fiche de démontage + brief recréé. Ajoute les idées au `profil/backlog.md`.
