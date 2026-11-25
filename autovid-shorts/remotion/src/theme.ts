export const W = 1080;
export const H = 1920;
// Hauteur de la zone graphique en mode "split" ; la facecam occupe le reste.
export const SPLIT_Y = 1000;

export const RED = '#E8392B';

export const themes = {
  light: { bg: '#EDEBE7', ink: '#1C1C1C', muted: '#9A968F', card: '#FFFFFF', term: '#1E1E1E' },
  dark: { bg: '#1C1C1C', ink: '#F4F2EE', muted: '#7A7770', card: '#2A2A2A', term: '#0F0F0F' },
} as const;

export type Theme = (typeof themes)[keyof typeof themes];

export const FONT = 'Inter, "Helvetica Neue", Arial, sans-serif';
export const MONO = '"JetBrains Mono", "SF Mono", Menlo, monospace';
