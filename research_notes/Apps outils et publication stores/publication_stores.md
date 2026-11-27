# Publier un jeu web (HTML5/three.js, "niveau 1 gratuit + code de déblocage Systeme.io") sur Google Play et l'App Store depuis la France (état novembre 2026)

> Note méthodo : recherche faite le 19/11/2026. Plusieurs domaines étaient bloqués par le réseau de la session (support.google.com, android-developers.googleblog.com, macrumors.com, iclarified.com, thenextweb.com, stash.gg). Les règles Google Play ont donc été vérifiées via developer.android.com (blog officiel) et des extraits de recherche des pages support.google.com. Côté Apple, les pages developer.apple.com (Guidelines, News, support EU, Small Business Program) ont été lues en direct. **Beaucoup de choses ont changé en 2026** (frais Google du 30/06/2026, termes Apple UE du 01/10/2026, arrêt Epic c. Apple de déc. 2025). Les informations antérieures à 2026 trouvées sur des blogs sont souvent périmées.

## 1. Options d'empaquetage : TWA (Bubblewrap/PWABuilder), Capacitor, et risque 4.2 chez Apple

### Takeaway
Pour Android, une TWA (Bubblewrap/PWABuilder) est la voie la plus légère : le jeu reste hébergé sur le site, et le lien est vérifié par Digital Asset Links. Pour iOS, il faut un vrai binaire (Capacitor/WKWebView avec les fichiers du jeu embarqués). La règle 4.2 (« pas un site web reconditionné ») est le principal risque de rejet. Un jeu 3D complet, jouable hors ligne, avec des fonctions natives (Game Center, haptique), s'en défend bien mieux qu'un simple wrapper d'URL.

### Cited Findings
- Les PWA peuvent être distribuées sur le Play Store (Android et ChromeOS) via Trusted Web Activities. Bubblewrap est l'outil CLI open source de Google qui génère la TWA — [Thinktecture](https://www.thinktecture.com/en/pwa/twa-bubblewrap) ; [Google codelab PWA in Play](https://developers.google.com/codelabs/pwa-in-play)
- Il faut prouver le lien entre l'app et le site avec un fichier `.well-known/assetlinks.json`. Si la vérification échoue, l'app affiche le site dans un Custom Tab (avec barre d'URL) au lieu du plein écran — [Chrome Developers, TWA quick start](https://developer.chrome.com/docs/android/trusted-web-activity/quick-start) ; [Android Developers, TWA guide](https://developer.android.com/develop/ui/views/layout/webapps/guide-trusted-web-activities-version2)
- Bubblewrap ne crée plus lui-même le fichier Digital Asset Links : on utilise sa commande `fingerprint` — [Google codelab](https://developers.google.com/codelabs/pwa-in-play)
- Avec Play App Signing, l'empreinte SHA-256 à mettre dans assetlinks.json est celle de la clé de signature de l'app (Play Console → App signing), pas celle de la clé d'upload. Source : retour d'expérience d'un développeur, à vérifier — [DEV Community](https://dev.to/markusbnet/how-i-shipped-my-pwa-to-google-play-as-a-twa-and-what-actually-went-wrong-392j)
- Texte Apple 4.2 : « Your app should include features, content, and UI that elevate it beyond a repackaged website. If your app is not particularly useful, unique, or 'app-like,' it doesn't belong on the App Store. » — [App Review Guidelines](https://developer.apple.com/app-store/review/guidelines/)
- Apple 4.7 autorise les « HTML5 and JavaScript mini apps and mini games » non embarqués dans le binaire. Le développeur reste responsable de leur contenu, qui doit respecter la vie privée, prévoir filtrage et signalement, et passer par la règle 3.1 pour les biens numériques — [App Review Guidelines](https://developer.apple.com/app-store/review/guidelines/)
- Des apps Capacitor ont été rejetées en 4.2 car « not sufficiently different from a mobile browsing experience » — [Apple Developer Forums](https://developer.apple.com/forums/thread/785584) ; [Apple Developer Forums](https://developer.apple.com/forums/thread/812889)
- Exemple d'un jeu indé rejeté en 4.2 puis accepté après ajout des succès Game Center, d'une structure claire en packs de niveaux et de notes de review précises — [blog.kulman.sk (via proxy)](https://hn.jakechampion.name/reader/https://blog.kulman.sk/beating-app-store-review)
- Selon un blog, Apple aurait rejeté environ 2,09 M de soumissions en 2025, dont 415 532 dans la catégorie « Design » (minimum functionality, webview wrappers, spam). Source secondaire, non vérifiée auprès d'Apple — [superappp.com](https://www.superappp.com/blog/most-common-app-store-rejection-reasons)
- Depuis le 28/04/2026, les uploads App Store doivent être compilés avec le SDK iOS 26 ou plus récent. À partir d'avril 2027, ce sera le SDK 27 (Xcode 27), et des captures « iPhone Duo » seront exigées — [Apple Developer News](https://developer.apple.com/news/)

### Inferences
- Android : une TWA convient si le jeu est servi en HTTPS et que le paiement est mis en conformité (voir §3). Capacitor sur Android permet en plus d'embarquer les assets (mode hors ligne) et d'intégrer Play Billing via plugin. Avec une TWA, Play Billing passe par la Digital Goods API, ce qui est plus complexe.
- iOS : il faut embarquer le jeu dans le binaire (Capacitor), et non charger une URL distante. Un jeu three.js complet avec plusieurs niveaux est un « vrai jeu » et non un site d'information, ce qui réduit le risque 4.2. Pour renforcer le dossier : mode hors ligne, Game Center, haptique, sauvegarde locale, pas de navigation web visible, et des notes de review qui expliquent le jeu.
- Mac indispensable ? Xcode ne tourne que sous macOS. Les services CI cloud (Codemagic, GitHub Actions macOS runners, Ionic Appflow) permettent de compiler et signer sans Mac personnel. Ce point n'a pas été vérifié par une source dans cette recherche (voir Gaps).

### Gaps
- PWABuilder : pas de page officielle lue (version actuelle, packaging iOS). Codemagic, GitHub Actions et Appflow : tarifs et faisabilité 2026 non vérifiés.
- Aucun cas documenté trouvé d'un jeu three.js empaqueté avec Capacitor, accepté ou rejeté.

## 2. Comptes et coûts : Google Play et Apple Developer Program

### Takeaway
Google Play : 25 USD une fois. Un compte personnel créé après le 13/11/2023 doit faire un test fermé avec au moins 12 testeurs inscrits pendant 14 jours consécutifs avant d'accéder à la production. Les comptes organisation en sont exemptés, mais demandent un numéro D-U-N-S, gratuit mais long à obtenir (30 jours ou plus). Apple : 99 USD/an et Xcode/macOS (ou CI cloud). Depuis septembre 2026, la vérification d'identité Android s'étend aussi à la distribution hors Play.

### Cited Findings
- Frais Google Play de 25 USD une fois, pour les comptes personnels comme organisation — [synthèse de guides : testerscommunity](https://www.testerscommunity.com/blog/google-play-developer-account-guide) ; [Choicely](https://www.choicely.com/blog/individual-vs-organization-developer-account?hs_amp=true)
- Le compte organisation exige un numéro D-U-N-S, que Google utilise pour vérifier l'identité. Le compte personnel vise « hobbyists and students » mais permet de monétiser — [Google Play Console Help 13634885](https://support.google.com/googleplay/android-developer/answer/13634885) (via extrait de recherche) ; [Help 14177239](https://support.google.com/googleplay/android-developer/answer/14177239)
- Le D-U-N-S est gratuit auprès de Dun & Bradstreet et peut prendre « 30 days or more ». Les services payants « express » sont inutiles — [Google, Introducing the Android Developer Console (PDF)](https://developer.android.com/developer-verification/assets/pdfs/introducing-the-android-developer-console.pdf)
- Test fermé des comptes personnels : au moins 12 testeurs inscrits pendant 14 jours consécutifs. L'exigence initiale (novembre 2023) était de 20 testeurs, ramenée à 12 fin 2024 (une source donne le 11/12/2024). Les tests internes ne comptent pas — [testerscommunity 2026](https://www.testerscommunity.com/blog/google-play-closed-testing-requirements-2026) ; [ProAndroidDev](https://proandroiddev.com/how-to-get-12-testers-for-google-play-closed-testing-and-actually-pass-6a2ab52a0779) ; [extendsclass 2026](https://extendsclass.com/blog/google-plays-closed-testing-requirement-what-developers-need-to-know-in-2026). La page officielle Help 14151465 n'était pas accessible, ces chiffres viennent de sources tierces concordantes.
- 2025-2026 : des refus pour « insufficient engagement » sont signalés. Le seul nombre de testeurs ne suffit plus, il faut une utilisation réelle et des retours. Seules deux sources l'affirment, donc non confirmé — [DEV Community](https://dev.to/tizoc_araujo_3cd9fb67191f/google-play-closed-testing-rejected-for-insufficient-engagement-what-that-actually-means-in-2026-ion)
- Les comptes organisation (avec D-U-N-S) sont exemptés du test fermé — [testerbee](https://testerbee.com/blog/organization-vs-personal-google-play-account-12-testers) ; [choicely](https://www.choicely.com/blog/google-play-12-tester-rule)
- Vérification des développeurs Android (sideloading) : annoncée en août 2025, effective à partir de septembre 2026. Elle impose identité et D-U-N-S même pour distribuer hors Play, et une pièce d'identité officielle pour certains — [Biometric Update](https://www.biometricupdate.com/202508/google-unveils-identity-verification-rules-for-android-app-developers)
- Le pays du profil de paiement, le type de compte et le D-U-N-S ne seraient pas modifiables après création. Non confirmé officiellement — [afkarsoftware](https://afkarsoftware.com/en/blog-detail/google-play-personal-vs-organization-duns-2026/)
- Apple Small Business Program : commission de 15 % (10 % pour les abonnements après la 1re année et pour les participants aux termes UE) si les recettes de l'année précédente sont ≤ 1 M USD, ou pour un nouveau développeur. Inscription manuelle dans App Store Connect, réduction effective 15 jours après la fin du mois fiscal d'approbation — [Apple Small Business Program](https://developer.apple.com/app-store/small-business-program/)

### Inferences
- Pour un auto-entrepreneur français, le compte personnel est le plus simple. Il faut prévoir le test fermé (12 testeurs × 14 jours, avec une vraie activité). Un compte organisation suppose une entreprise avec D-U-N-S (une micro-entreprise peut en demander un) : il évite le test fermé, mais demande plus de délais administratifs.
- Le choix personnel/organisation est quasi irréversible côté profil de paiement. Mieux vaut décider avant de créer le compte.

### Gaps
- Le prix Apple Developer Program en France (99 USD/an, couramment affiché 99 €) n'a pas été revérifié sur developer.apple.com/programs dans cette session.
- Page officielle Google sur le test fermé (support.google.com/…/14151465) inaccessible. À revérifier dans la Play Console.

## 3. Paiements in-app : les codes de déblocage externes sont-ils permis ? (Google Play Billing, DMA, Epic c. Apple, frais)

### Takeaway
**En l'état, le modèle « code acheté sur Systeme.io saisi dans l'app » n'est conforme à aucun des deux stores s'il est la seule façon de débloquer le jeu.**
- Apple 3.1.1 interdit explicitement les « license keys » et impose l'IAP pour « game levels » et « unlocking a full version ». L'exception multiplateforme 3.1.3(b) autorise l'accès à des achats faits sur le web **à condition que les mêmes éléments soient aussi achetables en IAP**.
- Google exige Play Billing pour le contenu numérique consommé dans l'app, sauf adhésion aux programmes de choix de facturation.
- Ce qui a changé en 2026 :
  - **Google** (depuis le 30/06/2026, US/UE/UK) : programme « billing choice » ouvert à tous pour l'UE/UK (facturation alternative ou lien vers son site, à côté de Play Billing). Frais de service de 10 % sur le premier million USD annuel, plus 5 % si on utilise Play Billing.
  - **Apple UE** (depuis le 01/10/2026) : IAP à 15 % pour les petits développeurs, paiement alternatif dans l'app à 10 %, lien vers une offre web à 10 % (taux réduits) sur les ventes faites dans les 7 jours suivant le clic.
  - **Apple US** : les liens et boutons vers un achat externe sont permis sans autorisation préalable. Le niveau de commission sur ces achats est encore en litige.

### Cited Findings
**Apple — texte des Guidelines (lu le 19/11/2026)**
- 3.1.1 : « If you want to unlock features or functionality within your app, (by way of example: subscriptions, in-game currencies, game levels, access to premium content, or unlocking a full version), you must use in-app purchase. Apps may not use their own mechanisms to unlock content or functionality, such as license keys, augmented reality markers, QR codes… » — [App Review Guidelines](https://developer.apple.com/app-store/review/guidelines/)
- 3.1.3(b) Multiplatform Services : « Apps that operate across multiple platforms may allow users to access content, subscriptions, or features they have acquired in your app on other platforms or your web site, including consumable items in multi-platform games, provided those items are also available as in-app purchases within the app. » — [App Review Guidelines](https://developer.apple.com/app-store/review/guidelines/)
- 3.1.1(a) / 3.1.3 : sur le storefront des États-Unis, les entitlements ne sont pas requis pour « buttons, external links, or other calls to action ». Sur les autres storefronts, l'app et ses métadonnées ne peuvent pas diriger vers un autre moyen d'achat que l'IAP, sauf entitlements ou termes spécifiques — [App Review Guidelines](https://developer.apple.com/app-store/review/guidelines/)

**Apple — UE (DMA), termes en vigueur depuis le 01/10/2026**
- Annonce du 18/08/2026. La Core Technology Fee est remplacée par une Core Technology Commission (CTC) de 5 % qui ne s'applique qu'à la distribution hors App Store. L'Initial Acquisition Fee et la Store Services Fee sont supprimées. IAP et paiements alternatifs peuvent coexister dans la même app. Attachment 14 du DPLA — [Apple Developer News](https://developer.apple.com/news/) ; [Apple Newsroom](https://www.apple.com/newsroom/2026/08/apple-announces-changes-for-apps-in-the-european-union/)
- Tableau officiel pour les storefronts UE : IAP 26 % standard / 15 % réduit (Small Business Program). Paiement alternatif dans l'app 20 % / 10 %. « Store services commission » sur une offre hors app avec lien actionnable 15 % / 10 %, pour les ventes conclues dans les 7 jours suivant le clic. En cas de paiement alternatif, le développeur collecte et reverse lui-même la TVA et déclare ses transactions à Apple chaque mois (dans les 15 jours). Les options de paiement doivent être maintenues 12 mois — [Apple, Changes for apps in the EU](https://developer.apple.com/support/apps-in-the-eu/)
- Protections mineurs (UE) : pas d'offre externe vers un site pour les apps de la catégorie Kids ni pour les moins de 13 ans. Pour les 13-17 ans, contrôle parental (« parental gate ») obligatoire — [Apple, Changes for apps in the EU](https://developer.apple.com/support/apps-in-the-eu/)
- Divergence : Ashurst indique 10 % comme taux réduit IAP, alors que la page Apple dit 15 %. Retenir Apple — [Ashurst Perkins Coie](https://www.ashurstperkinscoie.com/en/insights/apple-updates-app-store-developer-terms-in-the-eu/)
- Le calendrier 2025 (suppression de la CTF au 01/01/2026) est remplacé par celui d'août 2026 (01/10/2026) — [synthèse 9to5mac/iphoneincanada 2025](https://www.iphoneincanada.ca/2025/06/27/apple-eu-app-store-update-for-dma/)

**Apple — États-Unis (Epic c. Apple)**
- Le 11/12/2025, la Cour d'appel du 9e circuit (n° 25-2935) a confirmé l'outrage (contempt) contre Apple : la commission de 27 % sur les achats via lien externe et les restrictions de présentation des liens étaient prohibitives. Elle a en revanche annulé l'interdiction totale de commission : Apple peut demander une commission fondée sur ses coûts réels, à fixer par la juge Gonzalez Rogers. Apple peut exiger que les liens externes ne soient pas plus visibles que ses boutons IAP (parité) — [Fenwick](https://www.fenwick.com/insights/publications/ninth-circuit-largely-upholds-ruling-in-epic-v-apple) ; [Courthouse News](https://www.courthousenews.com/ninth-circuit-confirms-contem) ; [NeonPay](https://www.neonpay.com/blog/the-latest-epic-v.-apple-appeal-ruling-december-2025-what-changed-for-game-developers)
- Avril-mai 2026 : Epic aurait obtenu l'annulation d'une suspension, et Apple chercherait à porter l'affaire devant la Cour suprême. Titres seulement, non vérifiés — [MacRumors (titre)](https://www.macrumors.com/2026/04/29/epic-games-wins-reversal-app-store-fee-battle/) ; [pulse.bot](https://www.pulse.bot/legal/blogs/the-ninth-circuit-appeal-ruling-in-epic-v-apple-that-apple-is-seeking-to-overturn-at-the-supreme-cou-b8fb089a-7430-479a-945d-d79fbb4e9886/)

**Google Play**
- Les apps distribuées sur Play qui font payer des fonctions ou du contenu numérique dans l'app doivent utiliser Google Play Billing. Les biens numériques consommables uniquement hors de l'app n'y sont pas soumis. Interdit : un lien direct vers une page de paiement alternatif, ou un langage qui incite à acheter hors de l'app (hors exceptions et programmes) — [Google Play Payments policy, Help 10281818](https://support.google.com/googleplay/android-developer/answer/10281818) (via extraits de recherche ; page non lue directement)
- 24/06/2026, blog officiel : nouveau « billing choice program » ouvert « to all developers globally who provide digital services or content to users within the UK and the EEA » (programmes équivalents aux US). On peut proposer une facturation alternative ou un lien vers son site, à côté de Play Billing, avec un écran de choix personnalisable selon les règles UX de Google — [Android Developers Blog, 24/06/2026](https://developer.android.com/blog/posts/expanded-billing-choice-and-lower-fees-on-google-play)
- À partir du 30/06/2026 (US, EEE, UK), le service fee est séparé du billing fee. Service fee de **10 % sur le premier million USD** de revenus annuels, quel que soit le mode de facturation (Play Billing, alternatif ou lien web), et 10 % sur tous les abonnements. Au-delà, le taux dépend du type d'installation (« new installs » / « existing installs »). Billing fee de 5 % en plus **uniquement** avec Play Billing. Programmes Games Level Up / Apps Experience avec taux réduits dès le 30/09/2026 — [Android Developers Blog](https://developer.android.com/blog/posts/expanded-billing-choice-and-lower-fees-on-google-play)
- Ces changements font suite au règlement Epic c. Google — [9to5Google, 24/06/2026](https://9to5google.com/2026/06/24/google-play-store-external-billing-june-30/) ; [Shopifreaks](https://www.shopifreaks.com/google-starts-cutting-play-store-fees-to-a-flat-10-service-fee-on-the-first-1m-and-allows-external-payment-links-making-good-on-its-epic-games-settlement/)
- L'ancien « External Offers Program » de l'EEE (révisé en août 2025, frais de 5 à 17 % selon les sources) **exigeait d'être enregistré comme entreprise**, et on ne pouvait pas y cumuler Play Billing — [The Register, 20/08/2025](https://www.theregister.com/2025/08/20/google_play_eu_changes/) ; [PYMNTS](https://www.pymnts.com/google/2025/google-play-allows-developers-in-europe-to-promote-offers-outside-app/)
- Les taux au-delà de 1 M USD diffèrent selon les sources (20 %/25 %). L'image du barème officiel n'était pas lisible — [ppc.land](https://ppc.land/google-play-developers-face-25-percent-fee-under-new-structure/)

### Inferences
- **Ce qui sera rejeté** : une app iOS ou Android dont le niveau 2+ ne se débloque que par un code acheté sur Systeme.io, sans IAP ni programme de facturation alternative déclaré (Apple 3.1.1 « license keys » ; Google Payments policy). C'est aussi le cas d'un bouton ou d'un texte « achetez votre code sur notre site » hors cadre autorisé.
- **Options conformes** :
  - (a) **IAP natif seul** (Apple IAP / Play Billing), produit non consommable « Jeu complet ». Coût : 15 % chez Apple (Small Business Program), ou environ 15 % chez Google (10 % de service fee + 5 % de billing fee).
  - (b) **IAP + compatibilité multiplateforme** : l'app accepte aussi les codes Systeme.io pour les clients web existants. C'est autorisé par Apple 3.1.3(b) *si l'IAP est aussi proposé*, à condition de ne pas inciter dans l'app à acheter ailleurs (hors UE/US).
  - (c) **UE/UK chez Google** : adhérer au billing choice program et ajouter un lien vers la page Systeme.io. Coût : 10 % de service fee, sans billing fee. Il faut déclarer les transactions à Google (modalités exactes à lire sur la page 17161464).
  - (d) **UE chez Apple** : offre hors app avec lien vers Systeme.io, 10 % de store services commission (taux réduit) sur les ventes faites dans les 7 jours suivant le clic. Cela implique la déclaration mensuelle à Apple, un engagement de 12 mois et un contrôle parental pour les 13-17 ans. Sur un jeu classé 16+/18+, la question des mineurs pèse moins, mais la vérification d'âge reste à prévoir.
  - (e) **US chez Apple** : lien externe autorisé. La commission est encore incertaine (renvoi devant le tribunal de district).
- L'option (b) est la plus simple pour démarrer. Les options (c) et (d) ajoutent des déclarations et de la conformité fiscale (TVA OSS déjà gérée par Systeme.io/Stripe ?) pour un gain de quelques points seulement.
- Systeme.io ne fournit pas de vérification de code « côté serveur » prête pour une app. Il faudra un petit backend pour valider les codes, ou une liste de codes signés.

### Gaps
- La page officielle Google « billing choice program » (Help 17161464) n'a pas pu être lue. On ne sait pas si un **compte personnel** y est éligible (l'ancien programme exigeait un statut d'entreprise), ni comment se font la déclaration et la facturation des 10 %.
- Le barème Google au-delà de 1 M USD n'a pas été lu (image). Sans importance pour un indé.
- Le statut exact de la commission Apple US sur les liens externes en novembre 2026 n'est pas confirmé (procédure en cours, recours devant la Cour suprême non vérifié).
- Aucune source n'a traité spécifiquement les « codes de déblocage achetés sur un site » chez Google. L'analyse ci-dessus est une lecture des règles générales.

## 4. Contenu : jeu violent à thème criminel (classifications IARC/PEGI, Apple 1.1, police, drogues)

### Takeaway
Un jeu de crime violent est acceptable sur les deux stores s'il est correctement classé (questionnaire IARC sur Play, qui donne PEGI en Europe ; questionnaire d'âge Apple). Il faut s'attendre à **PEGI 16 ou 18**. La référence à des drogues entraîne au minimum PEGI 16. Côté Apple, les points de refus sont la violence réaliste gratuite (1.1.2) et le contenu « mean-spirited » visant un groupe (1.1.1), ce qui peut viser la police si le jeu la cible.

### Cited Findings
- Apple 1.1 : pas de contenu « offensive, insensitive, upsetting, intended to disgust, in exceptionally poor taste, or just plain creepy ». 1.1.1 : contenu diffamatoire, discriminatoire ou « mean-spirited » envers des groupes ciblés. 1.1.2 : « Realistic portrayals of people or animals being killed, maimed, tortured, or abused, or content that encourages violence. » — [App Review Guidelines](https://developer.apple.com/app-store/review/guidelines/)
- Apple a ajouté de nouvelles questions au questionnaire d'âge : réseaux sociaux (réponses requises dès septembre 2026), puis « Shared Location » et « Dating and Relationships » (exigées depuis le 16/11/2026 pour les nouvelles soumissions, et pour toutes les apps au 12/01/2027) — [Apple Developer News](https://developer.apple.com/news/)
- PEGI, descripteur « Drogues » : un jeu qui montre ou évoque des drogues illégales, de l'alcool ou du tabac est toujours PEGI 16 ou 18. PEGI 18 pour une glorification des drogues illégales — [askaboutgames (PEGI/VSC)](https://askaboutgames.com/need-to-know/what-are-content-descriptors) ; [Wikipedia PEGI](https://www.wikipedia.org/wiki/PEGI)
- PEGI 16 : violence d'aspect réaliste, représentation d'activités criminelles. PEGI 18 : « gross violence », meurtres apparemment sans motif, violence envers des personnages sans défense, techniques détaillées utilisables pour commettre des délits — [Wikipedia PEGI](https://www.wikipedia.org/wiki/PEGI) ; [localization.it](https://www.localization.it/2013-03-02-pegi-ratings-explained/)
- Une page Xbox indique que, depuis un changement de critères en 2020, ce type de contenu donne toujours PEGI 18 pour les nouveaux jeux. Cela contredit d'autres sources qui parlent de PEGI 16 — [Xbox Game Ratings](https://www.xbox.com/en-GB/games/gameratings)
- Juillet 2026 : Google a renforcé les outils d'expérience adaptée à l'âge (Play Age Signals API) — [Android Developers Blog, 29/07/2026 (titre)](https://developer.android.com/blog/posts/delivering-safer-age-appropriate-experiences-on-google-play)

### Inferences
- Il faut répondre honnêtement au questionnaire IARC (Play Console › Contenu de l'app › Classification). Une sous-déclaration peut entraîner une suspension. Le jeu ne doit pas viser les enfants (pas de catégorie Kids / Families).
- Pour la police : la montrer comme adversaire dans un jeu de crime est courant et n'est pas interdit en soi. Il faut éviter tout ce qui ressemble à une incitation réelle à la violence contre les forces de l'ordre ou à un contenu haineux, et éviter les logos ou marques réels (police nationale) pour des raisons de propriété intellectuelle et d'image.
- Pour les drogues : pas de mécanique qui « glorifie » ou enseigne la fabrication ou la vente réelle. L'évocation narrative entraîne PEGI 16 au minimum.

### Gaps
- La page officielle IARC/PEGI sur les critères actuels n'a pas été lue, et la divergence PEGI 16/18 sur les drogues n'est pas tranchée.
- La politique Google Play « Violence » et « Contenu inapproprié » (support.google.com) n'a pas pu être lue.

## 5. Vie privée : Data safety, politique de confidentialité, ATT

### Takeaway
Une **politique de confidentialité sur une URL publique** (pas de PDF) est obligatoire sur les deux stores, avec un lien dans la console et dans l'app, même si l'app ne collecte rien. Il faut aussi remplir le **formulaire Data safety** de Google et les « App Privacy labels » d'Apple. Le prompt **ATT** n'est requis que si l'app fait du tracking (pubs ciblées, SDK d'attribution). Dans l'UE, un prompt ATT alternatif existe depuis iOS 27.2, et il est le seul possible en France.

### Cited Findings
- Google : lien vers la politique de confidentialité dans le champ prévu de la Play Console, plus un lien ou un texte dans l'app. URL active, publique, non géo-restreinte, pas de PDF — [Google Play User Data policy, Help 10144311](https://support.google.com/googleplay/android-developer/answer/10144311) (via extrait de recherche)
- Même une app qui ne collecte aucune donnée doit remplir le formulaire Data safety (Policy › App content) et fournir une politique de confidentialité. Le formulaire doit être cohérent avec la politique — [Google Help 10787469](https://support.google.com/googleplay/android-developer/answer/10787469) (via extrait de recherche)
- Apple 5.1.1(i) : lien vers la politique de confidentialité dans App Store Connect et dans l'app. Elle doit identifier les données collectées, comment et pour quels usages. 5.1.2(i) : autorisation explicite via App Tracking Transparency pour tout tracking. On ne peut pas conditionner l'accès au jeu à l'acceptation du tracking ou des notifications — [App Review Guidelines](https://developer.apple.com/app-store/review/guidelines/)
- 16/09/2026 : prompt ATT alternatif possible dans l'UE à partir d'iOS 27.2. Il est **la seule option pour les apps distribuées en Allemagne, France, Italie, Pologne et Roumanie** — [Apple Developer News](https://developer.apple.com/news/)

### Inferences
- Si le jeu n'a ni pub, ni analytics, ni compte, les déclarations sont simples (« aucune donnée collectée »). Ajouter un SDK de pub ou d'analytics (Firebase, etc.) impose de mettre à jour Data safety, les Privacy labels, la politique de confidentialité, voire l'ATT. Un système de codes de déblocage qui envoie l'email ou le code à un serveur est une collecte de données à déclarer.
- Le RGPD s'applique en parallèle (mentions légales, base légale). La politique Systeme.io existante devra être complétée pour l'app.

### Gaps
- Privacy manifests d'Apple (fichier PrivacyInfo.xcprivacy, exigé pour certains SDK) : non vérifié dans cette session. À contrôler pour les plugins Capacitor.

## 6. Calendrier pratique et checklist

### Takeaway
Comptez environ 3 à 6 semaines pour Android avec un compte personnel (création et vérification du compte, au moins 14 jours de test fermé, revue de production), et environ 1 à 3 semaines pour iOS (inscription au programme, build, revue souvent en 24-48 h, plus d'éventuels allers-retours 4.2 ou 3.1.1). Le chemin critique est **la refonte du paiement** (IAP) et **le test fermé Google**.

### Cited Findings
- Test fermé de 14 jours consécutifs avec au moins 12 testeurs pour les comptes personnels — [testerscommunity](https://www.testerscommunity.com/blog/google-play-closed-testing-12-testers-14-days)
- D-U-N-S en 30 jours ou plus si l'on choisit un compte organisation — [Google PDF](https://developer.android.com/developer-verification/assets/pdfs/introducing-the-android-developer-console.pdf)
- Small Business Program : réduction effective environ 15 jours après la fin du mois fiscal d'approbation. Il faut donc s'y inscrire **avant** les premières ventes — [Apple](https://developer.apple.com/app-store/small-business-program/)
- SDK iOS 26 minimum depuis le 28/04/2026, SDK 27 à partir d'avril 2027 — [Apple Developer News](https://developer.apple.com/news/)

### Inferences — checklist proposée
1. **Décision de modèle de paiement** : IAP non consommable « Jeu complet », plus acceptation des codes web existants (3.1.3(b)). Dans les deux apps, aucun texte ni lien vers Systeme.io hors programmes UE/US.
2. **Comptes** : Google Play (25 USD, compte personnel, vérification d'identité) ; Apple Developer Program (99 USD/an) ; inscription au Small Business Program ; contrat Paid Apps et coordonnées bancaires et fiscales (formulaires W-8BEN pour Apple/Google).
3. **Build Android** : Capacitor (assets embarqués, plugin Play Billing) ou TWA (assetlinks.json avec l'empreinte de la clé de signature Play). Bundle AAB signé.
4. **Build iOS** : Capacitor, Xcode avec SDK 26+ (Mac ou CI cloud), StoreKit IAP, Game Center et haptique pour le 4.2, mode hors ligne.
5. **Backend de déblocage** : validation des reçus IAP, et des codes Systeme.io pour le multiplateforme.
6. **Conformité** : politique de confidentialité (URL HTML), Data safety, App Privacy labels, ATT seulement en cas de tracking, questionnaire IARC (PEGI 16/18 attendu), questionnaire d'âge Apple (y compris les nouvelles questions 2026).
7. **Fiche store** : captures d'écran, icône, description sans mention d'achat externe, notes de review Apple expliquant le gameplay et le déblocage (identifiants ou code de test pour le reviewer).
8. **Google, test fermé** : recruter au moins 12 testeurs (groupe Google), 14 jours d'usage réel, puis demande d'accès production (questionnaire).
9. **Soumission et revue**, puis gestion des rejets éventuels (4.2 → ajouter de la profondeur native ; 3.1.1 → retirer toute mention de code ou de site).

### Gaps
- Aucune source officielle 2026 n'a été trouvée sur les délais moyens de revue Apple ou Google. Les durées ci-dessus sont des estimations.
