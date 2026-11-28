# Liste à télécharger (sur ton PC) – sons et vidéos pour « Le monde se peuple »
Sites et licences : voir `docs/SOURCES.md`. Pour chaque fichier note **URL + licence** dans `licences.csv` (`fichier;nom;licence;auteur;source`). Refuse NC/ND/inconnu.

## A. AUDIO (priorité 1 → 3)
**Priorité 1 – tout de suite (ambiances et actions de la ville)**
| Nom du fichier | Mots à chercher (EN / FR) | Durée | 
|---|---|---|
| ambiance_ville | city ambience street day / ambiance rue ville jour | 30-60 s |
| ambiance_foule | crowd murmur, crowd cheer / foule murmure, foule acclame | 20-30 s |
| ambiance_oiseaux | birds morning park / oiseaux matin | 30 s |
| ambiance_vent | wind soft / vent léger | 30 s |
| ambiance_riviere | river stream / ruisseau | 30 s |
| ambiance_grillons | crickets night / grillons nuit | 30 s |
| ambiance_pluie | rain light / pluie légère | 30 s |
| pas_dalles, pas_gravier | footsteps pavement, gravel / pas | 5-10 s |
| porte, cloche_mairie | door open close, church bell / porte, cloche | 2-6 s |
| applaudissements, rire_enfants, cri_joie, waouh | applause, kids laughing, cheer, wow / applaudissements, rires | 2-6 s |
| pop, whoosh, ding, level_up | UI pop, whoosh, bell, level up (Kenney, CC0) | 0,2-2 s |
**Priorité 2 – métiers de la ville**
four_boulangerie / clochette_boulangerie (bakery bell), cuisine_friture (sizzling pan), sirene_pompier (fire truck siren), ambulance, police_sirene, fusee_decollage (rocket launch), clavier (keyboard typing), marteau, scie, caisse_enregistreuse (cash register), train, avion, marche_ambiance, mer_vagues, chantier, camera_clic (camera shutter), micro_larsen_non (éviter).
**Priorité 3 – animaux (vrais enregistrements, filtre CC0)**
chien (dog bark), chat (cat meow), poule, coq (rooster), vache, cheval (horse neigh), cochon, mouton, canard, singe (monkey – pour Robin), éléphant, lion, loup, oiseaux (blackbird, sparrow), grenouille. **Dinosaures** : aucun enregistrement réel n'existe : mélanger lion/alligator/éléphant ralenti (ou garder notre `roar.wav` de synthèse).
**Voix** (optionnel, plus tard) : rires et pleurs d'enfant, bébé (baby giggle, baby cry), foule qui compte « 3, 2, 1 ».

## B. VIDÉO (libres de droits : Pexels, Pixabay, Mixkit, Videvo)
| Usage | Mots à chercher |
|---|---|
| Transitions / effets | light leak, film grain, glitch overlay, flash white, zoom transition, confetti, sparkles, fireworks (fond noir pour « écran/screen ») |
| Habillage | like button animation, subscribe animation, arrow pointing, notification pop, heart burst, emoji reaction |
| Décors réels pour contraste (optionnel) | aerial city drone, empty street, crowd walking, sunrise city |
| Ciels / HDRI (Poly Haven, CC0) | sky clear, sunset, overcast : pour l'éclairage Blender |
**Vidéos de référence à REGARDER (pas à copier ni réutiliser)** : comptes repérés par la veille : @zarbi.histoires, @baommmm3344, @skibifruit3d, @bloxtales.story, @zenkai.ft1, @didiblud45. Note leurs hooks, rythme de coupe et sons (pas les scènes).
Ne télécharge pas de musiques/vidéos depuis YouTube/TikTok pour les réutiliser : droits d'auteur.

## C. Installer sur le PC (Windows)
1. Installer Python 3.11 (python.org), ffmpeg (`winget install ffmpeg`) et git.
2. `git clone https://github.com/YoutubeVieira/autovid-ai` puis `git checkout claude/canva-auto-video-montage-1c8g4k`.
3. Mettre les sons dans `packs/a_importer/` avec `licences.csv`, puis : `python packs\animals\importer_sons.py packs\a_importer --out packs\sons_monde` (rejette les licences non commerciales, nettoie, génère `CREDITS.md`).
4. Vérifier la voix : `python packs\voices\verifier_phonetique.py monde\episodes\ep02\script.txt monde\episodes\ep02\voix --asr-model packs\voices\models\sherpa-onnx-whisper-small` (modèle : release sherpa-onnx « asr-models »).
5. Commit + push sur la branche : je récupère tout et je branche les sons dans les épisodes.
