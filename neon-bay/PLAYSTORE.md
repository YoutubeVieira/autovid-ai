# Néon Bay sur Google Play : le guide (app Android autonome)

Ce guide remplace la méthode « site web + TWA » d'`ANDROID.md`. Ici, pas besoin de site ni de nom de domaine : tout le jeu est **dans l'application** et fonctionne **hors ligne**.

- Nom sur Google Play : **Néon Bay : Mafia en ville**
- Nom sous l'icône du téléphone : **Néon Bay**
- Identifiant de l'app : `com.neonbay.mafia` (voir « Changer l'identifiant » plus bas)
- Achat intégré : `full_game`, **2,99 €**, le niveau 1 reste gratuit.

---

## 1. Sur ton PC : fabriquer le fichier .aab

Le fichier `.aab` est le fichier que tu envoies à Google Play.

### Installer Android Studio (gratuit, une seule fois)
1. Va sur **developer.android.com/studio** et télécharge Android Studio.
2. Installe-le avec les options par défaut. Au premier lancement, laisse-le télécharger le « SDK Android ». C'est long (environ 15 minutes).

### Récupérer le projet
1. Télécharge le fichier **neon-bay-android.zip** que je t'ai envoyé.
2. Fais un clic droit dessus, puis **Extraire tout**. Range le dossier dans un chemin court, par exemple `C:\neonbay\`.
   Évite OneDrive et les chemins avec des accents.
3. Tu obtiens un dossier `neon-bay-android` avec ce guide et le dossier `app-android`.

### Ouvrir le projet
1. Dans Android Studio : **File → Open** (ou **Open** sur l'écran d'accueil).
2. Choisis le dossier **`app-android\android`** (pas `app-android`, bien le sous-dossier `android`).
3. Si Windows demande « Trust project ? », réponds **Trust**.
4. Attends la fin de la **synchronisation Gradle** (barre en bas de la fenêtre). La première fois, Android Studio télécharge ce qui manque : compte 5 à 10 minutes.
   Si un message propose d'installer un composant (« Install missing SDK… »), clique dessus.
   **Ne clique pas** sur « Upgrade Android Gradle Plugin » si on te le propose.

### Créer le fichier .aab signé
1. Menu **Build → Generate Signed App Bundle or APK…**
2. Choisis **Android App Bundle**, puis **Next**.
3. La **clé d'importation** (upload key), la première fois :
   - clique sur **Create new…** ;
   - **Key store path** : par exemple `C:\Users\TON-NOM\neonbay-keys\neonbay-upload.jks` (**hors** du dossier du projet) ;
   - choisis un mot de passe, **Alias** : `upload`, même mot de passe pour la clé ;
   - **Validity** : 25 ans ou plus ; **First and Last Name** : ton nom ou celui de ta société ; **Country Code** : `FR` ;
   - **OK**.
   Les fois suivantes : **Choose existing…** et sélectionne le même fichier `.jks`.
4. **Next**, choisis **release**, puis **Create** (ou **Finish**).
5. À la fin, une bulle « Generate Signed Bundle » apparaît. Clique sur **locate**.
   Le fichier est ici : `app-android\android\app\release\app-release.aab`
   (ou `app-android\android\app\build\outputs\bundle\release\app-release.aab`).

### Sauvegarder la clé : très important
- Copie le fichier **`neonbay-upload.jks`** et son **mot de passe** dans **deux endroits sûrs** : une clé USB et un gestionnaire de mots de passe, par exemple.
- Ne l'envoie jamais par email et ne le mets jamais dans le dossier du projet ni sur GitHub.
- Avec la « signature d'application Google Play » (voir étape 5), une clé perdue peut être remplacée par le support Google, mais cela bloque tes mises à jour pendant plusieurs jours.

### Pour chaque mise à jour
1. Ouvre `app-android\android\app\version.properties` avec le Bloc-notes.
2. Augmente **`versionCode`** de 1 (1, puis 2, puis 3…). Google refuse deux envois avec le même numéro.
3. Change **`versionName`** si tu veux (ex. `1.0.1`) : c'est le numéro que voient les joueurs.
4. Refais **Build → Generate Signed App Bundle**.

### Autre méthode, sans les menus (facultatif)
Dans PowerShell, dans le dossier `app-android` :
```
powershell -ExecutionPolicy Bypass -File .\build-android.ps1 -NewKey   # première fois : crée la clé
powershell -ExecutionPolicy Bypass -File .\build-android.ps1           # fabrique le .aab dans app-android\dist\
```
Le script demande le mot de passe et ne l'enregistre nulle part. Ouvre quand même le projet une fois dans Android Studio avant de l'utiliser.

### Avant d'envoyer : tester sur ton téléphone (conseillé)
1. Branche ton téléphone Android en USB, avec le « débogage USB » activé (Paramètres → À propos → touche 7 fois « Numéro de build », puis Options pour les développeurs).
2. Dans Android Studio, clique sur le triangle vert **Run**.
3. Vérifie : le jeu démarre en paysage et en plein écran, le niveau 1 se lance, le bouton Retour met en pause au lieu de fermer l'app, et le jeu marche en mode avion.
   L'achat ne fonctionne qu'avec une version installée depuis Google Play (test interne, étape 6).

---

## 2. Dans la Play Console (compte organisation)

Ton compte est un compte **organisation** : tu n'as **pas** l'obligation du test fermé avec 12 testeurs pendant 14 jours (elle ne concerne que les comptes personnels récents). Tu peux passer du test interne à la production.

### Étape 1 : profil de paiement
1. **Paramètres → Profil de paiement** : crée-le si ce n'est pas fait (coordonnées bancaires et TVA de ta société). Sans lui, tu ne peux pas vendre.
2. Les frais de Google sur les ventes ont changé ces derniers temps : vérifie le taux affiché dans ta console.

### Étape 2 : créer l'application
1. **Toutes les applications → Créer une application**.
2. Nom : **Néon Bay : Mafia en ville** ; langue : français ; type : **Jeu** ; **Gratuit** (l'achat se fait dans l'app).
3. Accepte les déclarations, puis **Créer**.

### Étape 3 : premier envoi en test interne
Google ne permet de créer le produit qu'après un premier envoi de l'app contenant la facturation. On commence donc par là.
1. **Tester et publier → Tests → Test interne → Créer une release**.
2. Google propose la **signature d'application Google Play** : accepte (**Utiliser la signature d'application Google Play**). Google garde la clé finale, toi tu gardes seulement la clé d'importation.
3. Glisse ton fichier **`app-release.aab`**, donne un nom de version (ex. « 1.0.0 »), puis **Suivant → Enregistrer → Publier**.
4. Onglet **Testeurs** : crée une liste avec ton adresse Gmail (et quelques proches), puis copie le **lien de participation**.

### Étape 4 : créer le produit « Jeu complet »
1. **Monétiser → Produits → Produits intégrés** (ou « Produits ponctuels ») **→ Créer un produit**.
2. **ID du produit : `full_game`** (exactement, il est écrit dans le jeu, `js/data.js`).
3. Nom : « Jeu complet » ; description : « Débloque les 29 niveaux et tout l'arsenal ».
4. Prix : **2,99 €**. Google propose les prix des autres pays : accepte.
5. Enregistre, puis **Activer**.
C'est un achat **non consommable** : le joueur le paie une fois et le garde, même après réinstallation. Le jeu confirme l'achat (« accusé de réception ») tout seul. Sans cette confirmation sous 3 jours, Google rembourse automatiquement.

### Étape 5 : tester l'achat sans payer
1. **Paramètres → Test de licence** : ajoute ton adresse Gmail et celles de tes testeurs.
2. Sur ton téléphone, ouvre le lien de participation, installe l'app depuis Google Play.
3. Dans le jeu : **Jeu complet → Acheter le jeu complet**. Google affiche un paiement de test gratuit.
4. Vérifie :
   - les niveaux 2 à 30 s'ouvrent ;
   - après « Effacer les données » de l'app, le bouton **Restaurer mes achats** retrouve l'achat ;
   - dans la console, **Commandes** : l'achat est bien **confirmé**.

### Étape 6 : remplir le « Contenu de l'application »
Menu **Règles et programmes → Contenu de l'application** (ou « Tableau de bord » : liste des tâches).
- **Règles de confidentialité** : colle l'adresse web de ta politique de confidentialité (voir plus bas). Elle est **obligatoire**.
- **Accès à l'application** : tout est accessible sans compte.
- **Annonces** : **Non**, l'app ne contient pas de publicité.
- **Classification du contenu** (questionnaire IARC) : catégorie **Jeu**. Réponds honnêtement : violence réaliste contre des humains, armes à feu, sang éventuel, activités criminelles, pas de jeux d'argent réels. Attends-toi à **PEGI 16**, voire **PEGI 18**.
- **Public cible** : **16 ans et plus** (ou 18+ si PEGI 18). Ne coche aucune tranche d'âge enfant.
- **Sécurité des données** :
  - « Votre application collecte-t-elle ou partage-t-elle des données ? » → **Non**. La progression reste sur le téléphone, il n'y a ni compte, ni publicité, ni statistiques ; le paiement est géré par Google Play.
  - Si un jour tu actives le serveur de vérification des achats (`verifyUrl` dans `js/data.js`), il faudra déclarer « Historique des achats ». Relis la page d'aide Google « Sécurité des données » avant d'envoyer le formulaire.
- **Application d'actualités, santé, finances, gouvernement** : **Non**.

### Étape 7 : la politique de confidentialité
1. Ouvre `privacy.html` et remplace les crochets : **[TON NOM OU TA SOCIÉTÉ]**, **[ADRESSE]**, **[ADRESSE EMAIL]**, **[DATE]**.
2. Le paragraphe « Services tiers » (Google Fonts) ne concerne pas l'app Android, qui n'utilise pas Internet. Tu peux le garder pour le site ou le retirer.
3. Mets cette seule page en ligne gratuitement, par exemple :
   - **Google Sites** (sites.google.com) : crée un site, colle le texte, publie ;
   - ou **GitHub Pages** : un dépôt public avec le fichier `privacy.html`.
4. Colle l'adresse obtenue dans la Play Console (étape 6) et dans la fiche du jeu.

### Étape 8 : la fiche du jeu (« Fiche principale du Play Store »)
**Textes** (repris d'`ANDROID.md`, avec une correction) :
- **Titre (30 caractères max)** : Néon Bay : Mafia en ville
- **Description courte (80 max)** : 30 missions, 4 pays, la police aux trousses. Le niveau 1 est gratuit.
- **Description longue** :
  > Tu arrives à Néon Bay sans un dollar. Trente niveaux plus tard, tu tiens la ville, puis Porto Lumi en Italie, Sierra Verde en Colombie et les ruelles de Morro Azul au Brésil.
  >
  > Chaque niveau compte 10 étapes : vols de voitures, livraisons contre la montre, fusillades, escortes, courses de nuit, convois à faire sauter. Les étoiles de recherche montent ? Sème la police par les tunnels, repeins ta voiture ou glisse un billet aux agents.
  >
  > Avec l'argent gagné, tu t'équipes : du pistolet au minigun, gilet pare-balles, nitro, blindage. Sept chefs de gang t'attendent.
  >
  > Le niveau 1 est gratuit. Un seul achat débloque tout le jeu, sans abonnement ni publicité.
  >
  > Ville en 3D, personnages en blocs, musique différente dans chaque pays. Se joue au doigt, en mode paysage, même sans connexion.

  (La phrase d'origine disait « en portrait comme en paysage » : l'app est en paysage uniquement.)

**Images** :
- **Icône** : 512 x 512 px, PNG → `icons/icon-512.png`.
- **Image de présentation** : **1024 x 500 px**, PNG ou JPEG, à créer (logo + une scène du jeu, pas de texte trop petit).
- **Captures d'écran téléphone** : au moins **2**, idéalement 4 à 8, en **paysage** (16:9, par exemple 1920 x 1080). Les fichiers `s-home.png`, `s-map.png`, `st-arrival.png`, `st-duel.png` peuvent servir de base. Évite la capture de l'écran de paiement.
- Vidéo YouTube (facultatif) : la bande-annonce.

**Catégorie** : Jeux → **Action**. Coordonnées : une adresse email de contact (obligatoire).

### Étape 9 : production
1. **Tester et publier → Production → Créer une release**.
2. Ajoute le **même `.aab`** depuis la bibliothèque (ou un nouveau, avec un `versionCode` plus grand).
3. **Pays** : choisis où vendre (France, Europe, monde…).
4. **Envoyer pour examen**. Le premier examen prend en général de quelques jours à une semaine.

---

## Points à surveiller

- **Codes de déblocage vendus hors Google Play** : dans l'app, le champ « Tu as déjà un code ? » reste visible (sans lien ni prix du site). Google Play interdit d'**orienter** les joueurs vers un autre moyen de paiement depuis l'app ; accepter un code acheté ailleurs, sans le mentionner, est une zone moins claire. Si Google refuse l'app pour cette raison, mets `playCodes: false` dans `js/data.js` : le champ disparaît de l'app Android, mais pas du site. Il faut ensuite refaire le `.aab` (demande-moi, je relance la synchronisation).
- **Niveau d'API cible** : l'app vise Android 16 (API 36), le niveau exigé par Google Play depuis le 31 août 2026.
- **Bibliothèque de facturation** : Google Play Billing 9 (via le module `cordova-plugin-purchase` 13.20), à jour avec les exigences actuelles.
- **Changer l'identifiant** `com.neonbay.mafia` : c'est possible **seulement avant le premier envoi** sur Google Play, ensuite il est définitif. Demande-moi de le faire (il apparaît dans plusieurs fichiers).
- **Taille** : environ 40 Mo de fichiers de jeu (modèles 3D et vidéos), bien en dessous de la limite de Google.
