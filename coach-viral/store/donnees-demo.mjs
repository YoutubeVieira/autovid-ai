/* Exemples affichés sur les captures du Play Store (réponses écrites d'avance, en français, niche capoeira). */
export const IDEES = {
  ideas: [
    {
      titre: "3 erreurs de débutant en ginga", accroche: "Tu fais sûrement l'erreur n°2 sans le savoir.",
      texte_ecran: "3 erreurs en ginga", format: "tutoriel", duree_secondes: 28,
      script: [
        { temps: "0-2s", visuel: "Gros plan sur les pieds", parole: "Tu fais sûrement l'erreur n°2 sans le savoir." },
        { temps: "2-10s", visuel: "Ginga trop raide, croix rouge", parole: "Erreur 1 : les jambes bloquées. La ginga doit respirer." },
        { temps: "10-20s", visuel: "Regard au sol", parole: "Erreur 2 : tu regardes tes pieds. Regarde ton partenaire." }
      ],
      appel_action: "Enregistre pour ton prochain cours", legende: "La ginga, c'est la base. Corrige ces 3 erreurs dès ce soir.",
      hashtags: ["capoeira", "ginga", "debutant"], pourquoi_ca_marche: "Promesse claire et curiosité sur l'erreur n°2."
    },
    {
      titre: "Ma 1re roda, honnêtement", accroche: "J'ai failli ne jamais revenir après ma première roda.",
      texte_ecran: "Ma 1re roda", format: "histoire", duree_secondes: 35,
      script: [{ temps: "0-3s", visuel: "Face caméra, berimbau derrière", parole: "J'ai failli ne jamais revenir après ma première roda." }],
      appel_action: "Raconte ta 1re roda en commentaire", legende: "Tout le monde a eu peur la première fois.",
      hashtags: ["capoeira", "roda"], pourquoi_ca_marche: "Histoire personnelle et émotion."
    }
  ]
};

export const SCORE = {
  score_global: 74, resume: "Bonne énergie et vrai savoir-faire. L'accroche arrive un peu tard.",
  criteres: [
    { nom: "Accroche (0-2 s)", note: 6, constat: "Le texte apparaît à 2,5 s.", conseil: "Afficher « 3 erreurs » dès la première image." },
    { nom: "Rythme et montage", note: 8, constat: "Coupes toutes les 2 à 3 s.", conseil: "Garder ce rythme." },
    { nom: "Texte à l'écran", note: 7, constat: "Lisible mais petit.", conseil: "Agrandir et centrer." },
    { nom: "Appel à l'action", note: 8, constat: "Clair en fin de vidéo.", conseil: "Le dire aussi à l'oral." }
  ],
  accroches_alternatives: ["Arrête de faire ça en ginga.", "Le secret des mestres que personne ne dit."],
  priorites: ["Texte dès la 1re seconde", "Accroche orale plus courte", "Musique plus présente"],
  limites: "Le son n'a pas été écouté."
};

export const THEMES = {
  themes: [
    { theme: "Défi ginga 7 jours", pourquoi_maintenant: "Les vidéos « défi 7 jours » montent cette semaine.", accroches: ["J'ai fait la ginga 7 jours de suite", "Jour 1 vs jour 7", "Personne ne tient 7 jours"], format: "défi", potentiel: 84, concurrence: "faible", sources: [] },
    { theme: "Batizado : à quoi s'attendre", pourquoi_maintenant: "Saison des batizados : beaucoup de questions.", accroches: ["Ton 1er batizado en 30 s"], format: "explication", potentiel: 71, concurrence: "moyenne", sources: [] }
  ]
};

export const VERSION = {
  titre: "La patience de la roda", legende: "Ce que la capoeira m'a appris.", hashtags: ["capoeira", "patience"],
  ambiance_musique: "berimbau doux", pourquoi_mieux: "Accroche personnelle dès la première seconde, une seule idée forte.",
  scenes: [
    { haut: "Dans la roda, celui qui se précipite tombe.", bas: "La capoeira m'a appris la patience.", voix: "Dans la roda, celui qui se précipite tombe.", prompt_image: "", duree: 4 },
    { haut: "Attendre son moment, c'est déjà jouer.", bas: "Et toi, tu sais attendre ?", voix: "Attendre son moment, c'est déjà jouer.", prompt_image: "", duree: 4 }
  ]
};

export const ANALYSE = {
  style: { format: "citation émouvante sur image 3D", visuel: "Image 3D style film d'animation, lumière chaude, fond flou", texte: "Phrase en haut, chute en bas, blanc", voix: "Voix douce et posée", rythme: "lent", duree_secondes: 8 },
  pourquoi_ca_marche: ["Émotion universelle", "Phrase courte qui intrigue"], a_ameliorer: ["Accroche plus personnelle"], nouvelle_version: VERSION
};

export const ADAPT = {
  versions: [
    { plateforme: "tiktok", titre: "", legende: "La ginga, c'est la base 🥋 Corrige ces 3 erreurs ce soir.", hashtags: ["capoeira", "ginga", "fyp"], conseils: "Publie entre 18 h et 21 h, son tendance discret." },
    { plateforme: "instagram", titre: "", legende: "3 erreurs que font TOUS les débutants en ginga 👇", hashtags: ["capoeira", "reels"], conseils: "Couverture avec le texte « 3 erreurs »." },
    { plateforme: "youtube", titre: "3 erreurs de débutant en capoeira #Shorts", legende: "Corrige ta ginga en 30 secondes.", hashtags: ["shorts", "capoeira"], conseils: "Titre avec le mot-clé au début." }
  ]
};

/* Faux client : choisit la réponse selon la demande. */
export const fauxClient = {
  beta: { messages: {
    async create() { return { stop_reason: "end_turn", content: [{ type: "text", text: "Tendances de la semaine." }] }; },
    async parse(p) {
      const t = JSON.stringify(p.messages[0].content);
      const out = /short-video themes/.test(t) ? THEMES : /video ideas/.test(t) ? IDEES : /Rate this short video/.test(t) ? SCORE
        : /Analyse this short video/.test(t) ? ANALYSE : /Adapt this video/.test(t) ? ADAPT : /Write an ORIGINAL/.test(t) ? VERSION : IDEES;
      return { stop_reason: "end_turn", parsed_output: out };
    }
  } }
};
