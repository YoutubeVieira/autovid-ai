// 20 testeurs, chacun avec une fonction précise. diff : 0 Facile, 1 Normal, 2 Difficile, 3 Légende.
// aimErr : imprécision du tir (radians), think : vitesse de réaction relative, carDist : distance à partir de laquelle il prend une voiture.
const base = { diff: 1, aimErr: .12, think: 1, range: 330, car: true, carDist: 700, drive: .8, run: true, heal: true, fightBack: true, shop: 'basic', strafe: false, tunnel: false, nitro: false, melee: false, wander: false, noCheckpoint: false, copsMax: 2 };
const P = (id, name, role, o) => Object.assign({}, base, { id, name, role }, o);
module.exports = [
  P(1, 'Débutant prudent', 'Mesure si un nouveau joueur finit le jeu en Facile', { diff: 0, aimErr: .26, drive: .55, run: false, think: .7 }),
  P(2, 'Joueur moyen', 'Référence : temps typique pour finir les 30 niveaux en Normal', {}),
  P(3, 'Expert', 'Temps plancher d’un très bon joueur', { aimErr: .05, drive: 1, strafe: true }),
  P(4, 'Speedrunner', 'Toujours en voiture, nitro, aucun détour : chemin le plus rapide', { aimErr: .06, drive: 1.1, carDist: 250, nitro: true, shop: 'weapons', copsMax: 3 }),
  P(5, 'Légende', 'Vérifie que la difficulté Légende reste faisable', { diff: 3, aimErr: .06, drive: 1, strafe: true, shop: 'max' }),
  P(6, 'Difficile', 'Équilibrage du mode Difficile', { diff: 2, aimErr: .09, drive: .9 }),
  P(7, 'Piéton pur', 'Ne prend une voiture que si l’étape l’exige : chronos des étapes à pied', { car: false, carDist: 99999 }),
  P(8, 'Gros acheteur', 'Dépense tout : armes, armures, soins. L’économie suit-elle ?', { shop: 'max' }),
  P(9, 'Radin', 'N’achète rien : le jeu se finit-il sans boutique ?', { shop: 'none' }),
  P(10, 'Entraîné', 'Achète l’entraînement en priorité : impact de la salle de sport', { shop: 'train' }),
  P(11, 'Tunnelier', 'Sème la police par les tunnels plutôt qu’en voiture', { tunnel: true }),
  P(12, 'Sans soins', 'N’utilise jamais de trousse : la régénération suffit-elle ?', { heal: false }),
  P(13, 'Sans armure', 'N’achète jamais d’armure', { shop: 'noarmor' }),
  P(14, 'Mauvais tireur', 'Vise mal : le jeu reste-t-il jouable pour un joueur maladroit ?', { aimErr: .38 }),
  P(15, 'Bagarreur', 'Poings uniquement : limite du corps à corps', { melee: true, shop: 'noarmor' }),
  P(16, 'Arme lourde', 'Achète la meilleure arme dès qu’il peut', { shop: 'weapons', aimErr: .1 }),
  P(17, 'Chasseur de contrats', 'N’achète aucune arme : les armes gratuites par défis suffisent-elles ?', { shop: 'contracts' }),
  P(18, 'Réflexes lents', 'Réagit 2,5 fois plus lentement (joueur sur petit téléphone)', { think: .4, aimErr: .2, drive: .6 }),
  P(19, 'Sans reprise', 'Recommence toujours depuis l’étape 1 : utilité du point de reprise', { noCheckpoint: true }),
  P(20, 'Explorateur', 'Fait des détours (30 % du temps hors GPS) : le chrono reste-t-il tenable ?', { wander: true, aimErr: .14 }),
];
