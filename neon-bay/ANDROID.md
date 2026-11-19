# Néon Bay sur Google Play : le guide

## Ce qui est déjà prêt dans le projet
- **Achat dans l'app** (`js/store.js`) : dans l'application Android, le bouton « Acheter le jeu complet » passe par Google Play Billing. Il y a aussi un bouton « Restaurer mes achats », et le jeu retrouve tout seul un achat déjà fait sur le même compte Google.
- **Codes web conservés** : un joueur qui a acheté un code sur ton site peut toujours le saisir dans l'app. Dans l'app, il n'y a aucun lien vers ton site et aucun prix du site (règle Google Play).
- **Application installable et hors ligne** : manifeste, icônes, cache hors ligne, three.js en local (`vendor/`).
- **Version à mettre en ligne** : `node tools/build-web.js` crée le dossier `dist-web/`.
- **Modèles Android** : `android/twa-manifest.json`, `android/assetlinks.json`, `android/verify-purchase.js`.
- **Politique de confidentialité** : `privacy.html` (remplis les crochets).

## Étape 1 : mettre le jeu en ligne sur ton domaine (1 jour)
1. Achète un nom de domaine (ex. `neonbay-jeu.fr`), environ 10 € par an.
2. Hébergement gratuit possible : Netlify, Cloudflare Pages ou GitHub Pages.
3. Envoie **tout le contenu** du dossier `dist-web/`, y compris le dossier caché `.well-known/`.
4. Vérifie que `https://ton-domaine/privacy.html` s'ouvre.

## Étape 2 : compte développeur Google Play (1 à 3 jours)
1. Crée le compte sur play.google.com/console : **25 $**, une seule fois, pièce d'identité demandée.
2. Compte **personnel** : avant la mise en production, il faudra un **test fermé avec 12 testeurs pendant 14 jours d'affilée**. Compte **organisation** : pas de test obligatoire, mais il faut un numéro D-U-N-S (gratuit, environ 30 jours).
3. Crée un **profil de paiement** (compte marchand) pour pouvoir vendre.
4. Inscris-toi au programme de **frais réduits** pour les petits développeurs, s'il est proposé dans ta console. Les frais ont changé en 2026 : vérifie le taux affiché.

## Étape 3 : créer l'application et le produit (1 heure)
1. Play Console → **Créer une application** : nom « Néon Bay », jeu, payant ou gratuit → **gratuit** (l'achat se fait dans l'app).
2. **Monétiser → Produits → Produits intégrés** → créer :
   - ID du produit : `full_game` (le même que `playSku` dans `js/data.js`)
   - Nom : « Jeu complet », description : « Débloque les 29 niveaux et tout l'arsenal »
   - Prix : 4,99 € (Google convertit pour les autres pays)
   - Activer le produit.

## Étape 4 : fabriquer l'application Android (1 à 2 heures)
**Méthode simple, sans rien installer : PWABuilder**
1. Va sur pwabuilder.com, colle l'adresse de ton site, puis **Package for stores → Android**.
2. Options : identifiant de paquet `com.ton-nom.neonbay`, **Start URL : `/?src=twa`**, affichage **plein écran**, et active **Google Play Billing** si l'option est proposée.
3. Télécharge le paquet : il contient un fichier `.aab` (à envoyer sur Google Play) et la **clé de signature**. **Garde la clé et son mot de passe précieusement** : sans elle, plus de mise à jour possible.

**Méthode en ligne de commande : Bubblewrap**
1. Installe Node.js, puis `npm i -g @bubblewrap/cli`.
2. Remplace dans `android/twa-manifest.json` : `com.CHANGE_MOI.neonbay` et `TON-DOMAINE.com`.
3. `bubblewrap init --manifest https://ton-domaine/manifest.webmanifest`, puis `bubblewrap build`. Bubblewrap installe Java et le SDK Android la première fois.
4. Vérifie que `"playBilling": { "enabled": true }` est bien présent dans le fichier `twa-manifest.json` généré.

## Étape 5 : relier l'app au site (15 minutes)
1. Envoie le `.aab` dans **Tests → Test fermé**.
2. Play Console → **Configuration → Intégrité de l'application → Signature d'application** : copie l'empreinte **SHA-256**.
3. Colle-la dans `android/assetlinks.json` (et remplace le nom du paquet), relance `node tools/build-web.js`, puis renvoie `dist-web/` sur l'hébergeur.
4. Vérifie que `https://ton-domaine/.well-known/assetlinks.json` s'affiche. Sinon, l'app montre une barre d'adresse en haut.

## Étape 6 : tester les achats sans payer
1. Play Console → **Paramètres → Test de licence** : ajoute ton adresse Gmail et celles des testeurs.
2. Installe l'app depuis le lien du test fermé, touche « Jeu complet » puis « Acheter » : Google affiche un achat de test gratuit.
3. Vérifie ensuite :
   - les niveaux 2 à 30 s'ouvrent ;
   - « Restaurer mes achats » fonctionne après avoir effacé les données de l'app ;
   - dans **Commandes**, l'achat est bien **confirmé (acknowledged)**. Un achat non confirmé sous 3 jours est remboursé automatiquement.

## Étape 7 : vérification serveur (recommandée)
Le jeu sait déjà appeler un serveur de vérification. Pour l'activer :
1. Dans la Google Cloud Console, crée un **compte de service**, puis donne-lui l'accès « Gérer les commandes » dans la Play Console (Utilisateurs et autorisations).
2. Déploie `android/verify-purchase.js` en fonction Netlify, avec les variables `GOOGLE_SERVICE_ACCOUNT_JSON` et `PACKAGE_NAME`.
3. Mets son adresse dans `verifyUrl` (`js/data.js`), puis rebuild et renvoie le site.
Sans serveur, le jeu tente de confirmer l'achat directement depuis l'appareil. **Contrôle-le pendant les tests (étape 6)** : si les achats ne passent pas en « confirmé », le serveur devient obligatoire.

## Étape 8 : la fiche du jeu et les formulaires
- **Classification du contenu** (questionnaire IARC) : réponds honnêtement (violence, armes, police). Attends-toi à **PEGI 16**, voire 18.
- **Public cible** : 16 ans et plus. Ne coche pas « enfants ».
- **Sécurité des données** : aucune donnée collectée, aucune donnée partagée ; achats gérés par Google Play.
- **Politique de confidentialité** : l'adresse de `privacy.html`.
- **Fiche** : textes ci-dessous, icône 512x512 (`icons/icon-512.png`), image de présentation 1024x500, au moins 2 captures d'écran (téléphone).

## Étape 9 : test fermé puis production
1. Recrute **12 testeurs**. Ils doivent rester inscrits et ouvrir le jeu régulièrement pendant **14 jours**.
2. Ensuite, Play Console → **Demander l'accès à la production**, réponds aux questions sur le test, puis publie.
3. Prévois **3 à 6 semaines** au total.

## Textes de la fiche Play Store

**Titre (30 caractères max)** : Néon Bay : Mafia en ville

**Description courte (80 max)** : 30 missions, 4 pays, la police aux trousses. Le niveau 1 est gratuit.

**Description longue** :
> Tu arrives à Néon Bay sans un dollar. Trente niveaux plus tard, tu tiens la ville, puis Porto Lumi en Italie, Sierra Verde en Colombie et les ruelles de Morro Azul au Brésil.
>
> Chaque niveau compte 10 étapes : vols de voitures, livraisons contre la montre, fusillades, escortes, courses de nuit, convois à faire sauter. Les étoiles de recherche montent ? Sème la police par les tunnels, repeins ta voiture ou glisse un billet aux agents.
>
> Avec l'argent gagné, tu t'équipes : du pistolet au minigun, gilet pare-balles, nitro, blindage. Sept chefs de gang t'attendent.
>
> Le niveau 1 est gratuit. Un seul achat débloque tout le jeu, sans abonnement ni publicité.
>
> Ville en 3D, personnages en blocs, musique différente dans chaque pays. Se joue au doigt, en portrait comme en paysage.

## Et l'iPhone ?
L'App Store demande une vraie application (Capacitor), un Mac ou un service de compilation en ligne, l'achat intégré d'Apple, et une app qui ne ressemble pas à un simple site (risque de refus, règle 4.2). On s'en occupe une fois Android lancé.
