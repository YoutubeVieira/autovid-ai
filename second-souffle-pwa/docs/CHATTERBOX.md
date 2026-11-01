# Voix off avec Chatterbox (sans quota, sur votre PC)

Chatterbox est un modèle de voix libre (licence MIT). Sa version multilingue lit le français, l'anglais et le portugais.
Le script `tools/generate-chatterbox.py` utilise les mêmes textes que la production Gemini (adaptés au genre de la voix) et
écrit les mêmes noms de fichiers dans `audio-chatterbox/<langue>/<f|m>/`.

**État :** le script a été essayé avec `--dry-run` (textes, noms, assemblage des séances). Il n'a pas été essayé avec le vrai
modèle. Commencez par `--test` et écoutez.

## Les voix : deux voix de référence, six voix finales
Une voix de femme et une voix d'homme, chacune dans les trois langues. Chatterbox garde le timbre d'une langue à l'autre.
- `voix-reference/f.wav` : voix de femme (10 à 20 secondes, une seule personne, sans musique ni écho)
- `voix-reference/m.wav` : voix d'homme
- Facultatif, une voix propre à une langue : `fr-f.wav`, `en-m.wav`, `pt-f.wav`...

**Pour une voix personnelle :** la référence doit être la voix d'une vraie personne qui a donné son accord écrit : vous, ou la
femme et l'homme que vous filmez. Le timbre de l'application est alors le leur, ce qui colle avec les vidéos.
Ne partez pas d'une voix produite par Gemini : changer son timbre ensuite ne règle pas la question des conditions d'utilisation de ce service.
Sans voix de référence, `--voix-par-defaut` utilise la voix intégrée du modèle (aucun clonage).

## Accord écrit (obligatoire pour le script)
Créez `voix-reference/consentement.txt` : nom de la personne, date, usage autorisé (application Second Souffle, voix off des
séances), durée, droit de retrait. Faites-le signer avant l'enregistrement. Une voix est une donnée personnelle : à faire valider par un juriste.

## Installation (Windows, une seule fois)
Dans PowerShell. Les commandes appellent directement le Python du dossier `ve`, pour éviter le blocage des scripts.
```
winget install Python.Python.3.11
cd $HOME\autovid-ai\second-souffle-pwa
py -3.11 -m venv ve
```
Avec une carte graphique Nvidia (beaucoup plus rapide) :
```
ve\Scripts\python.exe -m pip install torch==2.6.0 torchaudio==2.6.0 --index-url https://download.pytorch.org/whl/cu124
```
Puis, dans tous les cas :
```
ve\Scripts\python.exe -m pip install chatterbox-tts
```
Le premier lancement télécharge le modèle (plusieurs Go). Sans carte graphique, la production est très lente.

## Utilisation
```
ve\Scripts\python.exe tools\generate-chatterbox.py --test
ve\Scripts\python.exe tools\generate-chatterbox.py --lang fr --max 50
ve\Scripts\python.exe tools\generate-chatterbox.py --lang fr
```
Réglages de style : `--exaggeration 0.4` (plus bas : plus posé) et `--cfg 0.4` (plus bas : rythme plus lent et régulier).
Un fichier déjà produit n'est pas refait. `audio-chatterbox/controle.csv` liste les durées et signale les fichiers à réécouter.

## Conformité : à contrôler avant publication
- [ ] Accord écrit de chaque personne dont la voix sert de référence, conservé avec le projet.
- [ ] Tatouage inaudible de Chatterbox (PerTh) : ne pas le retirer.
- [ ] Mention « voix synthétique » dans l'application et dans la fiche du store.
- [ ] Écoute complète par une personne de langue maternelle pour le portugais du Brésil et l'anglais.
- [ ] Ton : calme, chaleureux, rythme posé ; aucune promesse médicale (les textes ont été relus pour cela).
- [ ] Niveau sonore homogène (les fichiers sont ramenés à la même crête) et pas de coupure en fin de phrase.
- [ ] Juriste : conditions de licence du modèle et des voix, protection des données, voix clonée d'un tiers.
