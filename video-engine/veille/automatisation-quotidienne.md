# Automatisation quotidienne : état des lieux et mise en route

Cadence : **jour 1 = vidéo longue (10 min, 16:9)**, **jour 2 = short (60 s, 9:16) toujours lié à cette longue**. Pilotage : `serie/serie.json` + `node tools/daily-plan.mjs`.

## Où tout est déjà OK (testé dans la session)

| Brique | État | Preuve |
|---|---|---|
| Moteur vidéo vertical 9:16 | OK | 3 shorts rendus (60 s) |
| Moteur 16:9 (1920×1080) | OK | test de 27 s rendu, bandeau de chapitre, encart média avec source |
| Voix Gemini homme (Fenrir), consigne de ton | OK | 3 modèles essayés |
| Voix par chapitre (1 requête → plusieurs scènes, découpe sur les pauses) | OK, à écouter | 5 scènes, 1 requête ; test unitaire de la découpe |
| Sous-titres 3 mots, bruitages, caméra à rebond, explosions, flèches, compteurs | OK | images de contrôle |
| Registre de faits obligatoire + `npm test` | OK | un cas d'échec vérifié |
| Planificateur long/short lié | OK | test unitaire (alternance, short orphelin signalé) |
| Contrôle qualité automatique `tools/qa.mjs` | OK | a bloqué à juste titre le test 16:9 |
| Miniatures 16:9 et 9:16, SEO, avis de non-obligation d'achat | OK | fichiers livrés |
| Skills (10) et agents (10) | OK, **non chargés dans cette session** : disponibles à l'ouverture d'une nouvelle session | `.claude/` |

## Ce qui bloque ou manque

| Point | État | Action |
|---|---|---|
| Domaines autorisés (BCE, INSEE, AFT, Banque de France, NASA, Wikimedia, YouTube, TikTok, Trends, etc.) | **Toujours bloqués dans cette session** | Réglages de l'environnement cloud → accès réseau → domaines autorisés ; probablement pris en compte à l'ouverture d'une **nouvelle** session. À retester avec `curl` |
| Images NASA et Google Earth « déposées » | **Aucun fichier trouvé** dans le dépôt ni dans les téléversements | Déposer dans `video-engine/public/media/` (ou me les envoyer) avec source, licence et mention ; règles Google Earth à relire |
| Quota voix gratuit | 10 requêtes/jour/modèle | Alternance longue (≈ 9) / short tient ; deux longues le même jour non |
| Rendu 10 min | ≈ 3 à 4 h | À découper en blocs (outil `--frames` + assemblage : **à écrire**) |
| Globe 3D d'ouverture | Possible (WebGL OK) | **À écrire** |
| Écoute de la voix et du mixage | Jamais faite en session | À faire par vous ou en session avec audio |
| Tâche planifiée quotidienne | **Non créée** | Voir ci-dessous : à activer sur votre accord |

## Tâche planifiée proposée

Sessions neuves chaque jour (donc sans la mémoire de celle-ci) : tout l'état est dans le dépôt (`serie/serie.json`, `projects/`, `veille/`).

- **Quand** : tous les jours à 04:23 UTC (hors des heures chargées), session neuve, branche de travail dédiée.
- **Prompt** : « Lis `.claude/skills/production-quotidienne/SKILL.md` et exécute la production du jour avec l'agent `chef-production-quotidienne`. Ne publie rien. Termine par un rapport et un commit sur la branche. »
- **Coût** : chaque journée longue consomme beaucoup de calcul (veille, vérification, script, rendu de plusieurs heures). Surveiller votre consommation les premières semaines.
- **Garde-fous** : aucune publication ; clé Gemini en variable d'environnement de l'environnement cloud (jamais dans le dépôt) ; arrêt propre sur quota ou domaine bloqué.
