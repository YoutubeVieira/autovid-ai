import { H, SPLIT_Y } from './theme';
import type { Layout, Scene } from './types';

export const graphicHeight = (layout: Layout) =>
  layout === 'graphic' ? H : layout === 'split' ? SPLIT_Y : 0;

export const sceneAt = (scenes: Scene[], t: number): Scene | undefined =>
  scenes.find((s) => t >= s.from && t < s.to) ?? scenes[scenes.length - 1];
