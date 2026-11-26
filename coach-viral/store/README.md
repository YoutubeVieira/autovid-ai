# Fiche Play Store de Coach Viral

## Ce qui est prêt

| Élément | Fichier | Format exigé par Google | Statut |
|---|---|---|---|
| Icône | `visuels/icone-512.png` | PNG 512×512, 32 bits, 1 Mo max | ✅ |
| Bannière (« feature graphic ») | `visuels/banniere-1024x500.png` | JPEG ou PNG 24 bits **sans transparence**, 1024×500 | ✅ |
| Captures téléphone (6) | `visuels/capture-1.png` … `capture-6.png` | 2 minimum, 4 pour une meilleure mise en avant, 1080 px minimum | ✅ 1080×1920 |
| Titre (30 caractères max) | `textes.json` | FR, PT-BR, EN | ✅ 28 / 26 / 25 |
| Description courte (80 max) | `textes.json` | FR, PT-BR, EN | ✅ 75 / 67 / 73 |
| Description longue (4 000 max) | `textes.json` | FR, PT-BR, EN | ✅ |

Pour refaire les visuels après une modification de l'application :

```bash
node store/generer-visuels.mjs
```

Le script prend de vraies captures de l'application, remplies avec les exemples de `donnees-demo.mjs`.

## Ce qu'il manque avant de pouvoir publier

1. **Un serveur toujours en ligne, avec une adresse fixe en HTTPS.** Sur le Play Store, l'application est une coquille qui ouvre votre site. L'adresse `trycloudflare.com` du PC change à chaque démarrage et s'éteint avec le PC : elle ne convient pas.
2. **Le paquet Android (.aab)**, fabriqué à partir de l'application web avec Bubblewrap ou PWABuilder (gratuits). Il faut aussi publier un fichier `/.well-known/assetlinks.json` sur le site.
3. **Un compte développeur Google Play** : 25 $ payés une fois.
4. **Le paiement.** Pour un abonnement vendu *dans* une application Play Store, Google impose en principe **sa** facturation (Google Play Billing, 15 %), pas Stripe. Il existe des exceptions, par exemple la facturation alternative pour les utilisateurs de l'Espace économique européen. **À vérifier avant de publier.**
5. **Une politique de confidentialité** en ligne : son adresse est obligatoire. Elle doit dire quelles données partent vers l'IA (Gemini ou Claude), ce qui est fait des voix enregistrées, et combien de temps les vidéos sont gardées.
6. **Le formulaire « Sécurité des données »** et le **questionnaire de classification du contenu**, dans la Play Console.
7. **Les règles de Google sur l'IA générative** : l'application doit permettre de signaler un contenu choquant produit par l'IA. Il faut ajouter un bouton « Signaler » sur les résultats.
8. **Les nouveaux comptes personnels** doivent faire un test fermé avec un nombre minimum de testeurs (12 personnes pendant 14 jours d'après les règles connues) avant de publier. **À vérifier dans la Play Console.**

Les points 4, 7 et 8 sont des règles de Google qui changent : la Play Console donne les exigences à jour.
