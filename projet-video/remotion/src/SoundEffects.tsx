import { Audio, Sequence, staticFile, useVideoConfig } from 'remotion';
import { soundEffects } from './sfx';
import type { VideoProps } from './types';

export const SoundEffects: React.FC<{ props: VideoProps }> = ({ props }) => {
  const { fps } = useVideoConfig();
  return (
    <>
      {soundEffects(props).map((e, i) => (
        <Sequence key={i} from={Math.round(e.at * fps)} layout="none">
          <Audio src={staticFile(e.sound)} volume={e.volume ?? 0.35} />
        </Sequence>
      ))}
    </>
  );
};
