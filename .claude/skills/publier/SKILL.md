---
name: publier
description: Prépare la publication d'un montage sur TikTok, Instagram Reels, YouTube Shorts et Facebook — export au bon format, légende, hashtags, miniature (Canva si connecté), meilleur moment de publication. À utiliser quand l'utilisateur veut poster ou monétiser une vidéo.
---

# Publier

1. Exports :
   - TikTok / Reels / Facebook : 1080x1920, 30 i/s, H.264, AAC, −14 LUFS (sortie par défaut d'autovid).
   - YouTube Shorts : `--resolution 4k` donne un master 2160x3840 (meilleure qualité après recompression YouTube).
2. Écris pour chaque plateforme : un titre (≤ 60 caractères), une légende avec une question pour les commentaires, 5–8 hashtags (mélange large : #boxe #mma #selfdefense, et niche : #pullcounter #muaythaitechnique), et un CTA (« Enregistre pour l'essayer »).
3. Miniature / couverture : prends l'image la plus forte (l'arrêt sur image de l'analyse #1) :
   `ffmpeg -ss <t> -i sorties/x.mp4 -frames:v 1 sorties/x_cover.jpg`. Si le connecteur Canva est actif (`.mcp.json`), crée une couverture à partir de cette image ; sinon garde le JPG.
4. Monétisation : rappelle les règles qui comptent : vidéos originales (pas de réupload de combats dont l'utilisateur n'a pas les droits — risque de Content ID / démonétisation), musique libre de droits (le beat généré l'est), régularité (1 short/jour), séries « PARTIE 1/2/3 ».
5. La publication elle-même se fait dans les apps (pas d'API de publication branchée ici). CapCut : n'a pas d'API officielle ; si l'utilisateur veut retoucher, il importe le MP4 dans CapCut.
