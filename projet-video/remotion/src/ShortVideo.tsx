import { AbsoluteFill, Sequence, useCurrentFrame, useVideoConfig } from 'remotion';
import { Captions } from './Captions';
import { Facecam } from './Facecam';
import { graphicHeight, sceneAt } from './layout';
import { H, themes } from './theme';
import type { VideoProps } from './types';
import { VisualView } from './visuals';

export const ShortVideo: React.FC<VideoProps> = (props) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const theme = themes[props.theme];
  const current = sceneAt(props.scenes, frame / fps);
  const top = current ? graphicHeight(current.layout) : 0;

  return (
    <AbsoluteFill style={{ backgroundColor: theme.bg }}>
      {/* Une seule facecam montée en continu (audio sans coupure) ; seule sa zone change. */}
      <div style={{ position: 'absolute', left: 0, right: 0, top: Math.min(top, H - 1), bottom: 0 }}>
        <Facecam src={props.facecam} theme={theme} />
      </div>

      {props.scenes.map((scene, i) =>
        scene.visual && scene.layout !== 'facecam' ? (
          <Sequence
            key={i}
            from={Math.round(scene.from * fps)}
            durationInFrames={Math.max(1, Math.round((scene.to - scene.from) * fps))}
          >
            <div
              style={{
                position: 'absolute',
                top: 0,
                left: 0,
                right: 0,
                height: graphicHeight(scene.layout),
                backgroundColor: theme.bg,
              }}
            >
              <VisualView visual={scene.visual} theme={theme} />
            </div>
          </Sequence>
        ) : null,
      )}

      <Captions captions={props.captions} scenes={props.scenes} />
    </AbsoluteFill>
  );
};
