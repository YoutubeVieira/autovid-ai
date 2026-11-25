import type { Scene, SoundEffect, VideoProps } from './types';

// Placement automatique : on connaît l'instant exact où chaque visuel apparaît,
// pas besoin « d'écouter » ni de regarder la vidéo pour savoir où mettre un son.
const LINE_EVERY = 6 / 30; // une ligne de terminal toutes les 6 images (visuals/Terminal)

const forScene = (scene: Scene, prev?: Scene): SoundEffect[] => {
  const v = scene.visual;
  if (!v || scene.layout === 'facecam') return [];
  const out: SoundEffect[] = [];
  const changed = !prev?.visual || prev.layout !== scene.layout || prev.visual.type !== v.type;
  if (v.type === 'bigNumber') {
    // Gros chiffre : un impact suffit, pas de whoosh par-dessus.
    out.push({ at: scene.from + 0.05, sound: 'sfx/impact.mp3', volume: 0.5 });
  } else {
    out.push({ at: scene.from, sound: 'sfx/whoosh.mp3', volume: changed ? 0.35 : 0.2 });
  }
  if (v.type === 'checklist' || v.type === 'ranking' || v.type === 'iconGrid') {
    out.push({ at: scene.from + 0.25, sound: 'sfx/pop.mp3', volume: 0.3 });
  }
  if (v.type === 'terminal') {
    // Un clic par ligne affichée, 4 maximum : au-delà, ça devient un tic-tac.
    v.lines.slice(0, 4).forEach((_, i) =>
      out.push({ at: scene.from + i * LINE_EVERY, sound: 'sfx/click.mp3', volume: 0.15 }),
    );
  }
  return out.filter((e) => e.at < scene.to);
};

export const soundEffects = (props: VideoProps): SoundEffect[] => {
  const base =
    props.sfx === 'off'
      ? []
      : Array.isArray(props.sfx)
        ? props.sfx
        : props.scenes.flatMap((s, i) => forScene(s, props.scenes[i - 1]));
  return [...base, ...(props.sfxExtra ?? [])].sort((a, b) => a.at - b.at);
};
