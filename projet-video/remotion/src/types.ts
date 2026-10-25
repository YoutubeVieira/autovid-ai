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

export type VideoProps = {
  title: string;
  theme: 'light' | 'dark';
  /** Fichier dans public/ (ex: "facecam.mp4"). Absent = emplacement factice. */
  facecam?: string;
  scenes: Scene[];
  captions: Caption[];
};
