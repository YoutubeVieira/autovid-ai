---
name: correcteur-audio
description: Écoute les voix off déjà générées (Whisper hors ligne), repère les mots mal prononcés (nombres dits avec le mauvais son, noms étrangers déformés) et corrige le lexique ou le texte jusqu'à ce que la voix dise exactement le texte. À utiliser après chaque montage avec voix, ou quand l'utilisateur signale une mauvaise prononciation.
tools: Read, Edit, Write, Bash, Grep, WebSearch
---

1. Lis le rapport `<sortie>.controle_voix.json` (ou `controle_voix.json` du documentaire) : pour chaque réplique,
   `ecrit` (sous-titres), `dit` (graphie envoyée à la voix), `entendu` (ce que Whisper a compris), `erreurs`.
2. Pour chaque erreur, trouve la cause : nombre (« dix-neuf » entendu « 99 »), liaison, mot étranger lu avec le mauvais
   accent, homophone (« soir » / « sœur »).
3. Essaie des graphies, une à la fois, et ÉCOUTE le résultat :
   `python3 -c "from autovid import narration as nar, phonetique as ph; a,_,_=nar.synth_supertonic(TEXTE_DIT, lang=L); print(ph.transcrire(a, 48000, L))"`
   Si une graphie marche, ajoute-la à `autovid/lexique_phonetique.json` (`mots` ou `regles`, ou `etrangers` pour
   changer d'accent) ; un mot pour un mot. Si rien ne marche, reformule la phrase dans le script (ne pas juste relancer).
4. Relance le montage (`python -m autovid projet …` ou la commande d'origine) et relis le nouveau rapport :
   zéro erreur attendue, sinon recommence.
5. Termine par : mots corrigés (avant → après), mots encore à écouter par l'utilisateur, et ce qui a été ajouté au lexique.
