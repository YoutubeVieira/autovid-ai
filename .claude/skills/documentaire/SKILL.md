---
name: documentaire
description: Documentaire YouTube automatique façon National Geographic (true crime responsable, histoire, faits divers jugés) — recherche des faits, script, archives libres de droits trouvées automatiquement, voix off, nappe sombre, chapitres, crédits, shorts. À utiliser quand l'utilisateur demande un documentaire, une enquête, une affaire criminelle, un « tueur en série », des images d'archives.
---

# Documentaire automatique

Commande : `python -m autovid documentaire "L'affaire X" -o dossier/ [--plan plan.json] [--images dossier/] [--minutes 8] [--langue pt]`

**Public de l'utilisateur pour les documentaires : brésilien → toujours `--langue pt`** (script, voix pm_alex ou ElevenLabs
en portugais, textes à l'écran et description en pt-BR ; `plan.json` écrit en portugais du Brésil, champs `requete`
en anglais). Les échanges avec l'utilisateur restent en français.

## Étapes
1. **Plan** (schéma `ai.DOC_SCHEMA`) :
   - avec une clé Anthropic, `ai.doc_plan` cherche sur le web puis écrit le plan tout seul ;
   - dans une session Claude Code sans clé : faire la recherche avec WebSearch, écrire `plan.json` soi-même
     (mêmes règles que `ai.DOC_RULES`), puis `--plan plan.json`.
2. **Archives** : `archives.py` cherche pour chaque plan (Wikimedia Commons, Library of Congress, Openverse,
   Internet Archive) et ne garde que domaine public / CC0 / CC BY / CC BY-SA. Crédits dans `credits.json`, à l'écran
   (bas à droite), au générique et dans la description. Réseau : ces domaines doivent être autorisés dans
   l'environnement (commons.wikimedia.org, upload.wikimedia.org, archive.org, www.loc.gov, tile.loc.gov,
   api.openverse.org). Sinon : plans d'ambiance (brume) et cartes texte.
3. **Montage** : Ken Burns sur les photos, films d'archive, cartes date / lieu / citation / chapitre, étalonnage froid,
   grain, vignette, nappe `sfx.ambiance_sombre`, coups `tension_hit` aux chapitres, −14 LUFS.
4. **Sorties** : `documentaire.mp4`, `chapitres.txt`, `documentaire.fr.srt`, `shorts/`, `a_publier.md`, `credits.json`.
5. Regarder la planche contact, puis le mettre dans la plateforme (skill `plateforme`, `--format 16:9`).

## Règles éditoriales (toujours)
- Affaires jugées ou faits établis et sourcés ; pas de nom de suspect jamais condamné (présomption d'innocence).
- Angle enquête et victimes ; jamais glorifier l'auteur ; aucun détail sanglant, aucune photo de corps ni de scène
  de crime (`archives.INTERDIT` les écarte ; vérifier aussi à l'œil sur la planche contact).
- Pas d'image générée présentée comme une archive ; une reconstitution est écrite « reconstitution » à l'écran.
- Relire les faits avec les sources avant publication ; conseiller une chaîne séparée de la chaîne capoeira.
- Mineurs jamais identifiés (ECA au Brésil) ; données personnelles des familles protégées (LGPD).
