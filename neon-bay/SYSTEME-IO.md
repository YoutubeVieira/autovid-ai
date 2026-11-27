# Vendre Néon Bay avec Systeme.io

Plan en deux temps : on lance avec **un code commun** (option A), puis on passe aux **codes uniques** avec Make quand les ventes arrivent (option B).

Les codes sont dans le dossier `private/` (il n'est pas envoyé sur GitHub) :
- `private/code-lancement.txt` : le code commun de lancement.
- `private/codes-uniques.csv` : 300 codes uniques pour l'option B.

Garde ces deux fichiers en lieu sûr. Ils ne marchent qu'avec la clé secrète qui est maintenant dans `js/data.js`. Si tu changes cette clé, il faudra régénérer tous les codes.

---

## Étape 1 : préparer Systeme.io (option A)

Les noms des menus peuvent varier un peu selon ta version de Systeme.io.

1. **Paiement** : dans les paramètres, connecte Stripe ou PayPal.
2. **Tunnel de vente** : crée un tunnel « Néon Bay » avec trois pages :
   - page de vente ;
   - bon de commande (offre « Néon Bay, jeu complet », paiement unique 4,99 €) ;
   - page de remerciement.
3. **Email automatique** : crée une règle d'automatisation.
   - Déclencheur : nouvelle vente de l'offre « Néon Bay, jeu complet ».
   - Action : envoyer l'email « Ton code Néon Bay » (texte plus bas).
4. **Dans le jeu** : copie l'adresse de ta page de vente dans `js/data.js` :
   ```js
   buyUrl: 'https://ton-compte.systeme.io/neon-bay',
   ```
   Puis relance `node tools/build-standalone.js` pour mettre à jour `dist/index.html`.
5. **Test** : fais un achat test (mode test Stripe ou coupon à 100 %), vérifie que l'email arrive et que le code débloque bien les niveaux.

---

## Textes de la page de vente

**Titre**
> 30 niveaux. 4 pays. Une seule ville à prendre à la fois.

**Sous-titre**
> Tu as fini le niveau 1 de Néon Bay ? La suite t'attend en Italie, en Colombie et dans les favelas de Morro Azul.

**Bloc 1 : ce que tu débloques**
- 29 nouveaux niveaux, 290 étapes de plus
- Porto Lumi (Italie) : deux familles mafieuses se disputent les canaux
- Sierra Verde (Colombie) : pistes clandestines, hacienda et laboratoire sous la jungle
- Morro Azul (Brésil) : ruelles des favelas, baile funk et guerre des bondes
- 7 chefs de gang à faire tomber, de Snake jusqu'à Sombra

**Bloc 2 : ton arsenal**
> Le fusil d'assaut arrive au niveau 8, le fusil de précision au 11, le lance-roquettes au 15. Le minigun, lui, se mérite : niveau 24. Entre deux missions, tu achètes ton armure, tes trousses de soins et ta nitro avec l'argent gagné sur le terrain.

**Bloc 3 : comment ça marche**
1. Tu paies une fois, 4,99 €. Pas d'abonnement.
2. Tu reçois ton code par email en quelques minutes.
3. Dans le jeu, tu cliques sur « Jeu complet » et tu colles ton code. Les 30 niveaux sont ouverts.

**Bouton**
> Je débloque les 29 niveaux · 4,99 €

**Questions fréquentes**
- *Sur quoi je peux jouer ?* Sur ordinateur (clavier et souris) et sur téléphone (commandes tactiles), directement dans le navigateur.
- *Je perds ma progression si je change d'appareil ?* La progression reste sur l'appareil où tu joues. Ton code, lui, marche partout.
- *Je n'ai pas reçu mon code.* Regarde dans tes spams, puis écris-nous à [ton adresse de contact].

---

## Page de remerciement

> **Merci, c'est parti !**
> Ton code arrive par email dans quelques minutes. Pense à vérifier tes spams.
> Dans le jeu, clique sur « Jeu complet », colle ton code, et rendez-vous à Porto Lumi.

---

## Email « Ton code Néon Bay »

**Objet :** Ton code pour les 30 niveaux de Néon Bay

> Salut,
>
> Merci pour ton achat. Voici ton code :
>
> **NBAY-XXXX-XXXX-XXXX** *(mets ici le code de `private/code-lancement.txt`)*
>
> Pour l'utiliser :
> 1. Ouvre Néon Bay : [lien du jeu]
> 2. Clique sur « Jeu complet ».
> 3. Colle ton code et valide.
>
> Le niveau 2 t'attend. MC Ozone aussi, et il n'aime pas attendre.
>
> Garde cet email : le code marche sur tous tes appareils.
>
> Bon jeu,
> [ta signature]

---

## Étape 2 : passer aux codes uniques (option B, avec Make)

À faire quand les premières ventes arrivent. Ça évite qu'un seul code circule partout.

**Préparation**
1. Importe `private/codes-uniques.csv` dans une feuille Google Sheets appelée « Codes Néon Bay ». Colonnes : `code`, `utilise`, `email`, `date`.
2. Crée un compte sur make.com (la formule gratuite suffit pour démarrer).

**Scénario Make (4 modules)**
1. **Webhooks › Custom webhook** : Make te donne une adresse. Copie-la.
2. **Google Sheets › Search Rows** : feuille « Codes Néon Bay », filtre `utilise` = `non`, limite 1 résultat.
3. **Google Sheets › Update a Row** : sur la ligne trouvée, mets `utilise` = `oui`, `email` = email de l'acheteur reçu par le webhook, `date` = maintenant.
4. **Gmail › Send an email** (ou ton service d'email) : à l'adresse de l'acheteur, avec le texte de l'email ci-dessus et le code trouvé à l'étape 2 à la place du code commun.

**Dans Systeme.io**
- Dans la règle d'automatisation de la vente, remplace l'envoi de l'email par l'action « Envoyer un webhook », avec l'adresse Make. Cette action peut demander une formule payante de Systeme.io : vérifie dans ton compte.
- Fais un achat test et vérifie que la ligne passe à `oui` dans la feuille.

**Quand il reste moins de 50 codes**, lance `node tools/generate-codes.js 300` et ajoute les nouveaux codes à la feuille.

---

## Rappel

- Les codes sont vérifiés dans le navigateur. Une personne très motivée peut contourner le verrou en lisant le code du jeu. Pour démarrer, ça suffit.
- Change le code commun de temps en temps si tu restes sur l'option A : génère-en un nouveau et mets-le dans l'email. Les anciens codes restent valables.
