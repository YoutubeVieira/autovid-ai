/* Néon Bay : traductions (fr par défaut, en, es, pt).
   Le jeu est écrit en français ; chaque texte affiché passe par t(), qui cherche
   la traduction dans NB_DICT (js/i18n-dict.js) puis dans les modèles ci-dessous
   (textes qui contiennent des nombres ou des noms). */
window.NB_I18N = (() => {
  'use strict';
  const LANGS = ['fr', 'en', 'es', 'pt'];
  const NAMES = { fr: 'Français', en: 'English', es: 'Español', pt: 'Português' };
  let lang = 'fr';
  try {
    const saved = JSON.parse(localStorage.getItem('neonbay.save.v2') || '{}').lang;
    const nav = (navigator.language || 'fr').slice(0, 2).toLowerCase();
    lang = LANGS.includes(saved) ? saved : LANGS.includes(nav) ? nav : 'en';
  } catch (e) { lang = 'fr'; }
  const EXTRA = {
    'Jouer': { en: 'Play', es: 'Jugar', pt: 'Jogar' },
    'Continuer': { en: 'Continue', es: 'Continuar', pt: 'Continuar' },
    '+50 santé (touche H). Max 5.': { en: '+50 health (H key). Max 5.', es: '+50 de salud (tecla H). Máx. 5.', pt: '+50 de saúde (tecla H). Máx. 5.' },
    "Tu as aimé ? La suite t'attend.": { en: 'Enjoyed it? The rest is waiting.', es: '¿Te gustó? Lo mejor está por venir.', pt: 'Curtiu? O resto te espera.' },
    "Le lien de paiement n'est pas encore configuré (SHOP_CONFIG.buyUrl dans js/data.js).": { en: 'Purchases are not available yet.', es: 'Las compras aún no están disponibles.', pt: 'As compras ainda não estão disponíveis.' },
    'Aide activée : plus de temps et ennemis moins dangereux': { en: 'Assist on: more time and weaker enemies', es: 'Ayuda activada: más tiempo y enemigos menos peligrosos', pt: 'Ajuda ativada: mais tempo e inimigos menos perigosos' },
    'Qualité graphique réduite pour plus de fluidité': { en: 'Graphics quality lowered for smoother play', es: 'Calidad gráfica reducida para más fluidez', pt: 'Qualidade gráfica reduzida para mais fluidez' },
    'Haute': { en: 'High', es: 'Alta', pt: 'Alta' }, 'Moyenne': { en: 'Medium', es: 'Media', pt: 'Média' }, 'Basse': { en: 'Low', es: 'Baja', pt: 'Baixa' },
  };
  const dict = () => Object.assign({}, window.NB_DICT || {}, EXTRA);
  // [motif sur le texte français, { en, es, pt }] ; $1, $2… sont traduits à leur tour
  const P = [
    [/^Rejoins (.+)$/, { en: 'Go to $1', es: 'Ve a $1', pt: 'Vá até $1' }],
    [/^Livre la marchandise à (.+) en voiture$/, { en: 'Deliver the goods to $1 by car', es: 'Entrega la mercancía en $1 en coche', pt: 'Entregue a mercadoria em $1 de carro' }],
    [/^Récupère les valises près de (.+) \((\d+)\/(\d+)\)$/, { en: 'Grab the briefcases near $1 ($2/$3)', es: 'Recoge los maletines cerca de $1 ($2/$3)', pt: 'Pegue as maletas perto de $1 ($2/$3)' }],
    [/^Élimine (.+), chef de (.+)$/, { en: 'Take down $1, boss of $2', es: 'Acaba con $1, jefe de $2', pt: 'Derrube $1, chefe de $2' }],
    [/^Neutralise (.+) \((\d+) restants\)$/, { en: 'Take out $1 ($2 left)', es: 'Neutraliza a $1 ($2 restantes)', pt: 'Neutralize $1 ($2 restantes)' }],
    [/^Retrouve (.+)$/, { en: 'Find $1', es: 'Encuentra a $1', pt: 'Encontre $1' }],
    [/^Emmène (.+) à (.+) en vie$/, { en: 'Get $1 to $2 alive', es: 'Lleva a $1 a $2 con vida', pt: 'Leve $1 até $2 com vida' }],
    [/^Détruis le convoi de (.+) \((\d+) restants\)$/, { en: 'Destroy $1\u2019s convoy ($2 left)', es: 'Destruye el convoy de $1 ($2 restantes)', pt: 'Destrua o comboio de $1 ($2 restantes)' }],
    [/^Course : passe les checkpoints \((\d+)\/4\)$/, { en: 'Race: hit the checkpoints ($1/4)', es: 'Carrera: pasa los puntos de control ($1/4)', pt: 'Corrida: passe pelos checkpoints ($1/4)' }],
    [/^Va voir l’agent corrompu et donne-lui (.+) \(E\)$/, { en: 'Meet the corrupt cop and hand over $1 (E)', es: 'Ve a ver al agente corrupto y dale $1 (E)', pt: 'Encontre o policial corrupto e entregue $1 (E)' }],
    [/^(.+) \(monte dans une voiture : E\)$/, { en: '$1 (get in a car: E)', es: '$1 (súbete a un coche: E)', pt: '$1 (entre em um carro: E)' }],
    [/^Niveau (\d+) · (.+) · étape (\d+)\/10$/, { en: 'Level $1 · $2 · step $3/10', es: 'Nivel $1 · $2 · etapa $3/10', pt: 'Nível $1 · $2 · etapa $3/10' }],
    [/^Niveau (\d+) · (.+)$/, { en: 'Level $1 · $2', es: 'Nivel $1 · $2', pt: 'Nível $1 · $2' }],
    [/^Niveau (\d+) : (.+)$/, { en: 'Level $1: $2', es: 'Nivel $1: $2', pt: 'Nível $1: $2' }],
    [/^Niveau (\d+) terminé$/, { en: 'Level $1 complete', es: 'Nivel $1 completado', pt: 'Nível $1 concluído' }],
    [/^Niveau (\d+)$/, { en: 'Level $1', es: 'Nivel $1', pt: 'Nível $1' }],
    [/^(.+) · (.+) · Niveau (\d+)\/30$/, { en: '$1 · $2 · Level $3/30', es: '$1 · $2 · Nivel $3/30', pt: '$1 · $2 · Nível $3/30' }],
    [/^(.+) · niveaux (\d+)–(\d+)$/, { en: '$1 · levels $2–$3', es: '$1 · niveles $2–$3', pt: '$1 · níveis $2–$3' }],
    [/^Étape (\d+)\/10 · (.+)$/, { en: 'Step $1/10 · $2', es: 'Etapa $1/10 · $2', pt: 'Etapa $1/10 · $2' }],
    [/^Étape (\d+)\/10 réussie · \+(.+)$/, { en: 'Step $1/10 done · +$2', es: 'Etapa $1/10 superada · +$2', pt: 'Etapa $1/10 concluída · +$2' }],
    [/^Mission réussie ! \+(.+)$/, { en: 'Mission complete! +$1', es: '¡Misión cumplida! +$1', pt: 'Missão cumprida! +$1' }],
    [/^Point (\d+)\/(\d+)$/, { en: 'Point $1/$2', es: 'Punto $1/$2', pt: 'Ponto $1/$2' }],
    [/^Checkpoint (\d+)\/4$/, { en: 'Checkpoint $1/4', es: 'Punto de control $1/4', pt: 'Checkpoint $1/4' }],
    [/^Soins (\d+) · Nitro (\d+)$/, { en: 'Medkits $1 · Nitro $2', es: 'Botiquines $1 · Nitro $2', pt: 'Kits $1 · Nitro $2' }],
    [/^Agents soudoyés \(−(.+)\)$/, { en: 'Cops bribed (−$1)', es: 'Agentes sobornados (−$1)', pt: 'Policiais subornados (−$1)' }],
    [/^Voiture repeinte · police semée \(−(.+)\)$/, { en: 'Car repainted · cops lost (−$1)', es: 'Coche repintado · policía despistada (−$1)', pt: 'Carro repintado · polícia despistada (−$1)' }],
    [/^Il faut (.+) pour repeindre$/, { en: 'You need $1 to repaint', es: 'Necesitas $1 para repintar', pt: 'Você precisa de $1 para repintar' }],
    [/^Il te faut (.+) pour soudoyer les agents$/, { en: 'You need $1 to bribe the cops', es: 'Necesitas $1 para sobornar a los agentes', pt: 'Você precisa de $1 para subornar a polícia' }],
    [/^B : soudoyer les agents \((.+)\)$/, { en: 'B: bribe the cops ($1)', es: 'B: sobornar a los agentes ($1)', pt: 'B: subornar a polícia ($1)' }],
    [/^E : payer l’agent \((.+)\)$/, { en: 'E: pay the cop ($1)', es: 'E: pagar al agente ($1)', pt: 'E: pagar o policial ($1)' }],
    [/^L’agent empoche (.+) et te donne le tuyau$/, { en: 'The cop pockets $1 and gives you the tip', es: 'El agente se embolsa $1 y te pasa el dato', pt: 'O policial embolsa $1 e te passa a dica' }],
    [/^Pas assez d’argent : l’agent prend (.+) et te balance !$/, { en: 'Not enough cash: the cop takes $1 and rats you out!', es: '¡No te alcanza: el agente se queda $1 y te delata!', pt: 'Dinheiro insuficiente: o policial pega $1 e te dedura!' }],
    [/^Termine le niveau (\d+) d’abord$/, { en: 'Finish level $1 first', es: 'Termina primero el nivel $1', pt: 'Termine o nível $1 primeiro' }],
    [/^(.+) est tombé !$/, { en: '$1 is down!', es: '¡$1 ha caído!', pt: '$1 caiu!' }],
    [/^(.+) te suit$/, { en: '$1 is following you', es: '$1 te sigue', pt: '$1 está te seguindo' }],
    [/^(.+) monte dans la voiture$/, { en: '$1 gets in the car', es: '$1 se sube al coche', pt: '$1 entra no carro' }],
    [/^(.+) n’a pas survécu$/, { en: '$1 didn\u2019t make it', es: '$1 no sobrevivió', pt: '$1 não sobreviveu' }],
    [/^\+ (.+) par étape$/, { en: '+ $1 per step', es: '+ $1 por etapa', pt: '+ $1 por etapa' }],
    [/^Conseillé : (.+)$/, { en: 'Recommended: $1', es: 'Recomendado: $1', pt: 'Recomendado: $1' }],
    [/^Rapide : moins de (\d+) min (\d+)$/, { en: 'Fast: under $1 min $2', es: 'Rápido: menos de $1 min $2', pt: 'Rápido: menos de $1 min $2' }],
    [/^Propre : santé ≥ 60 % et 3 passants K\.O\. maximum \((\d+)\)$/, { en: 'Clean: health ≥ 60% and 3 bystanders K.O. max ($1)', es: 'Limpio: salud ≥ 60 % y máximo 3 transeúntes K.O. ($1)', pt: 'Limpo: saúde ≥ 60% e no máximo 3 pedestres nocauteados ($1)' }],
    [/^(\d+) min (\d+)$/, { en: '$1 min $2', es: '$1 min $2', pt: '$1 min $2' }],
    [/^Nouveau dans la boutique : (.+)$/, { en: 'New in the shop: $1', es: 'Nuevo en la tienda: $1', pt: 'Novo na loja: $1' }],
    [/^(\d+)\/30 niveaux$/, { en: '$1/30 levels', es: '$1/30 niveles', pt: '$1/30 níveis' }],
    [/^(\d+)\/(\d+) succès$/, { en: '$1/$2 achievements', es: '$1/$2 logros', pt: '$1/$2 conquistas' }],
    [/^Musique : (oui|non)$/, { en: 'Music: $1', es: 'Música: $1', pt: 'Música: $1' }],
    [/^Bruitages : (oui|non)$/, { en: 'Sound effects: $1', es: 'Efectos: $1', pt: 'Efeitos: $1' }],
    [/^Vibrations : (oui|non)$/, { en: 'Vibration: $1', es: 'Vibración: $1', pt: 'Vibração: $1' }],
    [/^Caméra : (.+)$/, { en: 'Camera: $1', es: 'Cámara: $1', pt: 'Câmera: $1' }],
    [/^Jeu complet · (.+)$/, { en: 'Full game · $1', es: 'Juego completo · $1', pt: 'Jogo completo · $1' }],
    [/^Débloquer le jeu complet · (.+)$/, { en: 'Unlock the full game · $1', es: 'Desbloquear el juego completo · $1', pt: 'Desbloquear o jogo completo · $1' }],
    [/^Série : (\d+) jours? · \+(.+) chacun$/, { en: 'Streak: $1 day(s) · +$2 each', es: 'Racha: $1 día(s) · +$2 cada uno', pt: 'Sequência: $1 dia(s) · +$2 cada' }],
    [/^\+(.+) chacun$/, { en: '+$1 each', es: '+$1 cada uno', pt: '+$1 cada' }],
    [/^Vole (\d+) voitures$/, { en: 'Steal $1 cars', es: 'Roba $1 coches', pt: 'Roube $1 carros' }],
    [/^Sème la police (\d+) fois$/, { en: 'Lose the cops $1 times', es: 'Despista a la policía $1 veces', pt: 'Despiste a polícia $1 vezes' }],
    [/^Neutralise (\d+) ennemis$/, { en: 'Take out $1 enemies', es: 'Neutraliza a $1 enemigos', pt: 'Neutralize $1 inimigos' }],
    [/^Prends (\d+) tunnels$/, { en: 'Take $1 tunnels', es: 'Usa $1 túneles', pt: 'Use $1 túneis' }],
    [/^Soudoie la police (\d+) fois$/, { en: 'Bribe the cops $1 times', es: 'Soborna a la policía $1 veces', pt: 'Suborne a polícia $1 vezes' }],
    [/^Fais exploser (\d+) véhicules$/, { en: 'Blow up $1 vehicles', es: 'Haz explotar $1 vehículos', pt: 'Exploda $1 veículos' }],
    [/^Ramasse (.+) \$ par terre$/, { en: 'Pick up $$1 from the street', es: 'Recoge $1 $ del suelo', pt: 'Pegue $1 $ do chão' }],
    [/^Termine (\d+) niveaux différents$/, { en: 'Complete $1 different levels', es: 'Completa $1 niveles distintos', pt: 'Conclua $1 níveis diferentes' }],
    [/^Termine (\d+) niveau\(x\)$/, { en: 'Complete $1 level(s)', es: 'Completa $1 nivel(es)', pt: 'Conclua $1 nível(is)' }],
    [/^Obtiens 3 étoiles sur (\d+) niveaux$/, { en: 'Get 3 stars on $1 levels', es: 'Consigue 3 estrellas en $1 niveles', pt: 'Ganhe 3 estrelas em $1 níveis' }],
    [/^(\d+) étoiles sur 3$/, { en: '$1 stars out of 3', es: '$1 estrellas de 3', pt: '$1 estrelas de 3' }],
    [/^(.+) · recharge…$/, { en: '$1 · reloading…', es: '$1 · recargando…', pt: '$1 · recarregando…' }],
    [/^(\d\d:\d\d) · pluie$/, { en: '$1 · rain', es: '$1 · lluvia', pt: '$1 · chuva' }],
    [/^(.+)\. L'argent gagné pendant la tentative est conservé \((.+)\)\.$/, { en: '$1. The money earned during this attempt is kept ($2).', es: '$1. Conservas el dinero ganado en este intento ($2).', pt: '$1. O dinheiro ganho nesta tentativa fica com você ($2).' }],
    [/^Qualité : (.+)$/, { en: 'Quality: $1', es: 'Calidad: $1', pt: 'Qualidade: $1' }],
    [/^Auto \((.+)\)$/, { en: 'Auto ($1)', es: 'Auto ($1)', pt: 'Auto ($1)' }],
    [/^Doubler le bonus \(vidéo\) · \+(.+)$/, { en: 'Double the bonus (video) · +$1', es: 'Duplica el bonus (vídeo) · +$1', pt: 'Dobre o bônus (vídeo) · +$1' }],
    [/^Achat non abouti : (.+)$/, { en: 'Purchase failed: $1', es: 'Compra no completada: $1', pt: 'Compra não concluída: $1' }],
  ];
  const OUI = { oui: { en: 'on', es: 'sí', pt: 'sim' }, non: { en: 'off', es: 'no', pt: 'não' } };
  // contractions : es « de el » -> « del », pt « em o » -> « no », etc.
  function fix(x) {
    if (lang === 'es') return x.replace(/\bde el\b/g, 'del').replace(/\ba el\b/g, 'al').replace(/\bDe el\b/g, 'Del');
    if (lang === 'pt') return x.replace(/\bem o\b/g, 'no').replace(/\bem a\b/g, 'na').replace(/\bem os\b/g, 'nos').replace(/\bem as\b/g, 'nas').replace(/\bde o\b/g, 'do').replace(/\bde a\b/g, 'da').replace(/\bde os\b/g, 'dos').replace(/\bde as\b/g, 'das').replace(/\baté o\b/g, 'até o');
    return x;
  }
  function t(s) {
    if (lang === 'fr' || s == null) return s;
    s = String(s);
    const key = s.replace(/\s+/g, ' ').trim();
    if (!key) return s;
    if (OUI[key]) return OUI[key][lang];
    const d = dict()[key];
    if (d && d[lang]) return s.replace(s.trim(), d[lang]);
    for (const [re, tp] of P) {
      const m = key.match(re);
      if (m) { let out = tp[lang]; for (let i = m.length - 1; i >= 1; i--) out = out.split('$' + i).join(t(m[i])); return s.replace(s.trim(), fix(out)); }
    }
    return s;
  }
  function dom(root) {
    if (lang === 'fr' || !root) return;
    const w = document.createTreeWalker(root, NodeFilter.SHOW_TEXT, null);
    const nodes = []; while (w.nextNode()) nodes.push(w.currentNode);
    for (const n of nodes) { const v = n.nodeValue; if (/[A-Za-zÀ-ÿ]/.test(v)) { const r = t(v); if (r !== v) n.nodeValue = r; } }
    root.querySelectorAll('[placeholder],[aria-label],[title]').forEach(el => { for (const a of ['placeholder', 'aria-label', 'title']) { const v = el.getAttribute(a); if (v && /[A-Za-zÀ-ÿ]{2}/.test(v)) el.setAttribute(a, t(v)); } });
  }
  return { t, dom, LANGS, NAMES, get lang() { return lang; }, set(l) { if (LANGS.includes(l)) lang = l; document.documentElement.lang = lang; } };
})();
