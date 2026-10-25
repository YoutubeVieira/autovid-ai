import { interpolate, spring, useCurrentFrame, useVideoConfig } from 'remotion';
import { graphicHeight, sceneAt } from './layout';
import { FONT, H, RED } from './theme';
import type { Caption, Scene } from './types';

type Word = { text: string; red: boolean };

// "O Claude acabou de *matar* o YouTube" -> mots, ceux entre astérisques en rouge.
export const parseWords = (text: string): Word[] => {
  const words: Word[] = [];
  let red = false;
  for (const raw of text.split(/\s+/).filter(Boolean)) {
    const opens = raw.startsWith('*');
    const closes = raw.endsWith('*') && (raw.length > 1 || !opens);
    if (opens) red = true;
    words.push({ text: raw.replace(/\*/g, ''), red });
    if (closes) red = false;
  }
  return words;
};

export const Captions: React.FC<{ captions: Caption[]; scenes: Scene[] }> = ({ captions, scenes }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = frame / fps;
  const caption = captions.find((c) => t >= c.from && t < c.to);
  if (!caption) return null;

  const words = parseWords(caption.text);
  // Les mots apparaissent un par un, répartis sur les 70 % premiers du segment.
  const span = (caption.to - caption.from) * 0.7;
  const shown = Math.max(1, Math.ceil(((t - caption.from) / span) * words.length));

  const scene = sceneAt(scenes, t);
  const g = scene ? graphicHeight(scene.layout) : 0;
  // Sur la ligne de coupe en split, au tiers bas sinon.
  const y = g > 0 && g < H ? g : H * 0.7;

  const pop = spring({ frame: frame - Math.round(caption.from * fps), fps, config: { damping: 14, mass: 0.5 } });

  return (
    <div
      style={{
        position: 'absolute',
        left: 0,
        right: 0,
        top: y,
        display: 'flex',
        justifyContent: 'center',
        transform: `translateY(-50%) scale(${interpolate(pop, [0, 1], [0.85, 1])})`,
      }}
    >
      <div
        style={{
          backgroundColor: '#1A1A1A',
          color: '#FFFFFF',
          fontFamily: FONT,
          fontWeight: 800,
          fontSize: 50,
          lineHeight: 1.15,
          padding: '10px 24px 14px',
          borderRadius: 14,
          maxWidth: 900,
          textAlign: 'center',
          boxShadow: '0 6px 24px rgba(0,0,0,0.25)',
        }}
      >
        {words.slice(0, shown).map((w, i) => (
          <span key={i} style={{ color: w.red ? RED : undefined }}>
            {i > 0 ? ' ' : ''}
            {w.text}
          </span>
        ))}
      </div>
    </div>
  );
};
