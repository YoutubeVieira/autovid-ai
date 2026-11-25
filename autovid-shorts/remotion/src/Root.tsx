import { Composition } from 'remotion';
import { ShortVideo } from './ShortVideo';
import { H, W } from './theme';
import type { VideoProps } from './types';
import exemple from '../data/exemple-youtube-agent.json';

const FPS = 30;

export const RemotionRoot: React.FC = () => (
  <Composition
    id="AutoVidShort"
    component={ShortVideo}
    width={W}
    height={H}
    fps={FPS}
    durationInFrames={FPS * 10}
    defaultProps={exemple as VideoProps}
    calculateMetadata={({ props }) => {
      const end = Math.max(
        ...props.scenes.map((s) => s.to),
        ...props.captions.map((c) => c.to),
      );
      return { durationInFrames: Math.ceil(end * FPS) };
    }}
  />
);
