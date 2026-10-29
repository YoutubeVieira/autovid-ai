/* Adaptations du texte selon le genre de la voix : le guide s'appelle Léo avec une voix d'homme, Léa avec une
   voix de femme, et les mots qui s'accordent avec la personne qui parle sont mis au bon genre. */
"use strict";
const FEMALE = {
  fr: [["Je suis Léo", "Je suis Léa"], ["Content de vous revoir", "Contente de vous revoir"]],
  en: [["I'm Léo", "I'm Léa"]],
  pt: [["Eu sou o Léo", "Eu sou a Léa"], ["seu guia virtual", "sua guia virtual"], ["Obrigado por me dizer", "Obrigada por me dizer"], ["Sou um guia virtual, não um médico", "Sou uma guia virtual, não uma médica"]]
};
function adapt(text, lang, gender) {
  if (gender !== "f") return text;
  return (FEMALE[lang] || []).reduce((t, p) => t.split(p[0]).join(p[1]), text);
}
module.exports = { adapt, FEMALE };
