# Machine à Reels — créer, publier, analyser (vous ne faites que relire et approuver)

D'après un post Instagram « Máquina de Reels » (6 étapes). Chaque étape est tenue par un agent de ce projet :

| # | Étape | Agent | Outil |
|---|-------|-------|-------|
| 1 | Machine à Reels (narration, animations, sous-titres) | `monteur-video`, `directeur-creatif` | gabarit Remotion, 7 styles (`styles/STYLES.md`), sons automatiques |
| 2 | Connecteur Instagram / TikTok / YouTube | `publicateur` | voir « Connecteurs » ci-dessous |
| 3 | Recherche des tendances de la niche | `stratege-youtube` | skills `/yt-viral`, `/yt-plan` |
| 4 | Scripts et production des 7 vidéos de la semaine | `scenariste` puis `monteur-video` / `directeur-creatif` | `scripts/`, `remotion/data/` |
| 5 | Validation puis 1 publication par jour | **vous**, puis `publicateur` | `outils/machine.py approuver / programmer` |
| 6 | Analyse des performances, variantes des meilleures | `analyste-performance` | `outils/machine.py metriques / rapport` |

Le tout est piloté par l'agent **`chef-machine`** : « lance la machine pour la semaine prochaine ».

## La file de la semaine
`machine/semaines/<AAAA-Sss>/semaine.json` : 7 emplacements, chacun avec un statut
`idee → script → monte → a_approuver → approuve → programme → publie` (ou `refuse`).
- **Rien n'est programmé ni publié sans votre approbation.** `approuver` exige le fichier vidéo et la légende ; seul `approuver` fait passer à `approuve`, et seulement quand vous l'avez demandé.
- `programmer` place une vidéo approuvée par jour libre, écrit `publications.csv` (date, heure, plateforme, fichier, légende + hashtags) et `calendrier.ics` (à importer dans votre agenda).

```bash
python3 outils/machine.py semaine --debut 2026-11-30 --heure 18:00 --plateformes instagram,tiktok,youtube
python3 outils/machine.py statut
python3 outils/machine.py approuver v3
python3 outils/machine.py programmer
python3 outils/machine.py publie v3 --plateforme instagram --url https://www.instagram.com/reel/…
python3 outils/machine.py metriques export_youtube.csv --plateforme youtube
python3 outils/machine.py rapport
```

## Connecteurs (étape 2)
Publier à votre place demande l'accès à vos comptes : cela passe toujours par vous. Trois niveaux, du plus simple au plus automatique :

| Plateforme | Programmation native (gratuite, sans code) | API officielle (automatique) |
|------------|---------------------------------------------|------------------------------|
| YouTube | YouTube Studio : téléverser, « Programmer » à la date de `publications.csv` | YouTube Data API v3 (projet Google Cloud + OAuth à votre nom) ; envoi en privé avec date de publication |
| Instagram | Meta Business Suite (compte professionnel) : Planifier | Instagram Graph API (compte Pro relié à une Page Facebook) |
| TikTok | TikTok Studio (web) : Programmer | Content Posting API (application TikTok à faire auditer pour publier directement) |

**Connecteurs de votre compte Claude** : votre compte a des connecteurs qui savent programmer ou mesurer sur ces réseaux — OpusClip (publication et programmation multi-réseaux ; son accès par connecteur demande un abonnement Pro ou supérieur), Picsart (aperçu et publication sociale), Supermetrics (statistiques Instagram et réseaux sociaux). L'agent `publicateur` les utilise seulement si vous les avez connectés et seulement pour des vidéos approuvées ; sinon il prépare tout pour la programmation native.

## Données réelles (le « secret » du post)
L'analyse repose sur **vos** chiffres : exports CSV de YouTube Studio, d'Instagram (statistiques professionnelles) et de TikTok Studio, ou le connecteur Supermetrics. `machine.py metriques` reconnaît les colonnes en anglais, français et portugais ; `rapport` classe les vidéos et propose les variantes à produire la semaine suivante (`variante_de`).

Les résultats annoncés dans le post (« 15 millions de vues en 30 jours ») ne sont ni vérifiables ni reproductibles à coup sûr : la machine fait gagner du temps et rend la stratégie mesurable, elle ne garantit pas l'audience.
