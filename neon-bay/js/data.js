/* Néon Bay : données du jeu (régions, 30 niveaux, boutique, vente) */
window.NB_DATA = (() => {
  // ---------- VENTE ----------
  // Mets ici ton lien de paiement (Stripe Payment Link, Systeme.io, Gumroad, itch.io...).
  // Après paiement, envoie au client un code généré avec tools/generate-codes.js
  const SHOP_CONFIG = {
    buyUrl: '',            // ex: 'https://buy.stripe.com/xxxx'
    price: '4,99 €',
    salt: 'nb-27359c4a7da65190-', // change-le AVANT de vendre, et garde le même dans tools/generate-codes.js
    playSku: 'full_game',  // identifiant du produit « Jeu complet » créé dans la Play Console
    verifyUrl: '',         // (recommandé) adresse d'un petit serveur qui vérifie l'achat et en accuse réception, voir ANDROID.md
  };

  const REGIONS = [
    {
      id: 'usa', name: 'Néon Bay', country: 'États-Unis', from: 1, to: 8, seed: 11, accent: '#ff2e93',
      tagline: 'Gangs de rue, rappeurs et docks en feu.',
      pal: { ground: '#0d0b1a', road: '#17142a', walk: '#2b2546', line: '#352e56', curb: '#544a80', park: '#123629', tree: '#1f6a4c', water: '#0f2f4f', plaza: '#30294d',
        bld: ['#231b3f', '#1c2142', '#2a1d36', '#1f1a33'], neon: ['#ff2e93', '#21e6ff', '#ffb627', '#9d7bff', '#a6ff4d'] },
      blocks: { full: 4, split: 3, park: 1.2, warehouse: .8, plaza: .6 },
      factions: [{ name: 'les Vipères', color: '#a6ff4d' }, { name: 'le Crew du Port', color: '#ff6b3d' }],
      vip: 'MC Ozone, le rappeur',
      places: ["le studio d'enregistrement", 'le club Velvet', 'les docks', 'la station de radio', 'le parking du stade', 'le motel Paradise', 'la boutique de sneakers', 'le pied de la Neon Tower'],
    },
    {
      id: 'ita', name: 'Porto Lumi', country: 'Italie', from: 9, to: 16, seed: 23, accent: '#ffb627',
      tagline: 'Les familles mafieuses règnent sur les canaux.',
      pal: { ground: '#120d0b', road: '#1f1917', walk: '#3a2c26', line: '#46352d', curb: '#6b5244', park: '#1f3a24', tree: '#2f5e35', water: '#0f3a55', plaza: '#4a3a2e',
        bld: ['#4a2f26', '#55382b', '#3d2a2a', '#4f3226'], neon: ['#ffb627', '#ff6b3d', '#f2e6c9', '#7fd1ae'] },
      blocks: { full: 3, split: 2, plaza: 2, water: 2, park: .8 },
      factions: [{ name: 'la Famiglia Varga', color: '#c13cff' }, { name: 'la Famiglia Moretti', color: '#f2f2f2' }],
      vip: 'il Consigliere',
      places: ['la piazza del Duomo', 'le port de pêche', 'la trattoria Nonna Lia', 'le vignoble', 'la villa sur la colline', 'le pont des Soupirs', "l'entrepôt d'huile d'olive", 'le casino Lumi'],
    },
    {
      id: 'col', name: 'Sierra Verde', country: 'Colombie', from: 17, to: 23, seed: 37, accent: '#a6ff4d',
      tagline: 'Jungle, pistes clandestines et cartels.',
      pal: { ground: '#0a0f08', road: '#1d1c14', walk: '#3a3424', line: '#463f2b', curb: '#6b6040', park: '#163a1c', tree: '#2a6b2f', water: '#123e3a', plaza: '#3f3a28',
        bld: ['#2f3a2a', '#3b3226', '#28342c', '#363226'], neon: ['#a6ff4d', '#ffd23f', '#3ee0c5'] },
      blocks: { jungle: 3, warehouse: 2, full: 1.5, park: 1.5, split: 1 },
      factions: [{ name: 'Los Lobos', color: '#ff4d5e' }, { name: 'le Cartel del Cóndor', color: '#ffd23f' }],
      vip: 'Rosa, la pilote de brousse',
      places: ["la piste d'atterrissage", 'la plantation de café', 'le marché central', "l'hacienda", 'le pont de la rivière', 'le laboratoire caché', 'la cascade', 'le petit port fluvial'],
    },
    {
      id: 'bra', name: 'Morro Azul', country: 'Brésil', from: 24, to: 30, seed: 53, accent: '#21e6ff',
      tagline: 'Les favelas colorées, le baile funk et la guerre des bondes.',
      pal: { ground: '#0c0a14', road: '#1a1726', walk: '#3d3029', line: '#4a3a31', curb: '#6e5646', park: '#173a26', tree: '#25703f', water: '#0f3550', plaza: '#3b3045',
        bld: ['#8a3a52', '#9a7032', '#2f7d8c', '#4f7a34', '#6f4c8c', '#9a5626'], neon: ['#21e6ff', '#ffd23f', '#ff2e93'] },
      blocks: { favela: 5, full: 1, split: 1, park: .5 },
      factions: [{ name: 'le Bonde do Trovão', color: '#21e6ff' }, { name: 'le Comando Sombra', color: '#ff2e93' }],
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
    { t: 'Le flic corrompu', s: "L'inspecteur Kowalski vend des infos à tout le monde. Paie-le, utilise-le, puis débarrasse-toi de ceux qui l'ont acheté avant toi.", steps: ['bribe', 'goto', 'deliver', 'elim', 'escape', 'bribe', 'tunnel', 'collect', 'race', 'elim'] },
    { t: 'Docks en feu', s: "Le Crew du Port contrôle tout ce qui entre par la mer. Il est temps de leur montrer qui commande.", steps: ['goto', 'elim', 'destroy', 'collect', 'survive', 'steal', 'garage', 'escape', 'elim', 'destroy'] },
    { t: 'Le roi du port', s: "Big Marlow, le patron du Crew du Port, t'attend sur les quais. Après lui, Néon Bay est à toi.", steps: ['buy', 'escort', 'elim', 'collect', 'bribe', 'race', 'destroy', 'survive', 'tunnel', 'boss'], boss: 'Big Marlow' },
    // ---- Porto Lumi (Italie)
    { t: 'Benvenuti a Porto Lumi', s: "Un vieil ami de Dre te fait venir en Italie. Ici, rien ne se fait sans l'accord des familles.", steps: ['goto', 'bribe', 'steal', 'garage', 'deliver', 'collect', 'elim', 'tunnel', 'escape', 'race'] },
    { t: 'La trattoria', s: "Nonna Lia refuse de payer la protection des Varga. Ses lasagnes valent bien un coup de main.", steps: ['goto', 'elim', 'escort', 'deliver', 'collect', 'escape', 'bribe', 'elim', 'race', 'elim'] },
    { t: 'Le vin de la Famiglia', s: "Les Varga cachent leurs affaires dans des caisses de vin. Intercepte la livraison.", steps: ['steal', 'garage', 'destroy', 'collect', 'escape', 'deliver', 'elim', 'tunnel', 'survive', 'destroy'] },
    { t: 'Le Consigliere', s: "Le conseiller des Moretti veut changer de camp. Fais-le traverser la ville vivant.", steps: ['escort', 'elim', 'race', 'bribe', 'escort', 'collect', 'escape', 'tunnel', 'deliver', 'elim'] },
    { t: 'Les canaux', s: "Sous Porto Lumi passent de vieux tunnels de contrebandiers. Celui qui les contrôle contrôle la ville.", steps: ['goto', 'tunnel', 'collect', 'elim', 'destroy', 'escape', 'steal', 'garage', 'race', 'elim'] },
    { t: 'Trahison à la villa', s: "Don Varga t'invite à dîner. C'est un piège, et tout le monde le sait.", steps: ['goto', 'elim', 'survive', 'escape', 'bribe', 'collect', 'deliver', 'destroy', 'elim', 'boss'], boss: 'Don Varga' },
    { t: 'Le casino Lumi', s: "Le coffre du casino Moretti est plein. Le préfet de police aussi aime l'argent.", steps: ['bribe', 'collect', 'elim', 'race', 'steal', 'garage', 'escape', 'destroy', 'survive', 'elim'] },
    { t: 'Le Parrain', s: "Il ne reste qu'un homme entre toi et le contrôle de Porto Lumi : Don Moretti.", steps: ['buy', 'escort', 'elim', 'destroy', 'collect', 'tunnel', 'survive', 'escape', 'elim', 'boss'], boss: 'Don Moretti' },
    // ---- Sierra Verde (Colombie)
    { t: 'Atterrissage forcé', s: "Ton avion se pose en catastrophe à Sierra Verde. Rosa, la pilote, connaît tout le monde ici.", steps: ['goto', 'elim', 'collect', 'escort', 'race', 'escape', 'bribe', 'tunnel', 'deliver', 'elim'] },
    { t: 'La plantation', s: "Los Lobos ont pris la plantation de café de la famille de Rosa. Reprends-la.", steps: ['goto', 'elim', 'destroy', 'collect', 'survive', 'steal', 'garage', 'escape', 'race', 'elim'] },
    { t: 'Le pont de la rivière', s: "Le seul pont de la vallée sert de péage aux Lobos. Coupe leur route.", steps: ['destroy', 'elim', 'escape', 'tunnel', 'collect', 'bribe', 'deliver', 'survive', 'destroy', 'elim'] },
    { t: "L'hacienda", s: "El Lobo se cache dans son hacienda, protégé par ses hommes et par un colonel bien payé.", steps: ['goto', 'bribe', 'elim', 'collect', 'escort', 'elim', 'escape', 'race', 'destroy', 'boss'], boss: 'El Lobo' },
    { t: 'Le laboratoire caché', s: "Le Cartel del Cóndor a un repaire sous la jungle. On y entre par les tunnels.", steps: ['tunnel', 'elim', 'collect', 'destroy', 'survive', 'escape', 'steal', 'garage', 'elim', 'elim'] },
    { t: 'Fuite par la jungle', s: "Le Cóndor a mis ta tête à prix. Rosa doit rejoindre son avion avant l'aube.", steps: ['escort', 'survive', 'race', 'elim', 'tunnel', 'escape', 'collect', 'destroy', 'deliver', 'elim'] },
    { t: 'Le Cóndor', s: "Le chef du cartel t'attend. Après ça, tu quittes la Colombie, ou tu la diriges.", steps: ['buy', 'elim', 'destroy', 'collect', 'bribe', 'survive', 'escort', 'escape', 'elim', 'boss'], boss: 'El Cóndor' },
    // ---- Morro Azul (Brésil)
    { t: 'Bienvenue au morro', s: "Rosa te dépose à Morro Azul. Dans les ruelles des favelas, il faut gagner le respect avant tout.", steps: ['goto', 'bribe', 'collect', 'elim', 'race', 'steal', 'garage', 'escape', 'tunnel', 'elim'] },
    { t: 'Le baile funk', s: "DJ Favelinha organise le plus gros baile de l'année, mais le Bonde do Trovão veut tout arrêter.", steps: ['escort', 'elim', 'collect', 'survive', 'deliver', 'escape', 'race', 'destroy', 'escort', 'elim'] },
    { t: 'Le téléphérique', s: "Le téléphérique relie le morro à la ville. Le Trovão y fait passer ses affaires.", steps: ['goto', 'elim', 'tunnel', 'collect', 'destroy', 'escape', 'bribe', 'survive', 'race', 'elim'] },
    { t: 'Guerre des bondes', s: "Les deux gangs du morro se font la guerre. Frappe le Trovão à la tête.", steps: ['elim', 'destroy', 'elim', 'collect', 'escape', 'survive', 'steal', 'garage', 'elim', 'boss'], boss: 'Trovão' },
    { t: 'La plage', s: "Une cargaison du Comando Sombra arrive par la plage de Copa Azul cette nuit.", steps: ['race', 'deliver', 'elim', 'escort', 'collect', 'escape', 'tunnel', 'destroy', 'survive', 'elim'] },
    { t: 'Tout le monde te cherche', s: "Police, gangs, cartel : toute la ville est à tes trousses. Tiens bon.", steps: ['survive', 'escape', 'bribe', 'elim', 'collect', 'tunnel', 'destroy', 'escort', 'survive', 'elim'] },
    { t: 'Le dernier coup', s: "Sombra, le chef du Comando, contrôle tout Morro Azul. Le dernier coup, le plus gros.", steps: ['buy', 'elim', 'destroy', 'collect', 'escort', 'survive', 'tunnel', 'escape', 'elim', 'boss'], boss: 'Sombra' },
  ];

  const STEP_LABEL = {
    goto: 'Rendez-vous', steal: 'Vol de voiture', garage: 'Garage', buy: 'Équipement', deliver: 'Livraison',
    collect: 'Récupération', elim: 'Fusillade', boss: 'Chef de gang', escape: 'Fuite', survive: 'Survie',
    tunnel: 'Tunnel', bribe: 'Corruption', escort: 'Escorte', destroy: 'Convoi', race: 'Course',
  };

  const WEAPONS = [
    { id: 'pistol', name: 'Pistolet', price: 0, lvl: 1, rate: .28, dmg: 18, spread: .04, pellets: 1, speed: 760, life: .6, desc: 'Fiable, tir semi-auto.' },
    { id: 'uzi', name: 'Mitraillette', price: 1500, lvl: 2, rate: .08, dmg: 10, spread: .12, pellets: 1, speed: 760, life: .55, desc: 'Cadence très rapide, peu précise.' },
    { id: 'shotgun', name: 'Fusil à pompe', price: 4000, lvl: 4, rate: .7, dmg: 14, spread: .36, pellets: 7, speed: 700, life: .32, desc: 'Dévastateur au contact.' },
    { id: 'rifle', name: "Fusil d'assaut", price: 9000, lvl: 8, rate: .11, dmg: 20, spread: .05, pellets: 1, speed: 900, life: .8, desc: 'Précis et rapide, longue portée.' },
    { id: 'sniper', name: 'Fusil de précision', price: 15000, lvl: 11, rate: 1.1, dmg: 130, spread: 0, pellets: 1, speed: 1400, life: 1.1, desc: 'Une balle, un ennemi.' },
    { id: 'rocket', name: 'Lance-roquettes', price: 30000, lvl: 15, rate: 1.2, dmg: 90, spread: 0, pellets: 1, speed: 520, life: 1.3, explosive: true, desc: 'Explose voitures et groupes.' },
    { id: 'minigun', name: 'Minigun', price: 70000, lvl: 24, rate: .045, dmg: 14, spread: .15, pellets: 1, speed: 820, life: .7, desc: 'Un mur de balles.' },
  ];

  const GEAR = [
    { id: 'armor1', name: 'Gilet pare-balles', price: 1000, lvl: 1, kind: 'armor', value: 50, desc: '50 points d’armure au début de chaque niveau.' },
    { id: 'armor2', name: 'Gilet renforcé', price: 6000, lvl: 6, kind: 'armor', value: 100, desc: '100 points d’armure.' },
    { id: 'armor3', name: 'Armure tactique', price: 20000, lvl: 14, kind: 'armor', value: 150, desc: '150 points d’armure.' },
    { id: 'medkit', name: 'Trousse de soins', price: 400, lvl: 1, kind: 'medkit', max: 5, desc: '+50 santé (touche H). Max 5.' },
    { id: 'nitro', name: 'Nitro x3', price: 600, lvl: 2, kind: 'nitro', max: 9, desc: 'Boost en voiture (touche N). Max 9.' },
    { id: 'carArmor', name: 'Blindage de voiture', price: 5000, lvl: 5, kind: 'perk', desc: 'Tes voitures prennent 2 fois moins de dégâts.' },
    { id: 'radio', name: 'Brouilleur radio', price: 8000, lvl: 10, kind: 'perk', desc: 'Moins de renforts et la police te perd plus vite.' },
    { id: 'contacts', name: 'Carnet de contacts', price: 12000, lvl: 12, kind: 'perk', desc: 'Soudoyer les agents coûte 40 % de moins.' },
  ];

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

  return { SHOP_CONFIG, REGIONS, LEVELS, STEP_LABEL, WEAPONS, GEAR, AUDIO_FILES };
})();
