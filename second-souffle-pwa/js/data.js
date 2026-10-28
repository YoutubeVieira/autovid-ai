/* Données : catégories, zones sensibles, 28 exercices à filmer, fiches du coach privé, guide d'anatomie.
   Les contenus d'exercice et d'anatomie sont des propositions : ils doivent être validés par un
   kinésithérapeute ou un enseignant en activité physique adaptée avant publication. */
(function (g) {
  var CATS = ["warm", "lower", "upper", "core", "balance", "stretch"];
  var ZONES = ["cou", "epaules", "dos", "poignets", "hanches", "genoux"];

  function ex(id, cat, z, v1, fr, en, pt, cfr, cen, cpt) {
    return { id: id, cat: cat, z: z, v1: v1, n: { fr: fr, en: en, pt: pt }, c: { fr: cfr || "", en: cen || "", pt: cpt || "" } };
  }

  var EX = [
    ex("marche", "warm", ["genoux", "hanches"], 1, "Marche sur place", "Marching in place", "Marcha no lugar", "Genoux bas, bras qui balancent.", "Low knees, arms swinging.", "Joelhos baixos, braços balançando."),
    ex("epaules-rot", "warm", ["epaules"], 1, "Rotations d'épaules", "Shoulder rolls", "Rotação de ombros", "Petits cercles, bras détendus.", "Small circles, arms relaxed.", "Círculos pequenos, braços relaxados."),
    ex("cou-rot", "warm", ["cou"], 1, "Rotations lentes du cou", "Slow neck rotations", "Rotações lentas do pescoço", "Demi-cercles, sans forcer.", "Half circles, no forcing.", "Meios círculos, sem forçar."),
    ex("cercles", "warm", ["poignets"], 0, "Cercles de poignets et de chevilles", "Wrist and ankle circles", "Círculos de punhos e tornozelos"),
    ex("balancement", "warm", ["epaules"], 0, "Balancement des bras", "Arm swings", "Balanço dos braços"),

    ex("squat", "lower", ["genoux", "hanches"], 1, "Squat sur chaise", "Chair squat", "Agachamento na cadeira", "Asseyez-vous, relevez-vous, lentement.", "Sit down, stand up, slowly.", "Sente-se e levante-se, devagar."),
    ex("pont", "lower", ["dos"], 1, "Pont fessier", "Glute bridge", "Ponte de glúteos", "Allongé, soulevez le bassin.", "Lying down, lift your hips.", "Deitado, eleve o quadril."),
    ex("levee-jambe", "lower", ["hanches"], 1, "Levée de jambe allongée", "Lying leg raise", "Elevação de perna deitado", "Jambe tendue, montée lente.", "Straight leg, slow lift.", "Perna esticada, subida lenta."),
    ex("ext-jambe", "lower", ["genoux"], 1, "Extension de jambe assise", "Seated leg extension", "Extensão de perna sentado", "Tendez la jambe, tenez 2 secondes.", "Straighten the leg, hold 2 seconds.", "Estique a perna, segure 2 segundos."),
    ex("fente", "lower", ["genoux", "hanches"], 0, "Fente arrière avec appui", "Supported reverse lunge", "Avanço reverso com apoio"),
    ex("pointes", "lower", [], 0, "Montée sur pointes avec appui", "Supported calf raise", "Elevação de panturrilha com apoio"),
    ex("talon-pointe", "lower", ["hanches"], 0, "Marche talon-pointe", "Heel-to-toe walk", "Caminhada calcanhar-ponta"),

    ex("pompes-mur", "upper", ["epaules", "poignets"], 1, "Pompes au mur", "Wall push-ups", "Flexão na parede", "Mains à hauteur d'épaules.", "Hands at shoulder height.", "Mãos na altura dos ombros."),
    ex("rowing", "upper", ["dos", "epaules"], 1, "Rowing à l'élastique assis", "Seated band row", "Remada sentado com elástico", "Tirez les coudes vers l'arrière.", "Pull your elbows back.", "Puxe os cotovelos para trás."),
    ex("developpe", "upper", ["epaules"], 1, "Développé d'épaules assis", "Seated shoulder press", "Desenvolvimento de ombros sentado", "Poussez vers le haut, sans cambrer.", "Press up, don't arch your back.", "Empurre para cima, sem arquear as costas."),
    ex("elevations", "upper", ["epaules"], 0, "Élévations latérales", "Lateral raises", "Elevação lateral"),
    ex("flexion-bras", "upper", ["poignets"], 0, "Flexion de bras", "Arm curls", "Rosca de braço"),

    ex("dead-bug", "core", ["dos"], 1, "Dead bug lent", "Slow dead bug", "Dead bug lento", "Dos au sol, bras et jambe opposés.", "Back on the floor, opposite arm and leg.", "Costas no chão, braço e perna opostos."),
    ex("bascule", "core", ["dos"], 1, "Bascule de bassin", "Pelvic tilt", "Inclinação pélvica", "Aplatissez le bas du dos au sol.", "Flatten your lower back to the floor.", "Encoste a lombar no chão."),
    ex("gainage", "core", ["dos", "poignets", "epaules"], 1, "Gainage sur les genoux", "Kneeling plank", "Prancha com joelhos apoiados", "Corps aligné, respiration calme.", "Body aligned, calm breathing.", "Corpo alinhado, respiração calma."),
    ex("bird-dog", "core", ["dos", "poignets", "genoux"], 1, "Quadrupédie bras-jambe opposés", "Bird dog", "Bird dog (quatro apoios)", "Bras et jambe opposés, bassin stable.", "Opposite arm and leg, hips steady.", "Braço e perna opostos, quadril estável."),
    ex("rot-tronc", "core", ["dos"], 0, "Rotation du tronc assis", "Seated trunk rotation", "Rotação de tronco sentado"),

    ex("une-jambe", "balance", ["hanches", "genoux"], 1, "Appui sur une jambe près de la chaise", "Single-leg stand near a chair", "Apoio em uma perna perto da cadeira", "Une main sur la chaise, regard devant.", "One hand on the chair, eyes ahead.", "Uma mão na cadeira, olhar à frente."),

    ex("chat", "stretch", ["dos", "poignets"], 1, "Étirement du chat", "Cat stretch", "Alongamento do gato", "Dos rond, puis dos creux, lentement.", "Round the back, then arch, slowly.", "Arredonde as costas, depois arqueie, devagar."),
    ex("hanches-etir", "stretch", ["hanches", "genoux"], 1, "Étirement des hanches", "Hip stretch", "Alongamento de quadril", "Fente basse, sans forcer.", "Low lunge, no forcing.", "Avanço baixo, sem forçar."),
    ex("respiration", "stretch", [], 1, "Respiration allongée", "Lying breathing", "Respiração deitado", "Genoux pliés, ventre qui se gonfle.", "Knees bent, belly rising.", "Joelhos dobrados, barriga subindo."),
    ex("mollets", "stretch", ["genoux"], 1, "Étirement des mollets au mur", "Wall calf stretch", "Alongamento de panturrilha na parede", "Talon au sol, penchez-vous vers le mur.", "Heel down, lean toward the wall.", "Calcanhar no chão, incline-se para a parede."),
    ex("pectoraux", "stretch", ["epaules"], 0, "Étirement des pectoraux dans une porte", "Doorway chest stretch", "Alongamento do peitoral na porta")
  ];

  var BY_ID = {};
  EX.forEach(function (e) { BY_ID[e.id] = e; });

  /* Fiches du coach privé : exercices ciblés par thème. */
  var FICHES = {
    genoux: [["pont", "2 × 12"], ["levee-jambe", "2 × 10"], ["marche", "5 min"]],
    dos: [["bascule", "2 × 10"], ["dead-bug", "2 × 8"], ["chat", "1 min"]]
  };

  var AMBS = [
    { id: "commun", sw: ["#3B3F8F", "#F2784B", "#2F8F6B"] },
    { id: "aube", sw: ["#6B3FA0", "#E8636F", "#7FA88F"] },
    { id: "ardoise", sw: ["#1F5F7A", "#E0672B", "#4C8C6B"] }
  ];

  /* Guide d'anatomie simplifié. Faits généraux, à valider par un professionnel. */
  var ANAT = {
    cou: { b: { fr: "7 vertèbres cervicales", en: "7 cervical vertebrae", pt: "7 vértebras cervicais" }, m: { fr: "Trapèzes, sterno-cléido-mastoïdiens", en: "Trapezius, sternocleidomastoid", pt: "Trapézio, esternocleidomastoideo" } },
    epaules: { b: { fr: "Omoplate, clavicule, humérus", en: "Shoulder blade, collarbone, humerus", pt: "Escápula, clavícula, úmero" }, m: { fr: "Deltoïdes, coiffe des rotateurs", en: "Deltoids, rotator cuff", pt: "Deltoides, manguito rotador" } },
    dos: { b: { fr: "Colonne vertébrale (33 vertèbres)", en: "Spine (33 vertebrae)", pt: "Coluna vertebral (33 vértebras)" }, m: { fr: "Érecteurs du rachis, grand dorsal", en: "Erector spinae, latissimus dorsi", pt: "Eretores da espinha, grande dorsal" } },
    poignets: { b: { fr: "Carpe (8 os), radius, ulna", en: "Carpals (8 bones), radius, ulna", pt: "Carpo (8 ossos), rádio, ulna" }, m: { fr: "Fléchisseurs et extenseurs de l'avant-bras", en: "Forearm flexors and extensors", pt: "Flexores e extensores do antebraço" } },
    hanches: { b: { fr: "Bassin, fémur", en: "Pelvis, femur", pt: "Pelve, fêmur" }, m: { fr: "Fessiers, psoas", en: "Glutes, psoas", pt: "Glúteos, psoas" } },
    genoux: { b: { fr: "Fémur, tibia, rotule", en: "Femur, tibia, kneecap", pt: "Fêmur, tíbia, patela" }, m: { fr: "Quadriceps, ischio-jambiers", en: "Quadriceps, hamstrings", pt: "Quadríceps, isquiotibiais" } }
  };

  g.SS = g.SS || {};
  g.SS.data = { CATS: CATS, ZONES: ZONES, EX: EX, BY_ID: BY_ID, FICHES: FICHES, AMBS: AMBS, ANAT: ANAT };
})(typeof window !== "undefined" ? window : globalThis);
