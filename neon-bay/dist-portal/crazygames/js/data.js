/* Néon Bay : données du jeu (régions, 30 niveaux, boutique, vente) */
window.NB_DATA = (() => {
  // ---------- VENTE ----------
  // Mets ici ton lien de paiement (Stripe Payment Link, Systeme.io, Gumroad, itch.io...).
  // Après paiement, envoie au client un code généré avec tools/generate-codes.js
  const SHOP_CONFIG = {
    buyUrl: '',            // ex: 'https://buy.stripe.com/xxxx'
    price: '2,99 €',
    salt: 'nb-27359c4a7da65190-', // change-le AVANT de vendre, et garde le même dans tools/generate-codes.js
    playSku: 'full_game',  // identifiant du produit « Jeu complet » créé dans la Play Console
    verifyUrl: '',         // (recommandé) adresse d'un petit serveur qui vérifie l'achat et en accuse réception, voir ANDROID.md
  };


  // ---------- CONQUÊTE SPATIALE (bonus) : fuir la Terre en fusée et survivre sur la Lune ou sur Mars ----------
  const SPACE = [
    {
      id: 'moon', name: 'Base Tranquille', country: 'Lune', from: 31, to: 31, seed: 71, accent: '#cfd8ff', space: true,
      tagline: 'Gravité faible, oxygène compté, la Terre au-dessus de ta tête.',
      pal: { ground: '#0a0a0e', road: '#3a3a42', walk: '#55555e', line: '#6a6a74', curb: '#7a7a86', park: '#6d6d74', tree: '#5a5a62', water: '#3a3a42', plaza: '#8a8f9e',
        bld: ['#c9ccd6', '#b8bcc8', '#d8dae2', '#9fa4b2'], neon: ['#21e6ff', '#ffffff', '#ffb627', '#9d7bff', '#a6ff4d'] },
      blocks: { park: 4, full: 1.2, split: 1, plaza: 1.6, warehouse: 1 },
      factions: [{ name: 'les mineurs rebelles', color: '#ffb627', look: { shirt: '#e8e2d0', jacket: '#ffb627', pants: '#8a8070', hat: '#ffffff', hatType: 'beanie' } }, { name: 'la sécurité de la base', color: '#21e6ff', look: { shirt: '#dfe6f2', jacket: '#21e6ff', pants: '#3a4a66', hat: '#ffffff', hatType: 'beanie' } }],
      look: { roof: 'flat', glass: '#9fc6ff', facades: ['#d8dae2', '#c9ccd6', '#e8e8ee', '#b8bcc8'], trees: 'cone', edges: {}, lamp: '#cfe6ff', sidewalk: 'concrete', sky: '#000000', ground: '#6d6d74', space: 'moon', landmarks: [],
        peds: { shirts: ['#f4f4f4', '#e8e8ee', '#ffffff'], pants: ['#d8dae2', '#c9ccd6'], shorts: 0, hat: 1, hatTypes: ['beanie'], jacket: .4, skirt: 0, skins: ['#f2d3b3', '#c68b59', '#8d5a3b'] },
        cars: { palette: ['#f4f4f4', '#d8dae2', '#ffb627'], taxi: '#ffb627', types: { jeep: 4, van: 1.5, pickup: 1 } } },
      vip: 'la docteure Ilsa Moreau', places: ['le dôme Armstrong', 'la mine d’hélium 3', 'le module de communication', 'la serre hydroponique', 'le spatioport', 'le cratère Shackleton'],
    },
    {
      id: 'mars', name: 'Colonie Ares', country: 'Mars', from: 32, to: 32, seed: 97, accent: '#ff7a3d', space: true,
      tagline: 'Tempêtes de poussière, colons armés, un ciel couleur rouille.',
      pal: { ground: '#1a0c08', road: '#5a3424', walk: '#7a4a34', line: '#8a5a44', curb: '#9a6a50', park: '#a4573a', tree: '#7a3a24', water: '#5a3424', plaza: '#c9a48a',
        bld: ['#e2d6c6', '#cfc2b0', '#b8a894', '#f0e6d8'], neon: ['#ff7a3d', '#21e6ff', '#ffd23f', '#ffffff', '#a6ff4d'] },
      blocks: { park: 3.5, full: 1.2, warehouse: 1.4, plaza: 1.6, split: .8 },
      factions: [{ name: 'les Fils de la Poussière', color: '#ff7a3d', look: { shirt: '#c98a5a', jacket: '#ff7a3d', pants: '#5a3424', hat: '#e8e2d0', hatType: 'beanie' } }, { name: 'la milice de la colonie', color: '#a6ff4d', look: { shirt: '#e2d6c6', jacket: '#3a5a2a', pants: '#2a3a20', hat: '#ffffff', hatType: 'beanie' } }],
      look: { roof: 'flat', glass: '#ffb88a', facades: ['#f0e6d8', '#e2d6c6', '#cfc2b0'], trees: 'cone', edges: {}, lamp: '#ffd8b0', sidewalk: 'concrete', sky: '#c27a4e', ground: '#a4573a', space: 'mars', landmarks: [],
        peds: { shirts: ['#f4f4f4', '#ffb627', '#ffffff'], pants: ['#d8dae2', '#8a8070'], shorts: 0, hat: 1, hatTypes: ['beanie'], jacket: .5, skirt: 0, skins: ['#f2d3b3', '#c68b59', '#8d5a3b'] },
        cars: { palette: ['#f4f4f4', '#ff7a3d', '#d8dae2'], taxi: '#ff7a3d', types: { jeep: 4, pickup: 2, van: 1 } } },
      vip: 'le commandant Okafor', places: ['la serre de la colonie', 'le dôme principal', 'la foreuse de glace', 'le canyon Valles', 'la piste du spatioport', 'le relais radio'],
    },
  ];
  const REGIONS = [
    {
      id: 'usa', name: 'Néon Bay', country: 'États-Unis', from: 1, to: 8, seed: 11, accent: '#ff2e93',
      tagline: 'Gangs de rue, rappeurs et docks en feu.',
      pal: { ground: '#0d0b1a', road: '#17142a', walk: '#2b2546', line: '#352e56', curb: '#544a80', park: '#123629', tree: '#1f6a4c', water: '#0f2f4f', plaza: '#30294d',
        bld: ['#231b3f', '#1c2142', '#2a1d36', '#1f1a33'], neon: ['#ff2e93', '#21e6ff', '#ffb627', '#9d7bff', '#a6ff4d'] },
      blocks: { full: 4, split: 3, park: 1.2, warehouse: .8, plaza: .6 },
      factions: [{ name: 'les Vipères', color: '#a6ff4d', look: { shirt: '#1b1b22', jacket: '#2a2f24', pants: '#1a1a20', bandana: '#a6ff4d' } }, { name: 'le Crew du Port', color: '#ff6b3d', look: { shirt: '#ff6b3d', jacket: '#3a3f4a', pants: '#2f3b52', hatType: 'beanie', hat: '#ff6b3d' } }],
      look: {
        // ville balnéaire néon : tours de verre au centre, petits immeubles pastel, palmiers, plage au sud, océan à l'est
        roof: 'flat', glass: '#2b3d63', facades: ['#f2b5d4', '#9fe0e6', '#f6e3c3', '#c9b8ff', '#ffd1a1', '#b8f2c9'],
        trees: 'palm', edges: { s: 'beach', e: 'sea' }, lamp: '#e9f6ff', sidewalk: 'concrete', sky: '#7cc4f2', ground: '#c9b79a',
        landmarks: ['tower', 'wheel', 'stadium', 'palace', 'statue'],
        peds: { shirts: ['#ff2e93', '#21e6ff', '#ffd23f', '#ffffff', '#111111', '#7a5cff', '#ff8a3d', '#3ee0c5'], pants: ['#2f4f86', '#1d1a2e', '#c2a878', '#e8e8ee'], shorts: .45, hat: .3, hatTypes: ['cap', 'cap', 'beanie'], jacket: .15, skirt: .2, skins: ['#f2d3b3', '#e0b48c', '#c68b59', '#8d5a3b', '#5c3a24'] },
        cars: { palette: ['#ff5d8f', '#ffd23f', '#3ee0c5', '#e7e3f5', '#4da3ff', '#c13cff', '#111111', '#ff8a3d'], taxi: '#ffd23f', types: { sedan: 3, muscle: 2, convertible: 1.4, van: .8, pickup: 1, taxi: 1 } },
      },
      vip: 'MC Ozone, le rappeur',
      places: ["le studio d'enregistrement", 'le club Velvet', 'les docks', 'la station de radio', 'le parking du stade', 'le motel Paradise', 'la boutique de sneakers', 'le pied de la Neon Tower'],
    },
    {
      id: 'ita', name: 'Porto Lumi', country: 'Italie', from: 9, to: 16, seed: 23, accent: '#ffb627',
      tagline: 'Les familles mafieuses règnent sur les canaux.',
      pal: { ground: '#120d0b', road: '#1f1917', walk: '#3a2c26', line: '#46352d', curb: '#6b5244', park: '#1f3a24', tree: '#2f5e35', water: '#0f3a55', plaza: '#4a3a2e',
        bld: ['#4a2f26', '#55382b', '#3d2a2a', '#4f3226'], neon: ['#ffb627', '#ff6b3d', '#f2e6c9', '#7fd1ae'] },
      blocks: { full: 3, split: 2, plaza: 2, water: 2, park: .8 },
      factions: [{ name: 'la Famiglia Varga', color: '#c13cff', look: { shirt: '#f2f2f2', jacket: '#2a1a35', pants: '#2a1a35', hatType: 'fedora', hat: '#1a1020', tie: '#c13cff' } }, { name: 'la Famiglia Moretti', color: '#f2f2f2', look: { shirt: '#111111', jacket: '#e8e4da', pants: '#e8e4da', hatType: 'fedora', hat: '#f2f2f2', tie: '#8a0f1a' } }],
      look: {
        // ville portuaire méditerranéenne : façades ocre et saumon, toits de tuiles, canaux, places, cyprès, campanile et dôme
        roof: 'tile', roofColor: '#b5562f', facades: ['#e9c46a', '#f4a261', '#e9806a', '#f1dcb5', '#d9a28b', '#e8b07a', '#f3e1c2'],
        trees: 'cypress', edges: { s: 'sea', w: 'sea' }, lamp: '#ffcf8a', sidewalk: 'cobble', sky: '#8cc6ef', ground: '#d8c7a0',
        landmarks: ['campanile', 'dome'],
        peds: { shirts: ['#ffffff', '#f2e6c9', '#2e4a7d', '#7a1f2b', '#3a5a40', '#d9a28b', '#111111'], pants: ['#3a3a44', '#c2a878', '#2a3a5a', '#e8e4da'], shorts: .1, hat: .25, hatTypes: ['fedora', 'cap'], jacket: .4, skirt: .35, tie: .2, skins: ['#f2d3b3', '#e8c39e', '#e0b48c'] },
        cars: { palette: ['#c8102e', '#f2f2f2', '#2e6bff', '#ffd23f', '#3a5a40', '#111111', '#7fd1ae'], taxi: '#f2f2f2', types: { small: 3, sedan: 1.5, scooter: 2.5, van: .7, taxi: .6 } },
      },
      vip: 'il Consigliere',
      places: ['la piazza del Duomo', 'le port de pêche', 'la trattoria Nonna Lia', 'le vignoble', 'la villa sur la colline', 'le pont des Soupirs', "l'entrepôt d'huile d'olive", 'le casino Lumi'],
    },
    {
      id: 'col', name: 'Sierra Verde', country: 'Colombie', from: 17, to: 23, seed: 37, accent: '#a6ff4d',
      tagline: 'Jungle, pistes clandestines et cartels.',
      pal: { ground: '#0a0f08', road: '#1d1c14', walk: '#3a3424', line: '#463f2b', curb: '#6b6040', park: '#163a1c', tree: '#2a6b2f', water: '#123e3a', plaza: '#3f3a28',
        bld: ['#2f3a2a', '#3b3226', '#28342c', '#363226'], neon: ['#a6ff4d', '#ffd23f', '#3ee0c5'] },
      blocks: { jungle: 3, warehouse: 2, full: 1.5, park: 1.5, split: 1 },
      factions: [{ name: 'Los Lobos', color: '#ff4d5e', look: { shirt: '#4b5320', jacket: '#3b4220', pants: '#2b2f1e', hatType: 'cap', hat: '#ff4d5e' } }, { name: 'le Cartel del Cóndor', color: '#ffd23f', look: { shirt: '#f2efe2', pants: '#c2a878', hatType: 'straw', hat: '#e3c78a', chain: true } }],
      look: {
        // ville coloniale au pied des montagnes : maisons très colorées, tuiles rouges, jungle, rivière, église blanche à deux tours
        roof: 'tile', roofColor: '#a8432a', facades: ['#ffd23f', '#3a86ff', '#ff006e', '#8ac926', '#fb5607', '#ffffff', '#00b4d8'],
        trees: 'jungle', edges: { n: 'mountains', s: 'mountains', e: 'mountains', w: 'mountains' }, lamp: '#ffb347', sidewalk: 'terracotta', sky: '#8fd0f0', ground: '#6b8f3a',
        landmarks: ['church', 'plantation'],
        peds: { shirts: ['#ffffff', '#ffd23f', '#3a86ff', '#ff006e', '#8ac926', '#f2efe2', '#fb5607'], pants: ['#c2a878', '#2f4f86', '#3a2a22', '#f2efe2'], shorts: .2, hat: .4, hatTypes: ['straw', 'straw', 'cap'], jacket: .05, skirt: .4, skins: ['#e0b48c', '#c68b59', '#a8724a', '#8d5a3b'] },
        cars: { palette: ['#f2f2f2', '#c8102e', '#2e6bff', '#3a5a40', '#ffd23f', '#6b4a2a'], taxi: '#ffd23f', types: { jeep: 2.5, pickup: 2.5, sedan: 1, bus: .8, scooter: 1.2, taxi: .8 } },
      },
      vip: 'Rosa, la pilote de brousse',
      places: ["la piste d'atterrissage", 'la plantation de café', 'le marché central', "l'hacienda", 'le pont de la rivière', 'le laboratoire caché', 'la cascade', 'le petit port fluvial'],
    },
    {
      id: 'bra', name: 'Morro Azul', country: 'Brésil', from: 24, to: 30, seed: 53, accent: '#21e6ff',
      tagline: 'Les favelas colorées, le baile funk et la guerre des bondes.',
      pal: { ground: '#0c0a14', road: '#1a1726', walk: '#3d3029', line: '#4a3a31', curb: '#6e5646', park: '#173a26', tree: '#25703f', water: '#0f3550', plaza: '#3b3045',
        bld: ['#8a3a52', '#9a7032', '#2f7d8c', '#4f7a34', '#6f4c8c', '#9a5626'], neon: ['#21e6ff', '#ffd23f', '#ff2e93'] },
      blocks: { favela: 5, full: 1, split: 1, park: .5 },
      factions: [{ name: 'le Bonde do Trovão', color: '#21e6ff', look: { shirt: '#21e6ff', pants: '#111111', hatType: 'cap', hat: '#111111', shorts: true } }, { name: 'le Comando Sombra', color: '#ff2e93', look: { shirt: '#111111', pants: '#2a2a33', hatType: 'cap', hat: '#ff2e93', chain: true } }],
      look: {
        // favelas en escalier sur les collines, réservoirs d'eau bleus sur les toits, plage et promenade à vagues, grand rocher, téléphérique, terrain de foot
        roof: 'flat', facades: ['#e05a7a', '#f0b44c', '#4cc3d9', '#7ac74f', '#b57edc', '#f28c38', '#c46b3c', '#e8d9c0'],
        trees: 'palm', edges: { s: 'beach', n: 'mountains', w: 'mountains' }, lamp: '#ffd27a', sidewalk: 'waves', sky: '#76c7f5', ground: '#5f8a3f',
        landmarks: ['rock', 'cablecar', 'pitch'],
        peds: { shirts: ['#ffd23f', '#1f9e4a', '#2e6bff', '#ffffff', '#ff2e93', '#111111', '#21e6ff'], pants: ['#2f4f86', '#111111', '#e8e8ee', '#ffd23f'], shorts: .6, hat: .3, hatTypes: ['cap', 'cap', 'beanie'], jacket: .03, skirt: .25, skins: ['#e0b48c', '#c68b59', '#8d5a3b', '#5c3a24', '#3d2617'] },
        cars: { palette: ['#f2f2f2', '#ffd23f', '#1f9e4a', '#2e6bff', '#c8102e', '#111111'], taxi: '#ffd23f', types: { small: 2.5, scooter: 3, van: 1, sedan: 1, bus: .6 } },
      },
      vip: 'DJ Favelinha',
      places: ['le baile funk', 'le terrain de foot', 'le belvédère', 'la plage de Copa Azul', 'le marché du morro', "l'escalier coloré", 'la station de téléphérique', 'la planque du Comando'],
    },
  ];

  // 10 étapes par niveau. Types : goto, steal, garage, buy, deliver, collect, elim, boss,
  // escape, survive, tunnel, bribe, escort, destroy, race
  const LEVELS = [
    // ---- Néon Bay (USA)
    { t: 'Nouveau en ville', s: "Tu débarques à Néon Bay sans un dollar. Ton cousin Dre te confie tes premiers petits boulots pour te faire un nom.", steps: ['goto', 'steal', 'garage', 'buy', 'deliver', 'collect', 'elim', 'escape', 'tunnel', 'race'] },
    { t: 'Le rappeur', s: "MC Ozone sort son album demain et les Vipères veulent l'empêcher d'arriver au studio. Il te faut le protéger.", steps: ['goto', 'escort', 'elim', 'race', 'bribe', 'deliver', 'collect', 'escape', 'escort', 'elim'] },
    { t: 'Guerre de territoire', s: "Les Vipères débordent sur le quartier de Dre. Reprends les coins de rue un par un.", steps: ['goto', 'elim', 'collect', 'steal', 'garage', 'elim', 'escape', 'bribe', 'destroy', 'elim'] },
    { t: 'Clip sous haute tension', s: "Le tournage du clip d'Ozone tourne mal : des tireurs, des flics, et un réalisateur qui ne veut pas arrêter.", steps: ['escort', 'race', 'elim', 'goto', 'survive', 'tunnel', 'escort', 'collect', 'deliver', 'elim'] },
    { t: 'Le convoi des Vipères', s: "Un convoi de marchandise traverse la ville cette nuit. Détruis-le et va chercher leur chef, Snake.", steps: ['goto', 'destroy', 'escape', 'buy', 'collect', 'elim', 'steal', 'garage', 'destroy', 'boss'], boss: 'Snake' },
    { t: 'Le flic corrompu', s: "L'inspecteur Kowalski vend des infos à tout le monde. Paie-le, utilise-le, puis débarrasse-toi de ceux qui l'ont acheté avant toi.", steps: ['bribe', 'jailbreak', 'deliver', 'elim', 'escape', 'bribe', 'tunnel', 'collect', 'race', 'elim'] },
    { t: 'Docks en feu', s: "Le Crew du Port contrôle tout ce qui entre par la mer. Il est temps de leur montrer qui commande.", steps: ['goto', 'elim', 'destroy', 'collect', 'survive', 'steal', 'garage', 'escape', 'elim', 'destroy'] },
    { t: 'Le roi du port', s: "Big Marlow, le patron du Crew du Port, t'attend sur les quais. Après lui, Néon Bay est à toi.", steps: ['buy', 'escort', 'elim', 'collect', 'bribe', 'race', 'destroy', 'survive', 'tunnel', 'boss'], boss: 'Big Marlow' },
    // ---- Porto Lumi (Italie)
    { t: 'Benvenuti a Porto Lumi', s: "Un vieil ami de Dre te fait venir en Italie. Ici, rien ne se fait sans l'accord des familles.", steps: ['goto', 'bribe', 'steal', 'garage', 'deliver', 'collect', 'elim', 'tunnel', 'escape', 'race'] },
    { t: 'La trattoria', s: "Nonna Lia refuse de payer la protection des Varga. Ses lasagnes valent bien un coup de main.", steps: ['goto', 'elim', 'escort', 'deliver', 'collect', 'escape', 'bribe', 'elim', 'race', 'elim'] },
    { t: 'Le vin de la Famiglia', s: "Les Varga cachent leurs affaires dans des caisses de vin. Intercepte la livraison.", steps: ['steal', 'garage', 'destroy', 'collect', 'escape', 'deliver', 'elim', 'tunnel', 'survive', 'destroy'] },
    { t: 'Le Consigliere', s: "Le conseiller des Moretti veut changer de camp. Fais-le traverser la ville vivant.", steps: ['escort', 'elim', 'race', 'bribe', 'escort', 'collect', 'escape', 'tunnel', 'deliver', 'elim'] },
    { t: 'Les canaux', s: "Sous Porto Lumi passent de vieux tunnels de contrebandiers. Celui qui les contrôle contrôle la ville.", steps: ['jailbreak', 'tunnel', 'collect', 'elim', 'destroy', 'escape', 'steal', 'garage', 'race', 'elim'] },
    { t: 'Trahison à la villa', s: "Don Varga t'invite à dîner. C'est un piège, et tout le monde le sait.", steps: ['goto', 'elim', 'survive', 'escape', 'bribe', 'collect', 'deliver', 'destroy', 'elim', 'boss'], boss: 'Don Varga' },
    { t: 'Le casino Lumi', s: "Le coffre du casino Moretti est plein. Le préfet de police aussi aime l'argent.", steps: ['bribe', 'collect', 'elim', 'race', 'steal', 'garage', 'escape', 'destroy', 'survive', 'elim'] },
    { t: 'Le Parrain', s: "Il ne reste qu'un homme entre toi et le contrôle de Porto Lumi : Don Moretti.", steps: ['buy', 'escort', 'elim', 'destroy', 'collect', 'tunnel', 'survive', 'escape', 'elim', 'boss'], boss: 'Don Moretti' },
    // ---- Sierra Verde (Colombie)
    { t: 'Atterrissage forcé', s: "Ton avion se pose en catastrophe à Sierra Verde. Rosa, la pilote, connaît tout le monde ici.", steps: ['goto', 'elim', 'collect', 'escort', 'race', 'escape', 'bribe', 'tunnel', 'deliver', 'elim'] },
    { t: 'La plantation', s: "Los Lobos ont pris la plantation de café de la famille de Rosa. Reprends-la.", steps: ['goto', 'elim', 'destroy', 'collect', 'survive', 'steal', 'garage', 'escape', 'race', 'elim'] },
    { t: 'Le pont de la rivière', s: "Le seul pont de la vallée sert de péage aux Lobos. Coupe leur route.", steps: ['destroy', 'elim', 'escape', 'tunnel', 'collect', 'bribe', 'deliver', 'survive', 'destroy', 'elim'] },
    { t: "L'hacienda", s: "El Lobo se cache dans son hacienda, protégé par ses hommes et par un colonel bien payé.", steps: ['goto', 'bribe', 'elim', 'collect', 'escort', 'elim', 'escape', 'race', 'destroy', 'boss'], boss: 'El Lobo' },
    { t: 'Le laboratoire caché', s: "Le Cartel del Cóndor a un repaire sous la jungle. On y entre par les tunnels.", steps: ['tunnel', 'elim', 'jailbreak', 'destroy', 'survive', 'escape', 'steal', 'garage', 'elim', 'elim'] },
    { t: 'Fuite par la jungle', s: "Le Cóndor a mis ta tête à prix. Rosa doit rejoindre son avion avant l'aube.", steps: ['escort', 'survive', 'race', 'elim', 'tunnel', 'escape', 'collect', 'destroy', 'deliver', 'elim'] },
    { t: 'Le Cóndor', s: "Le chef du cartel t'attend. Après ça, tu quittes la Colombie, ou tu la diriges.", steps: ['buy', 'elim', 'destroy', 'collect', 'bribe', 'survive', 'escort', 'escape', 'elim', 'boss'], boss: 'El Cóndor' },
    // ---- Morro Azul (Brésil)
    { t: 'Bienvenue au morro', s: "Rosa te dépose à Morro Azul. Dans les ruelles des favelas, il faut gagner le respect avant tout.", steps: ['goto', 'bribe', 'collect', 'elim', 'race', 'steal', 'garage', 'escape', 'tunnel', 'elim'] },
    { t: 'Le baile funk', s: "DJ Favelinha organise le plus gros baile de l'année, mais le Bonde do Trovão veut tout arrêter.", steps: ['escort', 'elim', 'collect', 'survive', 'deliver', 'escape', 'race', 'destroy', 'escort', 'elim'] },
    { t: 'Le téléphérique', s: "Le téléphérique relie le morro à la ville. Le Trovão y fait passer ses affaires.", steps: ['goto', 'elim', 'tunnel', 'collect', 'destroy', 'escape', 'bribe', 'survive', 'race', 'elim'] },
    { t: 'Guerre des bondes', s: "Les deux gangs du morro se font la guerre. Frappe le Trovão à la tête.", steps: ['elim', 'destroy', 'elim', 'jailbreak', 'escape', 'survive', 'steal', 'garage', 'elim', 'boss'], boss: 'Trovão' },
    { t: 'La plage', s: "Une cargaison du Comando Sombra arrive par la plage de Copa Azul cette nuit.", steps: ['race', 'deliver', 'elim', 'escort', 'collect', 'escape', 'tunnel', 'destroy', 'survive', 'elim'] },
    { t: 'Tout le monde te cherche', s: "Police, gangs, cartel : toute la ville est à tes trousses. Tiens bon.", steps: ['survive', 'escape', 'bribe', 'elim', 'collect', 'tunnel', 'destroy', 'escort', 'survive', 'elim'] },
    { t: 'Le dernier coup', s: "Sombra, le chef du Comando, contrôle tout Morro Azul. Le dernier coup, le plus gros.", steps: ['buy', 'elim', 'destroy', 'collect', 'escort', 'survive', 'tunnel', 'escape', 'elim', 'boss'], boss: 'Sombra' },
  ];

  const STEP_LABEL = {
    goto: 'Rendez-vous', steal: 'Vol de voiture', garage: 'Garage', buy: 'Équipement', deliver: 'Livraison',
    collect: 'Récupération', elim: 'Fusillade', boss: 'Chef de gang', escape: 'Fuite', survive: 'Survie',
    tunnel: 'Tunnel', bribe: 'Corruption', escort: 'Escorte', destroy: 'Convoi', race: 'Course', jailbreak: 'Évasion',
  };

  const WEAPONS = [
    { id: 'fists', name: 'Poings', price: 0, lvl: 1, rate: .38, dmg: 30, melee: true, pellets: 1, spread: 0, desc: 'Silencieux et toujours là. Mets K.O. au contact.' },
    { id: 'pistol', name: 'Pistolet', price: 0, lvl: 1, rate: .28, dmg: 18, spread: .04, pellets: 1, speed: 760, life: .6, mag: 12, reload: 1, reserve: Infinity, desc: 'Fiable, tir semi-auto, munitions illimitées.' },
    { id: 'uzi', name: 'Mitraillette', price: 1500, lvl: 2, rate: .08, dmg: 10, spread: .12, pellets: 1, speed: 760, life: .55, mag: 30, reload: 1.4, reserve: 240, desc: 'Cadence très rapide, peu précise.' },
    { id: 'shotgun', name: 'Fusil à pompe', price: 4000, lvl: 4, rate: .7, dmg: 14, spread: .36, pellets: 7, speed: 700, life: .32, mag: 6, reload: 1.8, reserve: 48, desc: 'Dévastateur au contact.' },
    { id: 'rifle', name: "Fusil d'assaut", price: 9000, lvl: 8, rate: .11, dmg: 20, spread: .05, pellets: 1, speed: 900, life: .8, mag: 30, reload: 1.6, reserve: 240, desc: 'Précis et rapide, longue portée.' },
    { id: 'sniper', name: 'Fusil de précision', price: 15000, lvl: 11, rate: 1.1, dmg: 130, spread: 0, pellets: 1, speed: 1400, life: 1.1, mag: 5, reload: 2.0, reserve: 30, desc: 'Une balle, un ennemi.' },
    { id: 'rocket', name: 'Lance-roquettes', price: 30000, lvl: 15, rate: 1.2, dmg: 90, spread: 0, pellets: 1, speed: 520, life: 1.3, explosive: true, mag: 1, reload: 2.2, reserve: 8, desc: 'Explose voitures et groupes.' },
    { id: 'minigun', name: 'Minigun', price: 70000, lvl: 24, rate: .045, dmg: 14, spread: .15, pellets: 1, speed: 820, life: .7, mag: 150, reload: 3.0, reserve: 600, desc: 'Un mur de balles.' },
    { id: 'lmg', name: 'Mitrailleuse lourde', price: 22000, lvl: 13, rate: .075, dmg: 24, spread: .09, pellets: 1, speed: 860, life: .8, mag: 100, reload: 2.6, reserve: 400, desc: 'Gros chargeur, gros dégâts. Touche 9.' },
    { id: 'gl', name: 'Lance-grenades', price: 40000, lvl: 18, rate: .55, dmg: 70, spread: .03, pellets: 1, speed: 560, life: .9, explosive: true, mag: 6, reload: 2.4, reserve: 30, desc: 'Six explosions à la suite. Touche 0.' },
    { id: 'rail', name: 'Fusil à impulsion', price: 120000, lvl: 27, rate: .9, dmg: 260, spread: 0, pellets: 1, speed: 1800, life: 1.2, mag: 4, reload: 2.2, reserve: 24, desc: 'Prototype ultime : 260 dégâts par tir.' },
  ];

  const GEAR = [
    { id: 'armor1', name: 'Gilet pare-balles', price: 1000, lvl: 1, kind: 'armor', value: 50, desc: '50 points d’armure au début de chaque niveau.' },
    { id: 'armor2', name: 'Gilet renforcé', price: 6000, lvl: 6, kind: 'armor', value: 100, desc: '100 points d’armure.' },
    { id: 'armor3', name: 'Armure tactique', price: 20000, lvl: 14, kind: 'armor', value: 150, desc: '150 points d’armure.' },
    { id: 'armor4', name: 'Exosquelette', price: 45000, lvl: 20, kind: 'armor', value: 250, desc: '250 points d’armure.' },
    { id: 'armor5', name: 'Armure lourde', price: 90000, lvl: 27, kind: 'armor', value: 400, desc: '400 points d’armure : presque un tank.' },
    { id: 'medkit', name: 'Trousse de soins', price: 400, lvl: 1, kind: 'medkit', max: 5, desc: '+50 santé (touche H). Max 5.' },
    { id: 'nitro', name: 'Nitro x3', price: 600, lvl: 2, kind: 'nitro', max: 9, desc: 'Boost en voiture (touche N). Max 9.' },
    { id: 'carArmor', name: 'Blindage de voiture', price: 5000, lvl: 5, kind: 'perk', desc: 'Tes voitures prennent 2 fois moins de dégâts.' },
    { id: 'radio', name: 'Brouilleur radio', price: 8000, lvl: 10, kind: 'perk', desc: 'Moins de renforts et la police te perd plus vite.' },
    { id: 'contacts', name: 'Carnet de contacts', price: 12000, lvl: 12, kind: 'perk', desc: 'Soudoyer les agents coûte 40 % de moins.' },
  ];

  // ---------- TENUES (payées avec l'argent du jeu) ----------
  const OUTFITS = {
    jacket: { label: 'Veste', items: [['none', 'Sans veste', 0, null], ['neon', 'Veste néon', 0, '#21e6ff'], ['black', 'Blouson noir', 800, '#16141c'], ['red', 'Bomber rouge', 1500, '#c8102e'], ['camo', 'Veste kaki', 2500, '#4b5320'], ['purple', 'Veste violette', 3500, '#6a2bd1'], ['gold', 'Veste dorée', 9000, '#d4a017']] },
    shirt: { label: 'T-shirt', items: [['white', 'Blanc', 0, '#f2f2f2'], ['black', 'Noir', 300, '#121218'], ['pink', 'Rose néon', 600, '#ff2e93'], ['yellow', 'Jaune', 600, '#ffd23f'], ['green', 'Vert', 600, '#3ecf6e'], ['blue', 'Bleu roi', 600, '#2e6bff']] },
    pants: { label: 'Pantalon', items: [['dark', 'Noir', 0, '#1a1530'], ['jean', 'Jean', 400, '#2f4f86'], ['beige', 'Beige', 600, '#c2a878'], ['white', 'Blanc', 900, '#e8e8ee'], ['red', 'Rouge', 1200, '#a3122a']] },
    hat: { label: 'Casquette', items: [['none', 'Aucune', 0, null], ['black', 'Noire', 500, '#111118'], ['red', 'Rouge', 700, '#c8102e'], ['white', 'Blanche', 700, '#f2f2f2'], ['gold', 'Dorée', 4000, '#d4a017']] },
    hair: { label: 'Coiffure', items: [['short', 'Courte', 0, 'short'], ['afro', 'Afro', 500, 'afro'], ['long', 'Longue', 500, 'long'], ['ponytail', 'Queue de cheval', 500, 'ponytail'], ['none', 'Rasée', 300, 'none']] },
    hairColor: { label: 'Couleur des cheveux', items: [['black', 'Noir', 0, '#1a120c'], ['brown', 'Châtain', 200, '#5a3a22'], ['blond', 'Blond', 400, '#d8b46a'], ['red', 'Roux', 400, '#9a3b1c'], ['pink', 'Rose', 1500, '#ff5fb0'], ['blue', 'Bleu', 1500, '#3aa0ff']] },
    skin: { label: 'Teint', items: [['t1', 'Clair', 0, '#f2d3b3'], ['t2', 'Mat', 0, '#e0b48c'], ['t3', 'Hâlé', 0, '#c68b59'], ['t4', 'Brun', 0, '#8d5a3b'], ['t5', 'Foncé', 0, '#5c3a24']] },
    shoes: { label: 'Baskets', items: [['white', 'Blanches', 0, '#ffffff'], ['black', 'Noires', 300, '#0c0b12'], ['red', 'Rouges', 800, '#c8102e'], ['gold', 'Dorées', 5000, '#d4a017']] },
    chain: { label: 'Chaîne', items: [['none', 'Aucune', 0, false], ['gold', 'Chaîne en or', 6000, true]] },
    body: { label: 'Corps', items: [['human', 'Humain', 0, null], ['robot', 'Robot animé', 8000, 'robot']] },
  };

  // ---------- SONS EN FICHIERS (facultatif) ----------
  // Par défaut, tous les sons et musiques sont générés par le jeu (js/audio.js).
  // Pour utiliser tes propres fichiers, mets-les dans le dossier audio/ et indique leur chemin ici.
  // Clés possibles : music_menu, music_usa, music_ita, music_col, music_bra,
  // shot (tous les tirs), shot_pistol, shot_uzi, shot_shotgun, shot_rifle, shot_sniper, shot_rocket, shot_minigun, shot_enemy,
  // explosion, crash, cash, win, fail. Voir AUDIO.md pour trouver des sons gratuits.
  const AUDIO_FILES = {
    // music_usa: 'audio/music-usa.mp3',
    // explosion: 'audio/explosion.ogg',
  };

  // modèles 3D animés (.glb) : chemin -> utilisés si le fichier se charge
  const MODELS = { robot: 'models/robot.glb', lm_palace: 'models/lm_palace.glb', human_f3: 'models/human_f3.glb', human_m3: 'models/human_m3.glb', human_f4: 'models/human_f4.glb', human_m4: 'models/human_m4.glb', human_m5: 'models/human_m5.glb', animal_dog: 'models/animal_dog.glb', animal_cat: 'models/animal_cat.glb', animal_bird: 'models/animal_bird.glb', animal_parrot: 'models/animal_parrot.glb', animal_crab: 'models/animal_crab.glb', prop_lifeguard_tower: 'models/prop_lifeguard_tower.glb', prop_parasol: 'models/prop_parasol.glb', prop_towel: 'models/prop_towel.glb', prop_dj_booth: 'models/prop_dj_booth.glb', prop_speaker_stack: 'models/prop_speaker_stack.glb', prop_rescue_tube: 'models/prop_rescue_tube.glb', car_police: 'models/car_police.glb', army_jeep: 'models/army_jeep.glb', army_truck: 'models/army_truck.glb', army_apc: 'models/army_apc.glb', lm_statue: 'models/lm_statue.glb', car_sedan: 'models/car_sedan.glb', car_sports: 'models/car_sports.glb', car_suv: 'models/car_suv.glb', car_van: 'models/car_van.glb', human_m: 'models/human_m.glb', human_f: 'models/human_f.glb', human_m2: 'models/human_m2.glb', human_f2: 'models/human_f2.glb', palm: 'models/palm.glb', lamp: 'models/lamp.glb', hydrant: 'models/hydrant.glb', bench: 'models/bench.glb', traffic_light: 'models/traffic_light.glb', w_pistol: 'models/w_pistol.glb', w_uzi: 'models/w_uzi.glb', w_shotgun: 'models/w_shotgun.glb', w_rifle: 'models/w_rifle.glb', w_sniper: 'models/w_sniper.glb', w_rocket: 'models/w_rocket.glb', w_minigun: 'models/w_minigun.glb', w_lmg: 'models/w_lmg.glb', w_gl: 'models/w_gl.glb', w_rail: 'models/w_rail.glb' };

  return { MODELS, SHOP_CONFIG, SPACE, REGIONS, LEVELS, STEP_LABEL, WEAPONS, GEAR, AUDIO_FILES, OUTFITS };
})();
