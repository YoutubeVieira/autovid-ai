import { AbsoluteFill, OffthreadVideo, staticFile } from 'remotion';
import { FONT, type Theme } from './theme';

// Rendue une seule fois pour toute la vidéo : la prise facecam est continue,
// seule la zone visible change d'une scène à l'autre.
export const Facecam: React.FC<{ src?: string; theme: Theme }> = ({ src, theme }) => {
  if (src) {
    return (
      <OffthreadVideo
        src={staticFile(src)}
        style={{ width: '100%', height: '100%', objectFit: 'cover' }}
      />
    );
  }
  return (
    <AbsoluteFill
      style={{
        background: 'linear-gradient(180deg, #CFC6B8 0%, #8C8273 100%)',
        alignItems: 'center',
        justifyContent: 'center',
        color: theme.ink,
        fontFamily: FONT,
        fontSize: 34,
        letterSpacing: 6,
        opacity: 0.8,
      }}
    >
      FACECAM
    </AbsoluteFill>
  );
};
