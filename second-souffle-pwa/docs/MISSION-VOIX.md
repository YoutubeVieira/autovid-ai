# Mission : vérifier la clé Google et produire les voix off

À lire par une session Claude qui a accès au PC et au navigateur de l'utilisateur (application Claude pour ordinateur, contrôle de l'ordinateur ou Claude dans Chrome). Faire `git pull` sur la branche `ccr-625630fe-eazkl1` avant de commencer.

## Contexte
Application Second Souffle (coaching sportif après 40 ans, français, anglais et portugais du Brésil). Les textes de voix off sont écrits (`docs/voiceover-manifest.csv`, 137 phrases par langue). `tools/generate-audio.js` produit 822 fichiers WAV : voix de femme Sulafat et voix d'homme Achird dans chaque langue, Vindemiatrix et Charon pour les séances de bien-être, modèle `gemini-3.8-flash-tts`. La clé est lue dans la variable d'environnement `GEMINI_API_KEY`.

Sous Windows : `Verifier-ma-cle.bat` (vérifie l'accès de la clé aux modèles de voix, sans rien produire) et `Produire-les-voix.bat` (produit tout). Les deux demandent la clé en saisie masquée.

## Étapes
1. Ouvrir https://aistudio.google.com/apikey. Si une connexion est demandée, s'arrêter : l'utilisateur tape lui-même son mot de passe et ses codes. Relever, sans copier la clé : niveau de la clé (gratuit ou payant) et limites affichées pour `gemini-3.8-flash-tts` et `gemini-3.8-flash-lite-tts`.
2. Ouvrir https://console.cloud.google.com/billing. Relever seulement : un compte de facturation est-il relié au projet de la clé ? Y a-t-il une alerte de budget ? Ne créer aucun compte de facturation, n'ajouter aucune carte, n'activer aucune option payante.
3. Faire lancer par l'utilisateur `Verifier-ma-cle.bat`. Lire le résumé.
4. Si les modèles de voix sont accessibles : faire lancer `Produire-les-voix.bat`. Le script produit d'abord 6 fichiers d'essai ; l'utilisateur les écoute (surtout le portugais du Brésil) avant de continuer. En cas d'erreur 429, relancer plus tard : le script reprend là où il s'est arrêté.
5. En cas d'erreur 400, 403 ou 404, copier le message sans la clé. Si c'est la forme de la requête du modèle 3.8 (non vérifiée dans la documentation de Google), corriger `tools/generate-audio.js`, lancer `node tests/logic.test.js` et `node tests/audio.test.js`, puis pousser sur la même branche.

## Règles
- Ne jamais demander ni accepter un mot de passe, un code ou une clé d'API dans la conversation. Ne jamais l'écrire dans un fichier, un journal ou un dépôt.
- Ne pas modifier les paramètres du compte Google sans demander.
- Répondre en français, en phrases simples : niveau de la clé, limites, facturation (oui ou non), résultat de l'essai, nombre de fichiers produits et dossier.
