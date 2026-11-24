# Néon Bay : veille outils gratuits, assets CC0, Play Store et sensations de tir (24 novembre 2026)

## Comment lire ce document

- **[FAIT]** : chiffre ou information lus sur la source citée (registre npm, GitHub, page officielle).
- **[ESTIMATION]** : chiffre d'un outil tiers (AppGoblin, AppMagic, Sensor Tower, etc.) ou ordre de grandeur que je propose.
- **[RÉSUMÉ DE RECHERCHE]** : information obtenue par le moteur de recherche alors que la page elle-même était inaccessible depuis cette session. Il faut la vérifier avant de s'en servir dans un document public.
- Ce rapport ne reprend pas ce qui est déjà dans `AUDIT-COMPLET.md` (poids des modèles, chargement progressif, monétisation actuelle) ni dans `RECHERCHE-AAA.md` (revenus de Gangstar Vegas, CSR 2, Car Parking, GTA mobile). Il le complète.
- **Rien n'a été installé, téléchargé ni modifié dans le code.**

**Sites que je n'ai pas pu ouvrir** (bloqués par le réseau de la session, erreur DNS) : play.google.com, kenney.nl, quaternius.com, quaternius.itch.io, opengameart.org, polyhaven.com, docs.ambientcg.com, poly.pizza, sensortower.com, pocketgamer.biz, mobilegamer.biz, meshoptimizer.org, digitalproduction.com, cdn.jsdelivr.net. Pour ces sites, je me suis appuyé sur les résumés du moteur de recherche (marqués comme tels). Les registres npm et GitHub étaient accessibles.

---

## 0. Ce que le projet sait déjà faire (vérifié dans le code)

Le `vendor/GLTFLoader.js` (r128) du projet contient déjà les branchements suivants :
- `setMeshoptDecoder` (extension `EXT_meshopt_compression`) ;
- `setDRACOLoader` ;
- `setKTX2Loader` (`KHR_texture_basisu`) ;
- `KHR_mesh_quantization` ;
- `EXT_texture_webp`.

Il ne gère **pas** `EXT_mesh_gpu_instancing`, qui n'est arrivé que dans des versions plus récentes de three.js. Conséquence : les options d'instanciation des outils de compression (`gltfpack -mi`, `gltf-transform instance`) produiraient des fichiers que r128 ne sait pas lire correctement. Il faut les éviter.

Le projet a aussi un contrôle automatique, `tools/blender/check_glb_three.js`. Il charge chaque .glb dans three r128 et vérifie des « contrats » : noms des nœuds comme `Wheel_FL` ou `HandR`, noms des matériaux comme `Paint` ou `Skin`, clips d'animation, nombre de triangles. **Tout fichier compressé doit repasser ce contrôle**, car les outils d'optimisation fusionnent ou renomment volontiers les nœuds et les matériaux.

---

## 1. Outils GitHub et npm gratuits, compatibles three.js r128

### 1.1 Compression des modèles

| Outil | Licence | Dernière version | Compatible r128 en UMD ? | Gain attendu | Effort |
|---|---|---|---|---|---|
| **gltfpack / meshoptimizer** (zeux) | MIT [FAIT] ([GitHub](https://github.com/zeux/meshoptimizer), [README gltfpack](https://github.com/zeux/meshoptimizer/blob/master/gltf/README.md)) | 1.3.0, publiée le 25/09/2026 [FAIT] ([registre npm](https://registry.npmjs.org/meshoptimizer)) ; 8,9 k étoiles | **Oui, avec des précautions.** Le décodeur est fourni par three r128 lui-même : `examples/js/libs/meshopt_decoder.js` ([three r128](https://github.com/mrdoob/three.js/tree/r128/examples/js/libs)). La prise en charge dans three date de r122 [FAIT] (README gltfpack). N'utiliser que `-c` (extension EXT). **Ne pas utiliser `-cz` ni `-ce khr`** : ils produisent `KHR_meshopt_compression`, inconnu de r128. Je n'ai pas pu confirmer que le décodeur de 2021 lit tout ce que produit `-cc` avec gltfpack 1.3 : à tester. | Données de sommets 2 à 4 fois plus petites que des données déjà quantifiées [FAIT, README meshoptimizer]. Pour Néon Bay, je vise −50 à −70 % sur les ~5 Mo de .glb [ESTIMATION, cohérente avec l'audit] | Faible : une commande par fichier, plus 3 lignes de chargement. Garder `-kn` (conserve les nœuds nommés) et `-km` (conserve les matériaux), puis repasser `check_glb_three.js` |
| **Draco** (Google) | Apache-2.0 [FAIT] ([GitHub](https://github.com/google/draco)) | 1.5.9 (date non affichée) ; 7,6 k étoiles | **Oui.** r128 fournit `examples/js/loaders/DRACOLoader.js` (UMD) et `examples/js/libs/draco/` ([three r128 loaders](https://github.com/mrdoob/three.js/tree/r128/examples/js/loaders)) | Souvent plus compact que meshopt sur la géométrie seule. En revanche, le décodeur WASM (~300 Ko, ordre de grandeur non vérifié) se charge en plus, le décodage est plus lent, et Draco ne compresse pas les animations | Faible. **Choisir meshopt OU Draco, pas les deux.** Je recommande meshopt : le décodeur est plus léger, il compresse aussi les animations des humains, et il décode plus vite sur un téléphone d'entrée de gamme |
| **KTX2 / Basis Universal** (textures compressées GPU) | Basis : Apache-2.0 | n.d. | **Non en UMD.** Dans r128, `KTX2Loader.js` n'existe qu'en module ES (`examples/jsm/loaders/`), pas dans `examples/js/` [FAIT] ([jsm r128](https://github.com/mrdoob/three.js/tree/r128/examples/jsm/loaders)). r128 a seulement `BasisTextureLoader.js` en UMD (format .basis, ancien). Il faudrait porter le module à la main | Forte baisse de la mémoire GPU des textures | **Élevé et risqué. À ne pas faire maintenant.** Utiliser plutôt **WebP** (`EXT_texture_webp`, déjà géré par le GLTFLoader du projet) |
| **gltf-transform** (CLI, Don McCurdy) | MIT [FAIT] ([GitHub](https://github.com/donmccurdy/glTF-Transform)) ; 2,1 k étoiles | 4.5.1, publiée le 28/09/2026 [FAIT] ([registre npm](https://registry.npmjs.org/@gltf-transform/cli)) | **Oui pour les fichiers produits**, si on évite `instance`, KTX2 (`uastc`, `etc1s`) et `-cz`. Commandes utiles : `inspect`, `resize`, `webp`, `meshopt`, `draco`, `dedup`, `prune` | Réduction des textures (redimensionner à 512 ou 1024 px, passer en WebP), suppression des doublons, rapport de poids par fichier (`inspect`) | Faible à moyen. **Risque de sécurité :** la CLI tire 21 dépendances, dont `sharp`, qui télécharge un binaire natif à l'installation ([dépendances npm](https://registry.npmjs.org/@gltf-transform/cli/latest)). L'installer dans un dossier ou un conteneur isolé, épingler la version et ne pas lancer de scripts inconnus. `optimize` applique beaucoup de transformations à la fois : préférer des commandes une par une |

**Procédure conseillée (à faire plus tard, pas ici) :**
1. Lancer `gltf-transform inspect` sur les 24 .glb pour savoir si le poids vient des textures ou de la géométrie.
2. Si ce sont les textures : `resize` (1024 px au maximum, 512 px pour les armes) puis `webp`.
3. Ensuite : `gltfpack -c -kn -km` (sans `-mi`, `-cz`, `-tc`).
4. Repasser `check_glb_three.js`, puis comparer le poids et la fréquence d'images.
5. Côté chargement, appeler `loader.setMeshoptDecoder(MeshoptDecoder)` avec le fichier `meshopt_decoder.js` de r128. Le décodeur exige WebAssembly, que Chrome Android fournit ([README gltfpack](https://github.com/zeux/meshoptimizer/blob/master/gltf/README.md)).

**Sécurité :** gltfpack existe en binaire natif (pages Releases de GitHub) ou en paquet npm (`gltfpack` 1.3.0, MIT, [npm](https://registry.npmjs.org/gltfpack/latest)). Si on prend le binaire, ne le télécharger que depuis la page officielle `zeux/meshoptimizer` et vérifier l'empreinte. La version npm (WASM) est plus lente mais n'exécute pas de code natif. **Ne jamais livrer ces outils dans le jeu :** ils servent uniquement sur le poste de fabrication.

### 1.2 Performance

| Outil | Licence | Dernière version | Compatible r128 ? | Gain | Effort |
|---|---|---|---|---|---|
| **three-mesh-bvh** (gkjohnson) | MIT [FAIT] ([GitHub](https://github.com/gkjohnson/three-mesh-bvh)) ; 3,6 k étoiles | 0.10.0, publiée le 24/11/2026 [FAIT] ([npm](https://registry.npmjs.org/three-mesh-bvh)) | **Pas la version actuelle**, qui exige three ≥ 0.159 [FAIT] ([npm 0.10.0](https://registry.npmjs.org/three-mesh-bvh/latest)). **Épingler 0.5.24** (13/05/2023, dernière 0.5.x), qui accepte three ≥ 0.123 et fournit un build UMD `build/index.umd.cjs` [FAIT] ([npm 0.5.24](https://registry.npmjs.org/three-mesh-bvh/0.5.24)). Je n'ai pas pu lire l'en-tête UMD (jsDelivr inaccessible). Il faut vérifier qu'il lit bien `window.THREE` sans bundler | Lancers de rayons (tirs, visée, caméra qui ne traverse pas les murs) 10 à 100 fois plus rapides sur les maillages lourds [ESTIMATION, ordre de grandeur courant] | Moyen. **Risque :** une version de 2023 ne recevra plus de correctifs. N'en vaut la peine que si le profilage montre que le `Raycaster` coûte cher. Pour des collisions simples (boîtes et sphères), un découpage maison en grille suffit |
| **InstancedMesh** (dans three) | MIT | inclus dans r128 ([source r128](https://github.com/mrdoob/three.js/blob/r128/src/objects/InstancedMesh.js)) | **Oui.** `BatchedMesh` n'existe pas en r128 (introduit bien plus tard) | Un seul appel de dessin pour les lampadaires, climatiseurs, fenêtres, arbres, douilles et impacts de balles. C'est le premier gain sur mobile, où le nombre d'appels de dessin limite tout | Faible à moyen. Fusionner aussi le décor statique avec `BufferGeometryUtils.mergeBufferGeometries` (fourni en UMD dans r128 : [utils r128](https://github.com/mrdoob/three.js/tree/r128/examples/js/utils)) |
| **LOD** (dans three) | MIT | inclus dans r128 ([source r128](https://github.com/mrdoob/three.js/blob/r128/src/objects/LOD.js)) | Oui | Moins de triangles au loin pour les voitures et les passants | Faible si la chaîne Blender exporte 2 niveaux, par exemple avec un modificateur Decimate. `gltfpack -si 0.5` peut aussi simplifier un maillage |
| **stats.js** (mrdoob) | MIT ; 9,2 k étoiles ([GitHub](https://github.com/mrdoob/stats.js)) | Pas de version datée sur GitHub | Oui : `stats.min.js` est fourni dans `examples/js/libs` de r128 | Compteur d'images par seconde à l'écran, à n'afficher qu'en mode debug | Très faible. Aucune nouvelle dépendance |
| **Spector.js** (BabylonJS) | MIT ; 1,6 k étoiles ([GitHub](https://github.com/BabylonJS/Spector.js)) | 0.9.35 cité dans le README (date non affichée) | Indépendant de three (capture WebGL) | Capture une image et liste chaque appel de dessin, chaque shader et chaque texture : idéal pour trouver ce qui coûte | Faible. **Sécurité :** l'extension de navigateur demande l'accès à toutes les pages. Ne l'activer que pendant les sessions de profilage, et ne jamais l'inclure dans le build du store |
| `renderer.info` (dans three) | MIT | inclus | Oui | Nombre d'appels de dessin et de triangles par image, sans aucun outil externe | Très faible |

Pour mesurer sur un vrai téléphone, le débogage à distance de Chrome (`chrome://inspect`) fonctionne avec une TWA. Ce n'est pas une dépendance du projet.

### 1.3 Post-traitement léger pour mobile

| Outil | Licence | Version | Compatible r128 ? | Remarque |
|---|---|---|---|---|
| **pmndrs/postprocessing** | Zlib [FAIT] ([GitHub](https://github.com/pmndrs/postprocessing)) ; ~3 k étoiles | 6.39.6, publiée le 01/11/2026, exige three ≥ 0.168 et < 0.188 [FAIT] ([npm](https://registry.npmjs.org/postprocessing/latest)) | **Non pour la version actuelle.** La dernière compatible r128 est **6.22.5** (30/08/2021, three ≥ 0.102 et < 0.133) [FAIT] ([npm 6.22.5](https://registry.npmjs.org/postprocessing/6.22.5)). Son build `build/postprocessing.js` exposait historiquement une variable globale, mais je n'ai pas pu le vérifier (CDN inaccessible) | Gros avantage : elle fusionne plusieurs effets en une seule passe, ce qui est moins coûteux sur mobile. Mais une version de 2021 ne recevra plus de correctifs. **À n'envisager que si le bloom actuel coûte trop cher** |
| **Passes fournies par three r128** (`examples/js/postprocessing`) | MIT | r128 | **Oui, en UMD** : `EffectComposer`, `UnrealBloomPass`, `SMAAPass`, `SSAOPass`, `SAOPass`, `ShaderPass`, plus `FXAAShader`, `ColorCorrectionShader` et `VignetteShader` dans `examples/js/shaders` ([postprocessing r128](https://github.com/mrdoob/three.js/tree/r128/examples/js/postprocessing), [shaders r128](https://github.com/mrdoob/three.js/tree/r128/examples/js/shaders)) | Zéro nouvelle dépendance. C'est la voie recommandée |

**Recommandation mobile :**
- **FXAA** (une seule passe, très bon marché) plutôt que SMAA (trois passes) sur téléphone. SMAA ou l'antialiasing natif sont réservés au PC.
- **Pas de SSAO** en temps réel sur mobile. Il coûte trop cher pour un jeu en vue de dessus. À la place, utiliser l'occlusion « cuite » dans Blender (texture d'AO), ou les ombres de contact déjà présentes.
- **Vignette et étalonnage** dans le même `ShaderPass` que l'étalonnage par pays existant, pour éviter une passe de plus.
- **Bloom** à demi-résolution la nuit seulement. C'est déjà le cas d'après l'audit.

### 1.4 Animation de personnages (alternatives libres à Mixamo)

**Mixamo :** il est gratuit et utilisable commercialement « libre de droits », sans attribution obligatoire [FAIT, FAQ Adobe] ([FAQ Mixamo](https://helpx.adobe.com/en/creative-cloud/faq/mixamo-faq.html)). Mais **il n'est pas libre** :
- les fichiers ne doivent pas être redistribués seuls [RÉSUMÉ, propos d'un employé Adobe sur le forum] ([forum Adobe](https://community.adobe.com/t5/mixamo-discussions/mixamo-faq-licensing-royalties-ownership-eula-and-tos/td-p/13234775)) ;
- il faut un compte Adobe ;
- les conditions ont changé au fil du temps.

**Risque spécifique à Néon Bay :** dans un jeu web, les .glb sont téléchargeables par n'importe qui depuis le navigateur. Une animation Mixamo y devient de fait un fichier redistribué. C'est une zone grise : je recommande de **ne pas utiliser Mixamo** dans la version web.

| Alternative | Licence | Contenu utile | Remarques |
|---|---|---|---|
| **Quaternius – Universal Animation Library** (1 et 2) | **CC0** [RÉSUMÉ DE RECHERCHE] ([page officielle](https://quaternius.com/packs/universalanimationlibrary.html), [UAL 2](https://quaternius.com/packs/universalanimationlibrary2.html), [Godot Asset Store](https://store.godotengine.org/asset/quaternius/universal-animation-library/)) | Plus de 120 animations sur un squelette humanoïde unique, en glTF, FBX et OBJ : déplacements, combat, interactions | Version Standard gratuite. Les versions Pro et Source (avec les .blend) sont payantes [RÉSUMÉ] ([itch.io](https://quaternius.itch.io/universal-animation-library)). Les fichiers .blend facilitent le reciblage. Sites non ouverts |
| **Quaternius – personnages animés** (Animated Characters, Universal Base Characters) | CC0 annoncé, mais **licence non confirmée pour ces packs précis** [RÉSUMÉ] ([itch.io Quaternius](https://quaternius.itch.io/)) | Passants supplémentaires | À vérifier pack par pack |
| **KayKit (Kay Lousberg)** | **CC0**, « usage personnel et commercial, sans attribution » [RÉSUMÉ] ([Resource Bits](https://kaylousberg.itch.io/resource-bits), [City Builder Bits](https://kaylousberg.itch.io/city-builder-bits)) | Personnages et décors stylisés | Style « jouet », peut-être trop mignon pour Néon Bay |

**Reciblage (retargeting) :**
- **Dans Blender** (recommandé, car la chaîne du projet est déjà dans Blender) : renommer ou associer les os de la bibliothèque UAL aux os du projet (`Hips`, `Spine`, `UpperArm.L`, etc.), cuire l'animation sur le squelette Néon Bay, puis exporter. Les noms de clips attendus (`Idle`, `Walk`, `Run`, `Aim`, `AimRifle`, etc.) restent ainsi intacts pour `check_glb_three.js`.
- **Dans three r128** : `SkeletonUtils.retarget` existe en UMD dans `examples/js/utils/SkeletonUtils.js` ([utils r128](https://github.com/mrdoob/three.js/tree/r128/examples/js/utils)). Mais ce reciblage au chargement est fragile et coûte du temps CPU au lancement. À éviter.

---

## 2. Assets 3D gratuits utilisables commercialement

| Source | Licence exacte | Attribution | Utile pour Néon Bay | Poids typique |
|---|---|---|---|---|
| **Kenney** | **CC0** (domaine public) pour tous les assets des pages d'assets [RÉSUMÉ, page support Kenney] ([kenney.nl/support](https://kenney.nl/support)) | Non obligatoire, appréciée. **Le logo Kenney est réservé** et ne doit pas être utilisé | **Car Kit** : 45 fichiers, v3.0 en janvier 2026, OBJ/FBX/glTF ([page](https://kenney.nl/assets/car-kit), [itch.io](https://kenney-assets.itch.io/car-kit)). **City Kit** Suburban, Industrial, Commercial et Roads ([OGA Industrial](https://opengameart.org/content/city-kit-industrial), [Roads](https://gamedev.net/news/5156-city-kit-roads/)). **Retro Urban Kit**, avec GLB confirmé ([OGA](https://opengameart.org/content/retro-urban-kit)). **Blaster Kit** : armes de science-fiction façon jouet, plus de 20 modèles ([itch.io](https://kenney-assets.itch.io/blaster-kit)) | Quelques dizaines de Ko par modèle low-poly [ESTIMATION, non vérifiée car site inaccessible]. Packs complets de quelques Mo |
| **Quaternius** | **CC0** [RÉSUMÉ] ([liste OGA des uploads CC0](https://opengameart.org/content/all-cc0-uploader-quaternius)) | Non obligatoire | **Downtown City MegaKit** : plus de 300 pièces modulaires de quartiers façon Boston ou New York, glTF, CC0 ([page](https://quaternius.com/packs/downtowncitymegakit.html)). C'est le plus utile pour densifier la ville. **Low Poly Guns Pack** (CC0, [OGA](https://opengameart.org/content/low-poly-guns-pack)), **LowPoly Cars** (CC0, [OGA](https://opengameart.org/content/lowpoly-cars)), **Modular Street Pack** (FBX, OBJ et Blend seulement, [OGA](https://opengameart.org/content/lowpoly-modular-street-pack)), plus les animations UAL ci-dessus | Pièces de décor : quelques dizaines à quelques centaines de Ko. Personnages animés : 0,5 à 2 Mo [ESTIMATION]. Le style low-poly propre devra être harmonisé avec les modèles Blender du projet |
| **KayKit (Kay Lousberg)** | **CC0 1.0** [RÉSUMÉ] ([City Builder Bits](https://kaylousberg.itch.io/city-builder-bits)) | Non obligatoire | Routes, feux, lampadaires, véhicules, parcs ([version Unity, description](https://marketplace.unity.com/packages/3d/environments/urban/kaykit-city-builder-bits-for-unity-282686)) | glTF confirmé pour d'autres packs (Prototype Bits, Furniture Bits), **pas confirmé pour City Builder Bits** |
| **Poly Haven** | **CC0** pour les HDRI, les textures et les modèles [RÉSUMÉ, FAQ] ([FAQ](https://polyhaven.com/faq), [licence](https://polyhaven.com/license)) | Non obligatoire. Interdit de se dire l'auteur ou de re-licencier. Les avatars de chats du site sont en CC-BY (exception sans intérêt pour nous) | **HDRI urbains de nuit** pour la carte d'environnement (reflets des voitures). Textures d'asphalte, de béton et de briques. **À noter :** Poly Haven a **retiré ses modèles d'armes** parce que les designs réels qu'ils reproduisent sont une zone grise juridique [RÉSUMÉ] ([FAQ](https://polyhaven.com/faq)). C'est un signal pour Néon Bay : armes génériques, jamais de répliques de modèles réels nommés | HDRI : choisir 1K (environ 1 à 2 Mo en .hdr) pour le jeu. Les versions 4K et plus pèsent des dizaines de Mo [ESTIMATION]. Une carte d'environnement 256 px suffit sur mobile |
| **ambientCG** | **CC0 1.0**, usage commercial et redistribution autorisés [RÉSUMÉ] ([licence](https://docs.ambientcg.com/license), [guide tiers](https://licenseorg.com/guide/3d-assets/ambientcg)) | Non obligatoire (texte de crédit fourni, facultatif) | Plus de 2 000 matériaux PBR : asphalte mouillé, métal, béton, néons. Décalques (graffitis, taches) | Télécharger en 1K JPG. Une archive 1K complète (couleur, normale, rugosité, AO) fait quelques Mo. En jeu, ne garder que 2 ou 3 cartes, converties en WebP |
| **Poly Pizza** | **Licence mixte : CC0 OU CC-BY, modèle par modèle** [RÉSUMÉ] ([guide](https://app.cinevva.com/guides/free-3d-model-sites), [bundle KayKit sur Poly Pizza](https://poly.pizza/bundle/City-Builder-Bits-1wLdnIddSx)) | **CC-BY : attribution obligatoire** (titre, auteur, lien, version de licence). L'archive « Poly by Google » est surtout en CC-BY | Accessoires urbains variés en GLB | Petits fichiers GLB low-poly |

**Signalements (licence floue ou non commerciale) :**
- **Poly Pizza :** pas de « tout CC0 ». Il faut contrôler chaque modèle et tenir un fichier `CREDITS.md` pour les modèles CC-BY.
- **Sketchfab, TurboSquid gratuits, CGTrader gratuits :** les licences varient selon le modèle (CC-BY-NC fréquent, licences éditoriales). À exclure sauf vérification une par une. Les packs « city » de CGTrader apparus dans les recherches sont des produits payants ou sous licence propre.
- **OpenGameArt :** mélange de CC0, CC-BY, CC-BY-SA et GPL. Seuls les packs marqués CC0 sont sans contrainte. CC-BY-SA impose de partager les dérivés sous la même licence, ce qui est **à éviter**.
- **Mixamo :** voir 1.4. Gratuit mais pas libre, et risqué sur le web.
- **Tout modèle reprenant une marque** (logo de voiture, arme nommée, enseigne réelle) **ou un élément de GTA** est exclu, même s'il est en CC0. La licence CC0 couvre le droit d'auteur du créateur, pas les marques de tiers.
- **Bonne pratique :** pour chaque asset retenu, noter dans `CREDITS.md` l'URL, la date, la licence et une copie du fichier de licence du pack. Kenney et Quaternius en livrent un dans chaque archive.

---

## 3. Ce qui marche sur le Play Store dans notre genre

### 3.1 Tableau des jeux (Google Play inaccessible : chiffres de trackers ou résumés de recherche)

| Jeu | Modèle | Note et volume | Ce qu'aiment les 4-5 étoiles | Ce que détestent les 1-2 étoiles |
|---|---|---|---|---|
| **Gangstar Vegas** (Gameloft, 2013) | Gratuit, achats intégrés et publicités. Classé Mature 17+, avec « jeux d'argent simulés » | 4,4 sur ~6,85 M avis, plus de 100 M téléchargements [RÉSUMÉ DE RECHERCHE de la fiche Google Play, non ouverte] ([fiche App Store](https://apps.apple.com/hk/app/gangstar-vegas/id571393580?l=en)) | Grande ville libre, nombreux véhicules et armes, gratuit | **Publicités** en pleine mission, à la pause et à l'ouverture de la carte. Retrait des pubs jugé trop cher. Système d'énergie et VIP. Ralentissements, plantages, progression perdue en changeant d'appareil. Support qui ne répond pas [RÉSUMÉ, avis App Store] |
| **Dude Theft Wars** (Poxel Studios) | Gratuit, publicités et achats intégrés | 4,3 sur ~1,3 M avis [ESTIMATION, agrégateur] ([Grand Screen](https://grand-screen.com/games/dude-theft-wars-fps-open-world/)) ; plus de 100 M installations [AppBrain] ([AppBrain](https://www.appbrain.com/dev/Poxel+Studios+Games/)) | **Physique ragdoll drôle, bac à sable chaotique, ton léger**, multijoueur entre amis, secrets et codes de triche | Progression qui devient longue (« grind »), pubs, contrôles parfois maladroits, pas de sauvegarde dans le cloud (progression perdue), gyroscope cassé après une mise à jour [RÉSUMÉ, agrégateur généré automatiquement : fiabilité moyenne] |
| **Grand Gangsters 3D** (Doodle Mobile, 2016) | Gratuit, publicités et achats intégrés | 4,01 sur ~511 k notes, ~72,6 M installations, dernière mise à jour le 19/08/2024 [ESTIMATION AppGoblin] ([AppGoblin](https://appgoblin.info/apps/com.wordsmobile.grandfightgangsters)) | n.d. (pas d'avis trouvés) | n.d. |
| **Vegas Crime Simulator** (Naxeex) | Gratuit, achats intégrés, achat « NO ADS » (vu sur le jeu jumeau Miami) | 4,1 [RÉSUMÉ] ; installations non trouvées ([App Store](https://apps.apple.com/us/app/-/id1081817078)) | n.d. | Fréquence des pubs [source secondaire peu fiable] |
| **Mad City Crime 2** (Extereme Games) | Gratuit | Entre 10 et 100 M installations [AppBrain] ([AppBrain](https://www.appbrain.com/dev/Extereme+Games/)). La version App Store est notée 3,3 [ESTIMATION] ([App Store](https://apps.apple.com/app/id1034310786)) | n.d. | n.d. |
| **Real Gangster Crime** (Naxeex) | Gratuit, publicités | **Chiffres non vérifiables.** Le « 100 M+ » n'apparaît que sur un site d'APK modifiés, donc non retenu | n.d. | n.d. |
| **Gangstar Mirage City** (Gameloft, édité par Level Infinite) | Gratuit, monde ouvert en ligne : empire d'affaires, véhicules personnalisés, braquages, guerres de gangs, territoires | Lancement anticipé le 20/08/2026 après 30 M pré-inscriptions [FAIT, éditeur] ([Level Infinite](https://www.levelinfinite.com/news/gangstar-mirage-city-is-live-in-select-regions/)). N°1 mondial de la croissance des téléchargements en août 2026 selon Sensor Tower [RÉSUMÉ, page non ouverte] ([Sensor Tower](https://sensortower.com/blog/top-10-worldwide-mobile-games-by-revenue-and-downloads-in-august-2026)) | (trop récent) | (trop récent) |
| **Codename Crime: Vice Open World** | Gratuit | ~1,25 M$ pour 16,7 M téléchargements [ESTIMATION AppMagic, via résumé de recherche] ([pocketgamer.biz, non ouvert](https://pocketgamer.biz/august-2026-mobile-game-charts)) | n.d. | n.d. |

**Tendance août 2026 :** les jeux de crime « RP » en ligne (Mayfia City RP, Gangster Miami RP) figurent dans les tendances AppMagic [RÉSUMÉ] (même source). Le genre est porteur en téléchargements, mais il rapporte peu par joueur hors des gros éditeurs (voir `RECHERCHE-AAA.md` §1.2).

**Lecture :**
1. Les gros volumes viennent de jeux **gratuits avec publicité**, souvent techniquement modestes. Les joueurs pardonnent les graphismes, **pas les pubs intrusives ni la perte de progression**.
2. Ce que les joueurs aiment, c'est **le chaos amusant** (physique, ragdoll, cascades) et **la liberté**, plus qu'un scénario.
3. Les plaintes récurrentes du genre sont toujours les mêmes : pubs, énergie et VIP, contrôles tactiles, plantages, sauvegarde perdue.

### 3.2 Fonctions qui reviennent souvent

| Fonction | Présente chez | Intérêt pour Néon Bay |
|---|---|---|
| Garage et personnalisation des véhicules | Gangstar Vegas, Mirage City, Car Parking | Fort : les voitures PBR existent déjà. Couleur, jantes, néons sous caisse (cohérent avec le nom « Néon Bay ») |
| Armes à améliorer | Gangstar, Naxeex | Moyen : garder les armes gratuites par défis (argument de l'audit). L'amélioration peut se gagner par l'usage |
| Récompenses quotidiennes et VIP | Gangstar (VIP), F2P en général ([analyse VIP, Adrian Crook](https://adriancrook.com/?p=4914)) | Une récompense de connexion simple suffit. Pas de VIP payant |
| Roue de la fortune et « jeux d'argent simulés » | Gangstar Vegas (classé 17+ avec mention de jeux d'argent simulés) | **À éviter** : cela alourdit la classification et attire les critiques sur les mineurs |
| Énergie | Gangstar New Orleans (~1,10 $ le plein d'énergie [ESTIMATION] [pocketgamer.biz](https://www.pocketgamer.biz/how-does-gangstar-new-orleans-monetise)) | **À éviter** : c'est une plainte n°1 dans les avis |
| Missions courtes | Tout le genre | Déjà en place : niveaux de 10 étapes, petits boulots |
| Mode chaos et bac à sable | Dude Theft Wars | Très fort pour la viralité (clips TikTok) |

### 3.3 Fiche store qui convertit

- **Vidéo :** la vidéo de jeu réel qui montre les fonctions et les événements convertit le mieux (retour d'expérience de Dots/TwoDots) [FAIT, blog Android Developers, 2015] ([Android Developers Blog](https://android-developers.googleblog.com/2015/08/games-developer-dots-share-their-dos.html)).
- **Captures :** peu de texte. Elles doivent raconter une histoire visuelle et être localisées (même source).
- **Tests A/B :** Google conseille de tester l'icône, la vidéo et les captures, un élément à la fois, pendant au moins une semaine [FAIT] ([Store listing experiments](https://developer.android.com/distribute/best-practices/grow/store-listing-experiments)). Chez Tapps Games, des messages plus courts, des couleurs contrastées, des captures réordonnées et des visuels simplifiés ont donné des gains de 5 à 50 % selon les variantes [FAIT, étude de cas Google] ([Tapps](https://play.google.com/console/about/tapps-casestudy/)).
- **Pour Néon Bay :**
  - 1re capture : une poursuite de nuit sous les néons, en vue poursuite (pas en vue de dessus) ;
  - 2e : un tir avec flash et impacts ;
  - 3e : le garage ;
  - ensuite : les pays, la Lune et Mars (différenciant fort) ;
  - une légende de 3 à 5 mots par capture, en 4 langues.

### 3.4 Dix recommandations classées pour Néon Bay

Coût : S = moins d'une journée avec l'IA, M = 2 à 5 jours, L = plus d'une semaine. L'impact est une estimation.

| # | Recommandation | Pourquoi (source) | Impact | Coût |
|---|---|---|---|---|
| 1 | **Sensations de tir** (§4) : recul, flash, impacts, tremblement, son en couches, vibration | C'est ce que voient la vidéo de store et les clips | Très fort sur la rétention et la conversion | S à M |
| 2 | **Sauvegarde fiable et exportable** (code de transfert ou compte) | Perte de progression : plainte récurrente (Gangstar, Dude Theft Wars) | Fort (moins de notes 1 étoile) | M |
| 3 | **Pas d'énergie, pas de roue de la fortune, pub uniquement « récompensée » et optionnelle** | Pubs intrusives et énergie : plaintes n°1 du genre | Fort sur la note du store | S |
| 4 | **Garage néon** : couleur, jantes, néons sous caisse, klaxon. Gratuit par l'argent du jeu, avec éventuellement des cosmétiques payants | Fonction centrale du genre, voitures PBR déjà là | Fort sur l'engagement et la monétisation | M |
| 5 | **Compression meshopt + textures WebP** (§1.1) | Chargement plus court et TWA plus légère : moins d'abandons au premier lancement | Moyen à fort | S |
| 6 | **Mode chaos / bac à sable** (physique exagérée, ragdoll, cascades notées) | Ce que les avis 4-5 étoiles de Dude Theft Wars aiment | Fort pour la viralité | M |
| 7 | **Contrôles tactiles réglables** (taille et position des boutons, sensibilité, aide à la visée réglable, gyroscope optionnel) | Plainte récurrente sur les contrôles ([Game Developer, UX FPS mobile](https://www.gamedeveloper.com/game-platforms/ux-deep-dive-painful-reality-of-building-fps-experiences-on-mobile-part-1)) | Fort | M |
| 8 | **Récompense quotidienne simple** (7 jours, cosmétiques et argent du jeu) et **défis courts** du jour | Standard du genre, sans « pay-to-win » | Moyen sur la rétention J1/J7 | S |
| 9 | **Fiche store** : vidéo de jeu réel de 20 à 30 s, 8 captures légendées, test A/B de l'icône | Sources Google ci-dessus | Fort sur la conversion | S à M |
| 10 | **Densifier la ville avec des assets CC0** (Downtown City MegaKit de Quaternius, textures ambientCG) passés par la chaîne Blender, instanciés et compressés | Ville plus crédible sans coût de modélisation | Moyen | M |

---

## 4. Sensations de tir sur mobile (« game feel » des armes)

### 4.1 Références

- **Jan Willem Nijman (Vlambeer), « The Art of Screenshake », 2013.** Il part d'un jeu de tir basique et ajoute les effets un par un : chaque ajout améliore la sensation ([Game Developer](https://gamedeveloper.com/design/vlambeer-co-founder-shares-advice-on-building-better-action-games), [analyse Infovore](https://infovore.org/?p=5275)). Exemple cité pour Nuclear Throne : à chaque tir, l'arme recule légèrement (« kick ») puis revient très vite en place, en même temps que le son.
- **Martin Jonasson et Petri Purho, « Juice It or Lose It », GDC Europe 2012.** Ils montrent sur scène comment de petits retours (rebonds, particules, sons) rendent un jeu fade satisfaisant ([GDC Vault](https://gdcvault.com/play/1016789/Juice-It-or-Lose)). Contrepoint : Folmer Kelly, « Don't Juice It or Lose It », sur le risque de surcharge ([Game Developer](https://gamedeveloper.com/design/video-indies-resist-the-urge-to-juice-it-or-lose-it-)).
- **Recherche :** l'article arXiv « impact feel » (2022) décompose la sensation d'impact (gel, tremblement, son, particules) ([arXiv 2208.06155](https://arxiv.org/abs/2208.06155)). Une thèse cite Swink (*Game Feel*), Jonasson et Purho, et Nijman comme sources principales du sujet ([arXiv 2011.09201](https://arxiv.org/pdf/2011.09201)).
- **Aide à la visée :**
  - Nick Weihs (Insomniac), « Techniques for Building Aim Assist in Console Shooters », GDC 2013 : magnétisme, centrage, friction, zones mortes, accélération de caméra ([GDC Vault](https://gdcvault.com/play/1017942/Techniques-for-Building-Aim-Assist)) ;
  - sur mobile, l'aide à la visée et le tir automatique réduisent l'effort de suivi de cible ([Game Developer, UX FPS mobile](https://www.gamedeveloper.com/game-platforms/ux-deep-dive-painful-reality-of-building-fps-experiences-on-mobile-part-1)) ;
  - Apex Legends Mobile a une aide « nettement plus forte » que sur PC, réglée arme par arme, et compensée par un temps pour tuer un peu plus long ([Dot Esports](https://dotesports.com/news/does-apex-legends-mobile-have-aim-assist)) ;
  - choix de cible automatique sur mobile ([Game Developer, auto-aim équitable](https://gamedeveloper.com/design/how-to-create-a-fair-auto-aiming-system-in-a-robot-shooter-)).
- **Son en couches :** un tir se décompose en mécanique, grave, détail proche, détail lointain et queue de réverbération ([Splice](https://splice.com/blog/?p=16617)). Garder le son « sec » et laisser le moteur ajouter la réverbération selon le lieu (même source). C'est utile pour les tunnels, déjà relevés comme manque dans l'audit. Borderlands 3 assemble des milliers de fragments sonores en signatures d'armes ([Game Developer](https://www.gamedeveloper.com/marketing/creating-a-complex-sonic-ecosystem-with-modular-design-in-tiny-tina-s-wonderlands)).
- **Ralenti ou gel à l'impact (hitstop) :** ne figer que les acteurs concernés, pas l'interface ni le son, et caler le gel sur le son d'impact [source de blog, fiabilité moyenne] ([uhiyama-lab](https://uhiyama-lab.com/en/notes/unity/unity-game-feel-hit-feedback/)).
- **Vibration :**
  - Android recommande « moins, c'est mieux », des retours nets plutôt que des bourdonnements, et une conception commune image + son + vibration ([Android haptics principles](https://developer.android.com/develop/ui/views/haptics/haptics-principles)) ;
  - dans la TWA (Chrome), `navigator.vibrate()` fonctionne après une interaction de l'utilisateur ([MDN](https://developer.mozilla.org/en-US/docs/Web/API/Navigator/vibrate)) ;
  - **il n'est pas pris en charge par Safari sur iOS**, et WebKit s'y oppose ([rapport W3C](https://w3c.github.io/vibration/reports/implementation.html)) ;
  - il faut un réglage pour couper la vibration (accessibilité).

### 4.2 Valeurs de départ proposées

Ce sont **des valeurs à régler en jeu**, pas des chiffres sourcés.

| Effet | Pistolet | Fusil d'assaut | Fusil à pompe ou explosion |
|---|---|---|---|
| Recul de l'arme (modèle) | 3 cm, retour en 80 ms | 1,5 cm par balle, retour en 60 ms | 6 cm, retour en 150 ms |
| Recul de caméra (sens opposé au tir, idée de Nijman) | 0,3° | 0,15° plus une petite dérive verticale | 1° |
| Tremblement de caméra (« trauma » qui décroît) | 0,05 | 0,03 par balle, plafonné | 0,3 à 0,6 |
| Flash de bouche | sprite additif plus `PointLight` pendant 1 image (lumière désactivée sur mobile bas de gamme) | idem, rotation aléatoire | plus gros, 2 images |
| Douilles | 1 instance d'un `InstancedMesh` partagé, durée 2 s | idem, au maximum 64 visibles | — |
| Impacts | décalque et étincelles instanciés, au maximum 32 | idem | débris et fumée |
| Gel à l'impact | aucun | aucun | 40 à 60 ms sur l'ennemi touché, ralenti de 0,2 s sur une mise à terre |
| Son | 3 couches (mécanique, détonation, queue), hauteur ±5 % aléatoire | idem, sans répétition identique | plus une couche grave |
| Vibration (`navigator.vibrate`) | 10 ms | 8 ms toutes les 2 balles | 30 à 40 ms |
| Aide à la visée mobile | magnétisme léger dans un cône de 6°, friction quand le réticule passe sur une cible | idem | cône de 10° |
| Retour de touche | marqueur de touche (« hitmarker ») plus un « tic » sonore, éclair blanc sur l'ennemi pendant 1 image | idem | idem |

Tout tient dans three r128 sans dépendance : `InstancedMesh`, sprites, et un `ShaderPass` déjà disponible pour un léger flash d'écran.

---

## Ce qu'on peut en tirer pour le studio

1. **Compresser sans changer de version de three :** `gltf-transform inspect`, puis `resize` + `webp`, puis `gltfpack -c -kn -km`, avec le `meshopt_decoder.js` fourni par r128. Ne jamais utiliser `-mi`, `-cz` ni KTX2. Valider avec `check_glb_three.js`.
2. **Ne pas ajouter de bibliothèque récente :** pmndrs/postprocessing et three-mesh-bvh exigent un three plus récent. Les passes FXAA, bloom et vignette de r128 suffisent. three-mesh-bvh 0.5.24 n'est à épingler que si le profilage le justifie.
3. **Une semaine « game feel »** (§4) avant de tourner la vidéo de store : c'est le meilleur rapport impact/coût.
4. **Assets CC0 seulement**, tous tracés dans `CREDITS.md`. Animations : Quaternius UAL plutôt que Mixamo. Ville : Downtown City MegaKit et ambientCG. Aucune arme réelle nommée.
5. **Monétisation propre** : pas d'énergie, pas de roue de la fortune, pub récompensée optionnelle, garage cosmétique. C'est exactement ce que les avis 1-2 étoiles du genre reprochent aux concurrents.
