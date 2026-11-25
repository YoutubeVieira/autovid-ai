/* Faux client Anthropic : enregistre les demandes et renvoie des réponses écrites d'avance. */
export const SAMPLES = {
  ideas: {
    ideas: [{
      titre: "3 mouvements pour débuter", accroche: "Tu n'as jamais fait de capoeira ? Commence par ça.",
      texte_ecran: "3 mouvements, 0 expérience", format: "tutoriel", duree_secondes: 25,
      script: [{ temps: "0-2s", visuel: "Plan serré, ginga", parole: "Tu n'as jamais fait de capoeira ?" }],
      appel_action: "Enregistre pour ton premier cours", legende: "Ton premier pas en capoeira", hashtags: ["capoeira", "#debutant"],
      pourquoi_ca_marche: "Promesse claire et simple."
    }]
  },
  score: {
    score_global: 62, resume: "Bonne énergie, accroche trop lente.",
    criteres: [{ nom: "Accroche (0-2 s)", note: 4, constat: "Le titre arrive à 3 s.", conseil: "Mettre le texte dès la première image." }],
    accroches_alternatives: ["Arrête de faire cette erreur en ginga"], priorites: ["Accroche plus rapide"], limites: "Pas de son analysé."
  },
  profile: {
    score_profil: 55, resume: "Compte régulier, peu de partages.", chiffres_lus: [{ indicateur: "Abonnés", valeur: "1 200" }],
    forces: ["Régularité"], faiblesses: ["Accroches faibles"], plan_7_jours: [{ jour: "Lundi", action: "Tester 2 accroches", idee_video: "Erreur de débutant" }],
    frequence_conseillee: "1 vidéo par jour", meilleurs_formats: ["Tutoriel court"]
  },
  adapt: {
    versions: [
      { plateforme: "tiktok", titre: "", legende: "Ton premier pas", hashtags: ["capoeira"], conseils: "Publie le soir." },
      { plateforme: "youtube", titre: "Capoeira pour débutants #Shorts", legende: "Les bases", hashtags: ["shorts"], conseils: "Miniature lisible." }
    ]
  }
};

export function fakeClient({ output, stop_reason = "end_turn", error } = {}) {
  const calls = [];
  return {
    calls,
    beta: {
      messages: {
        async parse(params) {
          calls.push(params);
          if (error) throw error;
          return { stop_reason, parsed_output: output === undefined ? null : output, content: [] };
        }
      }
    }
  };
}
