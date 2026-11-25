// Format JSON produit par la skill /yt-edit et consommé par la composition.

export type Layout = 'split' | 'facecam' | 'graphic';

export type Visual =
  | { type: 'headline'; text: string; label?: string }
  | { type: 'bigNumber'; value: number; label?: string; suffix?: string }
  | { type: 'terminal'; title?: string; label?: string; lines: string[] }
  | { type: 'iconGrid'; label?: string; items: string[]; highlight?: number }
  | { type: 'bars'; label?: string; labels: string[]; values: number[] }
  | { type: 'ranking'; label?: string; rows: { text: string; value: string }[] }
  | { type: 'checklist'; label?: string; items: { text: string; ok: boolean }[] }
  | { type: 'score'; label?: string; title: string; score: number; notes: string[] };

export type Scene = {
  /** Début / fin en secondes. */
  from: number;
  to: number;
  layout: Layout;
  visual?: Visual;
};

export type Caption = {
  from: number;
  to: number;
  /** Les mots entre *astérisques* sont surlignés en rouge. */
  text: string;
};

export type SoundEffect = {
  /** Instant en secondes. */
  at: number;
  /** Fichier dans public/ (ex: "sfx/whoosh.mp3"). */
  sound: string;
  volume?: number;
};

export type VideoProps = {
  title: string;
  theme: 'light' | 'dark';
  /** Fichier dans public/ (ex: "facecam.mp4"). Absent = emplacement factice. */
  facecam?: string;
  scenes: Scene[];
  captions: Caption[];
  /**
   * Effets sonores. "auto" (défaut) : placés d'après les scènes (voir src/sfx.ts) ;
   * "off" : aucun ; liste : uniquement ces sons. sfxExtra s'ajoute dans tous les cas.
   */
  sfx?: 'auto' | 'off' | SoundEffect[];
  sfxExtra?: SoundEffect[];
};
