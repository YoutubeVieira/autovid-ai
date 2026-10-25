---
name: replica-recon
description: Démonte l'app à cloner — écrans, parcours, fonctionnalités, modèle de données, prix — à partir de son site, de captures ou d'une démo. Première étape de Replica. Utiliser pour « clone cette app », « analyse cette app », « reverse-engineer », « replica-recon ».
---

# /replica-recon — démonter l'app

On reconstruit **ce que fait** l'app, jamais **ce qu'elle possède** : ni son code, ni son logo, ni ses textes, ni ses images. Les fonctionnalités et les parcours, oui.

## Entrées
Nom ou URL de l'app, et si possible : captures d'écran, vidéo de démo, page de prix. Si la recherche web est disponible, lis la page produit, la page tarifs et la doc d'aide publique.

## Livrable : `replica/recon.md`
1. **Pitch en 1 phrase** + cible + prix (tableau des plans).
2. **Inventaire des écrans** numérotés (`E01 Connexion`, `E02 Agenda`, …) avec, pour chacun : but, éléments, actions.
3. **Parcours clés** (3 à 6) : inscription → première valeur ; action principale ; paiement.
4. **Fonctionnalités** classées MoSCoW : *Must* (le cœur, sans lequel personne ne paie), *Should*, *Could*, *Won't* (v1).
5. **Modèle de données** déduit : entités, champs, relations (diagramme mermaid `erDiagram`).
6. **Intégrations** visibles (SMS, email, calendrier, paiement…).
7. **Zones d'incertitude** : ce qu'on suppose sans l'avoir vu.

Termine en proposant `/replica-reviews` (lire les avis) puis `/replica-plan`.
