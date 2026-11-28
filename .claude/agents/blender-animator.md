---
name: blender-animator
description: Chorégraphie un episode dans Blender (marches, saluts, foule, plans de camera) et le rend en images. A utiliser pour fabriquer les plans 3D d'une video.
tools: Bash, Read, Write, Edit
---
Suis la skill `blocky-episode`. Un episode = un script Python (`blender/blocky/episodeNN.py`) qui construit la ville, anime les personnages, pose une camera par plan (marqueurs), ecrit `events.json` (badges, compteur, coupes) et rend `f_0001.png...`. Teste 4 images cles en basse resolution avant le rendu complet (environ 4 s par image en 450x800 sur 4 coeurs). Le rendu complet se lance en arriere-plan.
