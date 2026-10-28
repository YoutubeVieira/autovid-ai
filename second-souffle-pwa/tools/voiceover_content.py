# -*- coding: utf-8 -*-
"""Contenu des voix off : séances, bien-être, motivation, exercices non V1."""

def T(fr, en, pt):
    return {"fr": fr, "en": en, "pt": pt}

SESSION = [
 ("s.intro.short", "Début court", T("C'est parti. Installez-vous, et respirez un grand coup.", "Let's go. Get settled, and take a deep breath.", "Vamos lá. Acomode-se e respire fundo.")),
 ("s.intro.standard", "Début standard", T("Bonjour, et bravo d'être là. Avancez à votre rythme, et arrêtez si quelque chose vous fait mal.", "Hello, and well done for showing up. Go at your own pace, and stop if anything hurts.", "Olá, e parabéns por estar aqui. Vá no seu ritmo e pare se algo doer.")),
 ("s.intro.adapted", "Début, séance adaptée", T("J'ai adapté la séance à vos zones sensibles. Certains mouvements ont été remplacés.", "I adapted the session to your sensitive areas. Some movements were swapped.", "Adaptei a sessão às suas áreas sensíveis. Alguns movimentos foram trocados.")),
 ("s.next", "Exercice suivant", T("Prochain exercice.", "Next exercise.", "Próximo exercício.")),
 ("s.three", "Décompte de départ", T("Trois, deux, un, c'est parti.", "Three, two, one, go.", "Três, dois, um, vai.")),
 ("s.switch", "Changement de côté", T("Changez de côté.", "Switch sides.", "Troque de lado.")),
 ("s.half", "Moitié de séance", T("Vous êtes à la moitié. Continuez, vous le faites très bien.", "You're halfway there. Keep going, you're doing great.", "Você está na metade. Continue, você está indo muito bem.")),
 ("s.ten", "Dix secondes restantes", T("Plus que dix secondes.", "Ten seconds left.", "Faltam dez segundos.")),
 ("s.five", "Décompte final", T("Cinq, quatre, trois, deux, un.", "Five, four, three, two, one.", "Cinco, quatro, três, dois, um.")),
 ("s.rest", "Récupération entre deux exercices", T("Prenez dix secondes pour souffler.", "Take ten seconds to catch your breath.", "Tome dez segundos para respirar.")),
 ("s.breath", "Rappel de respiration", T("Respirez. Expirez en faisant l'effort.", "Breathe. Breathe out on the effort.", "Respire. Solte o ar no esforço.")),
 ("s.posture", "Rappel de posture", T("Gardez le dos long et les épaules basses.", "Keep your back long and your shoulders down.", "Mantenha as costas alongadas e os ombros baixos.")),
 ("s.pain", "Douleur pendant un mouvement", T("Si vous ressentez une douleur vive, arrêtez ce mouvement. Dites-le au coach, ou voyez un médecin si elle persiste.", "If you feel sharp pain, stop this movement. Tell the coach, or see a doctor if it lasts.", "Se sentir uma dor aguda, pare este movimento. Avise o coach ou procure um médico se persistir.")),
 ("s.pause", "Séance en pause", T("Séance en pause. Reprenez quand vous voulez.", "Session paused. Resume whenever you're ready.", "Sessão pausada. Retome quando quiser.")),
 ("s.resume", "Reprise", T("On reprend.", "Back at it.", "Vamos retomar.")),
 ("s.cooldown", "Retour au calme", T("Place au retour au calme. Ralentissez, et laissez le souffle redescendre.", "Time to cool down. Slow down and let your breathing settle.", "Hora de desacelerar. Vá mais devagar e deixe a respiração se acalmar.")),
 ("s.end", "Fin de séance", T("Séance terminée. Bravo. Buvez un peu d'eau et prenez un instant pour vous.", "Session complete. Well done. Have some water and take a moment for yourself.", "Sessão concluída. Parabéns. Beba um pouco de água e reserve um momento para você.")),
 ("s.stop", "Arrêt de la séance", T("Vous arrêtez la séance ? Aucun souci. Ce que vous avez fait compte.", "Stopping the session? No problem. What you did counts.", "Vai encerrar a sessão? Sem problema. O que você fez conta.")),
]

EXTRA_EX = {
 "cercles": T("Faites tourner doucement les poignets, puis les chevilles, dans un sens puis dans l'autre. Petits cercles réguliers.", "Gently rotate your wrists, then your ankles, one way and then the other. Small, steady circles.", "Gire suavemente os punhos e depois os tornozelos, para um lado e para o outro. Círculos pequenos e regulares."),
 "balancement": T("Debout, laissez vos bras se balancer d'avant en arrière, comme un pendule. Détendez les épaules et respirez.", "Standing, let your arms swing forward and back like a pendulum. Relax your shoulders and breathe.", "Em pé, deixe os braços balançarem para a frente e para trás, como um pêndulo. Relaxe os ombros e respire."),
 "fente": T("Une main sur la chaise. Reculez un pied, fléchissez doucement les deux genoux, puis revenez. Petit mouvement, sans forcer.", "One hand on the chair. Step one foot back, bend both knees gently, then come back. Small movement, no forcing.", "Uma mão na cadeira. Leve um pé para trás, dobre os dois joelhos com suavidade e volte. Movimento pequeno, sem forçar."),
 "pointes": T("Une main sur la chaise. Montez sur la pointe des pieds, tenez une seconde, puis redescendez lentement.", "One hand on the chair. Rise onto your toes, hold one second, then lower slowly.", "Uma mão na cadeira. Suba na ponta dos pés, segure um segundo e desça devagar."),
 "talon-pointe": T("Marchez en plaçant le talon d'un pied juste devant la pointe de l'autre, comme sur une ligne. Regard devant, un doigt sur le mur si besoin.", "Walk by placing the heel of one foot right in front of the toes of the other, as if on a line. Eyes ahead, fingertips on the wall if you need.", "Caminhe colocando o calcanhar de um pé logo à frente da ponta do outro, como em uma linha. Olhe para a frente e apoie os dedos na parede se precisar."),
 "elevations": T("Bras le long du corps. Levez-les sur les côtés jusqu'à hauteur d'épaules, puis redescendez lentement. Pas plus haut.", "Arms at your sides. Raise them out to shoulder height, then lower slowly. No higher.", "Braços ao lado do corpo. Levante-os para os lados até a altura dos ombros e desça devagar. Sem passar disso."),
 "flexion-bras": T("Coudes près du corps. Pliez les bras pour amener les mains vers les épaules, puis redescendez lentement. Poignets droits.", "Elbows close to your body. Bend your arms to bring your hands toward your shoulders, then lower slowly. Keep your wrists straight.", "Cotovelos junto ao corpo. Dobre os braços levando as mãos aos ombros e desça devagar. Punhos retos."),
 "rot-tronc": T("Assis, dos droit, bras croisés. Tournez doucement le haut du corps d'un côté, puis de l'autre. Les hanches restent de face.", "Sit tall with your arms crossed. Gently turn your upper body to one side, then the other. Your hips stay facing forward.", "Sentado, com as costas retas e os braços cruzados. Gire suavemente o tronco para um lado e depois para o outro. O quadril fica de frente."),
 "pectoraux": T("Dans l'encadrement d'une porte, avant-bras posés sur les montants. Avancez un peu le torse jusqu'à sentir l'étirement devant les épaules. Tenez, sans forcer.", "In a doorway, forearms resting on the frame. Lean forward until you feel a stretch across the front of your shoulders. Hold, no forcing.", "Na porta, com os antebraços apoiados nos batentes. Incline o tronco até sentir o alongamento na frente dos ombros. Segure, sem forçar."),
}

def seg(fr, en, pt, pause):
    return {"t": T(fr, en, pt), "pause": pause}

WELLNESS = [
 ("w.respiration", "Respiration apaisante", "environ 2 minutes", [
  seg("Installez-vous confortablement, assis ou allongé. Fermez les yeux si vous le souhaitez.", "Settle in comfortably, sitting or lying down. Close your eyes if you like.", "Acomode-se bem, sentado ou deitado. Feche os olhos, se quiser.", 4),
  seg("Posez une main sur le ventre. Nous allons respirer lentement.", "Rest one hand on your belly. We're going to breathe slowly.", "Apoie uma mão na barriga. Vamos respirar devagar.", 3),
  seg("Inspirez par le nez, doucement, en comptant jusqu'à quatre. Un, deux, trois, quatre.", "Breathe in through your nose, gently, counting to four. One, two, three, four.", "Inspire pelo nariz, com suavidade, contando até quatro. Um, dois, três, quatro.", 1),
  seg("Expirez lentement par la bouche, en comptant jusqu'à six. Un, deux, trois, quatre, cinq, six.", "Breathe out slowly through your mouth, counting to six. One, two, three, four, five, six.", "Solte o ar devagar pela boca, contando até seis. Um, dois, três, quatro, cinco, seis.", 3),
  seg("Recommencez à votre rythme. Le ventre se gonfle, puis se vide.", "Continue at your own pace. Your belly fills, then empties.", "Continue no seu ritmo. A barriga enche e depois esvazia.", 20),
  seg("Si vous sentez un vertige, reprenez une respiration normale.", "If you feel dizzy, go back to normal breathing.", "Se sentir tontura, volte a respirar normalmente.", 2),
  seg("Laissez les épaules tomber. La mâchoire se détend.", "Let your shoulders drop. Your jaw softens.", "Deixe os ombros caírem. A mandíbula relaxa.", 15),
  seg("Encore trois respirations. Inspirez… et expirez.", "Three more breaths. Breathe in… and breathe out.", "Mais três respirações. Inspire… e solte o ar.", 12),
  seg("Doucement, reprenez une respiration naturelle. Bougez les doigts et les orteils. Quand vous êtes prêt, ouvrez les yeux.", "Gently return to natural breathing. Wiggle your fingers and toes. When you're ready, open your eyes.", "Aos poucos, volte à respiração natural. Mexa os dedos das mãos e dos pés. Quando estiver pronto, abra os olhos.", 0),
 ]),
 ("w.soir", "Relaxation du soir", "environ 2 minutes", [
  seg("Allongez-vous confortablement. Laissez le lit ou le tapis vous porter.", "Lie down comfortably. Let the bed or the mat hold you.", "Deite-se confortavelmente. Deixe a cama ou o tapete sustentar você.", 4),
  seg("Prenez une grande inspiration, et soufflez longuement.", "Take a big breath in, and let it out for a long time.", "Respire fundo e solte o ar longamente.", 5),
  seg("Portez votre attention sur vos pieds. Laissez-les devenir lourds et chauds.", "Bring your attention to your feet. Let them become heavy and warm.", "Leve a atenção aos pés. Deixe-os ficarem pesados e quentes.", 8),
  seg("Remontez vers les jambes, les genoux. Relâchez, sans rien faire.", "Move up to your legs and knees. Let go, without doing anything.", "Suba para as pernas e os joelhos. Solte, sem fazer nada.", 8),
  seg("Les hanches, le bas du dos. Laissez le poids s'enfoncer dans le sol.", "Your hips, your lower back. Let the weight sink into the floor.", "O quadril, a lombar. Deixe o peso afundar no chão.", 8),
  seg("Le ventre monte et descend au rythme de votre souffle.", "Your belly rises and falls with your breath.", "A barriga sobe e desce no ritmo da sua respiração.", 10),
  seg("Les épaules, les bras, jusqu'au bout des doigts. Tout se détend.", "Your shoulders, your arms, all the way to your fingertips. Everything softens.", "Os ombros, os braços, até a ponta dos dedos. Tudo relaxa.", 8),
  seg("Le cou, la mâchoire, le front. Laissez le visage devenir doux.", "Your neck, your jaw, your forehead. Let your face go soft.", "O pescoço, a mandíbula, a testa. Deixe o rosto ficar macio.", 10),
  seg("Restez ici quelques respirations. Si des pensées arrivent, laissez-les passer.", "Stay here for a few breaths. If thoughts come, let them pass.", "Fique aqui por algumas respirações. Se pensamentos surgirem, deixe-os passar.", 20),
  seg("Quand vous le souhaitez, bougez doucement les doigts et les pieds. Vous pouvez rester allongé ou vous endormir.", "Whenever you like, gently move your fingers and feet. You can stay lying down, or drift off to sleep.", "Quando quiser, mexa devagar os dedos das mãos e dos pés. Você pode continuar deitado ou adormecer.", 0),
 ]),
 ("w.reveil", "Réveil en douceur", "environ 1 min 30", [
  seg("Bonjour. Avant de vous lever, restez allongé un instant et prenez trois grandes respirations.", "Good morning. Before you get up, stay lying down for a moment and take three deep breaths.", "Bom dia. Antes de levantar, fique deitado um instante e respire fundo três vezes.", 10),
  seg("Étirez les bras au-dessus de la tête et les jambes vers le bas, comme pour vous allonger. Tenez, puis relâchez.", "Stretch your arms overhead and your legs downward, as if lengthening yourself. Hold, then release.", "Estique os braços acima da cabeça e as pernas para baixo, como se quisesse se alongar. Segure e depois solte.", 6),
  seg("Ramenez les genoux vers la poitrine, doucement, et faites quelques petits balancements.", "Bring your knees toward your chest, gently, and rock a little from side to side.", "Leve os joelhos em direção ao peito, com suavidade, e balance um pouco de um lado para o outro.", 8),
  seg("Asseyez-vous au bord du lit, pieds au sol. Faites rouler les épaules vers l'arrière, trois fois.", "Sit on the edge of the bed, feet on the floor. Roll your shoulders backward, three times.", "Sente-se na beira da cama, com os pés no chão. Gire os ombros para trás, três vezes.", 8),
  seg("Tournez doucement la tête à droite, puis à gauche, sans forcer.", "Gently turn your head to the right, then to the left, without forcing.", "Gire a cabeça devagar para a direita e depois para a esquerda, sem forçar.", 8),
  seg("Levez-vous lentement, en vous appuyant si besoin. Vous êtes prêt pour la journée.", "Stand up slowly, using support if you need it. You're ready for the day.", "Levante-se devagar, apoiando-se se precisar. Você está pronto para o dia.", 0),
 ]),
 ("w.bureau", "Pause bureau", "environ 1 min 30", [
  seg("Pause. Asseyez-vous au bord de la chaise, les pieds à plat.", "Break time. Sit at the edge of your chair, feet flat.", "Hora da pausa. Sente-se na beira da cadeira, com os pés apoiados no chão.", 3),
  seg("Faites rouler vos épaules vers l'arrière, dix fois, lentement.", "Roll your shoulders backward, ten times, slowly.", "Gire os ombros para trás, dez vezes, devagar.", 8),
  seg("Penchez doucement l'oreille vers l'épaule droite. Tenez dix secondes. Puis à gauche.", "Gently tilt your ear toward your right shoulder. Hold ten seconds. Then the left.", "Incline suavemente a orelha em direção ao ombro direito. Segure dez segundos. Depois, o esquerdo.", 12),
  seg("Étirez un bras devant vous, paume vers le haut, et tirez doucement les doigts vers le bas. Changez de côté.", "Stretch one arm in front of you, palm up, and gently pull your fingers downward. Switch sides.", "Estique um braço à frente, com a palma para cima, e puxe os dedos suavemente para baixo. Troque de lado.", 12),
  seg("Joignez les mains derrière le dos et ouvrez la poitrine. Respirez.", "Clasp your hands behind your back and open your chest. Breathe.", "Una as mãos atrás das costas e abra o peito. Respire.", 10),
  seg("Levez-vous, marchez trente secondes, et buvez un verre d'eau.", "Stand up, walk for thirty seconds, and drink a glass of water.", "Levante-se, caminhe por trinta segundos e beba um copo de água.", 0),
 ]),
]

MOTIV = [
 ("Accueil", [
  ("o.welcome", T("Bienvenue dans Second Souffle. Je suis Léo, votre guide virtuel. Je vous pose trois questions, et votre première séance est prête.", "Welcome to Second Wind. I'm Léo, your virtual guide. Three questions, and your first session is ready.", "Bem-vindo ao Segundo Fôlego. Eu sou o Léo, seu guia virtual. Três perguntas e sua primeira sessão está pronta.")),
  ("o.zones", T("Touchez les zones qui vous tirent. Je les éviterai dans vos séances.", "Tap the areas that pull. I'll steer your sessions around them.", "Toque nas áreas que incomodam. Vou evitá-las nas suas sessões.")),
  ("o.ready", T("Votre séance est prête. Elle est adaptée à vous.", "Your session is ready. It's tailored to you.", "Sua sessão está pronta. Ela foi adaptada a você.")),
 ]),
 ("Message du matin", [
  ("m.1", T("Bonjour. Aujourd'hui, pas besoin d'être parfait. Dix minutes suffisent.", "Good morning. Today you don't have to be perfect. Ten minutes is enough.", "Bom dia. Hoje você não precisa ser perfeito. Dez minutos bastam.")),
  ("m.2", T("Votre corps vous remercie à chaque mouvement. On y va doucement ?", "Your body thanks you with every movement. Shall we start gently?", "Seu corpo agradece a cada movimento. Vamos começar com calma?")),
  ("m.3", T("Le plus dur, c'est de commencer. Vous êtes déjà là.", "The hardest part is starting. You're already here.", "O mais difícil é começar. Você já está aqui.")),
  ("m.4", T("Une petite séance vaut mieux qu'aucune. Faisons-en une ensemble.", "A short session beats none. Let's do one together.", "Uma sessão curta vale mais do que nenhuma. Vamos fazer uma juntos.")),
  ("m.5", T("La lumière monte. Prenez votre temps, et commençons.", "The light is rising. Take your time, and let's begin.", "A luz está subindo. Tome seu tempo e vamos começar.")),
  ("m.6", T("Chaque séance est une victoire, même petite.", "Every session is a win, even a small one.", "Cada sessão é uma vitória, mesmo pequena.")),
  ("m.7", T("Écoutez votre corps aujourd'hui. Je m'occupe du reste.", "Listen to your body today. I'll take care of the rest.", "Escute seu corpo hoje. Eu cuido do resto.")),
 ]),
 ("Repos choisi", [
  ("r.1", T("Un jour de repos choisi, c'est un jour de progrès. Votre corps récupère.", "A chosen rest day is a day of progress. Your body is recovering.", "Um dia de descanso escolhido é um dia de progresso. Seu corpo está se recuperando.")),
  ("r.2", T("Pas la forme aujourd'hui ? C'est normal. Reposez-vous, on se retrouve demain.", "Not feeling it today? That's normal. Rest up, see you tomorrow.", "Sem energia hoje? É normal. Descanse, nos vemos amanhã.")),
  ("r.3", T("Votre semaine reste lumineuse. Le repos fait partie du programme.", "Your week stays bright. Rest is part of the plan.", "Sua semana continua luminosa. O descanso faz parte do programa.")),
  ("r.4", T("Si vous voulez bouger un peu, une marche lente de cinq minutes suffit.", "If you'd like to move a little, a slow five-minute walk is enough.", "Se quiser se mexer um pouco, uma caminhada lenta de cinco minutos basta.")),
 ]),
 ("Encouragement pendant l'effort", [
  ("e.1", T("Très bien. Continuez à votre rythme.", "Very good. Keep going at your own pace.", "Muito bem. Continue no seu ritmo.")),
  ("e.2", T("Respirez, vous êtes en train de le faire.", "Breathe, you're doing it.", "Respire, você está conseguindo.")),
  ("e.3", T("Beau mouvement. Gardez cette précision.", "Nice movement. Keep that control.", "Belo movimento. Mantenha esse controle.")),
  ("e.4", T("Encore quelques secondes. Vous pouvez le faire.", "A few more seconds. You can do this.", "Mais alguns segundos. Você consegue.")),
  ("e.5", T("C'est la qualité qui compte, pas la vitesse.", "Quality matters, not speed.", "O que importa é a qualidade, não a velocidade.")),
  ("e.6", T("Si c'est trop, faites plus petit. Votre corps décide.", "If it's too much, make it smaller. Your body decides.", "Se estiver demais, faça menor. Seu corpo decide.")),
 ]),
 ("Après la séance", [
  ("p.hard", T("Merci de me le dire. Demain, on baisse d'un cran.", "Thanks for telling me. Tomorrow, we'll dial it down a notch.", "Obrigado por me dizer. Amanhã, vamos aliviar um pouco.")),
  ("p.ok", T("Parfait. On garde ce rythme et on ajoute un mouvement nouveau demain.", "Perfect. We keep this pace and add one new movement tomorrow.", "Perfeito. Mantemos esse ritmo e adicionamos um movimento novo amanhã.")),
  ("p.easy", T("Super. Demain, on monte d'un cran, doucement.", "Great. Tomorrow we step it up a notch, gently.", "Ótimo. Amanhã subimos um pouco o nível, com calma.")),
  ("p.bravo", T("Bravo. Vous venez de faire quelque chose de bon pour vous.", "Well done. You just did something good for yourself.", "Parabéns. Você acabou de fazer algo bom por si mesmo.")),
  ("p.sun", T("Le soleil monte un peu plus haut aujourd'hui.", "The sun is a little higher today.", "O sol está um pouco mais alto hoje.")),
 ]),
 ("Reprise après une pause", [
  ("c.1", T("Content de vous revoir. Une pause ne fait rien perdre : on reprend en douceur.", "Good to see you again. A break doesn't undo your progress: we restart gently.", "Que bom ver você de volta. Uma pausa não apaga o que você conquistou: vamos retomar com calma.")),
  ("c.2", T("Pas de culpabilité. Aujourd'hui, une séance courte et facile.", "No guilt. Today, a short, easy session.", "Sem culpa. Hoje, uma sessão curta e fácil.")),
  ("c.3", T("Reprendre, c'est déjà gagner. Allons-y.", "Starting again is already a win. Let's go.", "Recomeçar já é vencer. Vamos.")),
 ]),
 ("Bilan de la semaine", [
  ("b.good", T("Belle semaine. Votre lumière grandit, jour après jour.", "A good week. Your light grows, day after day.", "Que boa semana. Sua luz cresce, dia após dia.")),
  ("b.calm", T("Cette semaine a été plus calme, et c'est très bien. On repart ensemble.", "This week was quieter, and that's fine. We start again together.", "Esta semana foi mais tranquila, e tudo bem. Recomeçamos juntos.")),
 ]),
 ("Sécurité", [
  ("f.health", T("Votre santé passe avant tout. En cas de douleur forte, de vertige ou de gêne dans la poitrine, arrêtez et appelez un médecin ou les urgences.", "Your health comes first. If you feel severe pain, dizziness or chest discomfort, stop and call a doctor or emergency services.", "Sua saúde vem em primeiro lugar. Em caso de dor forte, tontura ou desconforto no peito, pare e chame um médico ou o serviço de emergência.")),
  ("f.virtual", T("Je suis un guide virtuel, pas un médecin. Pour toute question de santé, parlez à un professionnel.", "I'm a virtual guide, not a doctor. For any health question, talk to a professional.", "Sou um guia virtual, não um médico. Para qualquer dúvida de saúde, fale com um profissional.")),
 ]),
]
