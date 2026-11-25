import { AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig } from 'remotion';
import { FONT, MONO, RED, type Theme } from '../theme';
import type { Visual } from '../types';

type P<T extends Visual['type']> = { v: Extract<Visual, { type: T }>; theme: Theme };

const useIn = (delay = 0) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  return spring({ frame: frame - delay, fps, config: { damping: 16, mass: 0.6 } });
};

// Petit libellé gris en capitales au-dessus de chaque visuel ("ELA TE AJUDA A DECIDIR").
const Label: React.FC<{ text?: string; theme: Theme }> = ({ text, theme }) =>
  text ? (
    <div
      style={{
        fontFamily: MONO,
        fontSize: 22,
        letterSpacing: 6,
        textTransform: 'uppercase',
        color: theme.muted,
        marginBottom: 28,
        textAlign: 'center',
      }}
    >
      {text}
    </div>
  ) : null;

const Frame: React.FC<{ label?: string; theme: Theme; children: React.ReactNode }> = ({ label, theme, children }) => (
  <AbsoluteFill style={{ alignItems: 'center', justifyContent: 'center', padding: '0 70px' }}>
    <Label text={label} theme={theme} />
    {children}
  </AbsoluteFill>
);

// Mot rouge si entouré d'astérisques, comme dans les sous-titres.
const Rich: React.FC<{ text: string }> = ({ text }) => (
  <>
    {text.split(/(\*[^*]+\*)/).map((part, i) =>
      part.startsWith('*') ? (
        <span key={i} style={{ color: RED }}>
          {part.slice(1, -1)}
        </span>
      ) : (
        <span key={i}>{part}</span>
      ),
    )}
  </>
);

const Headline: React.FC<P<'headline'>> = ({ v, theme }) => {
  const s = useIn();
  return (
    <Frame label={v.label} theme={theme}>
      <div
        style={{
          fontFamily: FONT,
          fontWeight: 900,
          fontSize: 120,
          lineHeight: 1,
          textAlign: 'center',
          textTransform: 'uppercase',
          color: theme.ink,
          transform: `scale(${interpolate(s, [0, 1], [0.6, 1])})`,
          opacity: s,
        }}
      >
        <Rich text={v.text} />
      </div>
    </Frame>
  );
};

const BigNumber: React.FC<P<'bigNumber'>> = ({ v, theme }) => {
  const s = useIn();
  const n = Math.round(interpolate(s, [0, 1], [0, v.value]));
  return (
    <Frame label={v.label} theme={theme}>
      <div style={{ fontFamily: FONT, fontWeight: 900, fontSize: 360, lineHeight: 1, color: RED }}>
        {n}
        {v.suffix ?? ''}
      </div>
    </Frame>
  );
};

const Window: React.FC<{ title?: string; theme: Theme; children: React.ReactNode }> = ({ title, theme, children }) => (
  <div
    style={{
      width: '100%',
      backgroundColor: theme.term,
      borderRadius: 18,
      boxShadow: '0 20px 60px rgba(0,0,0,0.35)',
      overflow: 'hidden',
    }}
  >
    <div style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '16px 20px' }}>
      {['#FF5F57', '#FEBC2E', '#28C840'].map((c) => (
        <div key={c} style={{ width: 16, height: 16, borderRadius: 8, backgroundColor: c }} />
      ))}
      <div style={{ flex: 1, textAlign: 'center', fontFamily: MONO, fontSize: 20, color: '#8A8A8A' }}>
        {title ?? 'Claude Code'}
      </div>
    </div>
    <div style={{ padding: '10px 34px 34px' }}>{children}</div>
  </div>
);

const Terminal: React.FC<P<'terminal'>> = ({ v, theme }) => {
  const frame = useCurrentFrame();
  const s = useIn();
  // Une ligne toutes les 6 images, la dernière avec curseur clignotant.
  const visible = Math.min(v.lines.length, Math.floor(frame / 6) + 1);
  return (
    <Frame label={v.label} theme={theme}>
      <div style={{ width: '100%', transform: `translateY(${interpolate(s, [0, 1], [60, 0])}px)`, opacity: s }}>
        <Window title={v.title} theme={theme}>
          {v.lines.slice(0, visible).map((line, i) => (
            <div
              key={i}
              style={{
                fontFamily: MONO,
                fontSize: 30,
                lineHeight: 1.6,
                color: line.startsWith('>') || line.startsWith('$') ? '#9A9A9A' : line.startsWith('!') ? RED : '#EDEDED',
                whiteSpace: 'pre',
              }}
            >
              {line.startsWith('!') ? line.slice(1) : line}
              {i === visible - 1 && frame % 30 < 15 ? '▌' : ''}
            </div>
          ))}
        </Window>
      </div>
    </Frame>
  );
};

const IconGrid: React.FC<P<'iconGrid'>> = ({ v, theme }) => {
  const frame = useCurrentFrame();
  const cols = v.items.length > 6 ? 4 : 3;
  return (
    <Frame label={v.label} theme={theme}>
      <div style={{ display: 'grid', gridTemplateColumns: `repeat(${cols}, 1fr)`, gap: 30, width: '100%' }}>
        {v.items.map((item, i) => {
          const s = spring({ frame: frame - i * 3, fps: 30, config: { damping: 14 } });
          const hot = v.highlight === i;
          return (
            <div
              key={item}
              style={{
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                gap: 12,
                transform: `scale(${s})`,
                opacity: v.highlight === undefined || hot ? 1 : 0.35,
              }}
            >
              <div
                style={{
                  width: 110,
                  height: 72,
                  borderRadius: 12,
                  backgroundColor: hot ? RED : '#D98576',
                  boxShadow: hot ? `0 0 0 6px ${RED}33` : undefined,
                }}
              />
              <div style={{ fontFamily: MONO, fontSize: 22, color: theme.muted }}>{item}</div>
            </div>
          );
        })}
      </div>
    </Frame>
  );
};

const Bars: React.FC<P<'bars'>> = ({ v, theme }) => {
  const s = useIn();
  const max = Math.max(...v.values, 1);
  return (
    <Frame label={v.label} theme={theme}>
      <div style={{ display: 'flex', alignItems: 'flex-end', gap: 22, height: 520, width: '100%' }}>
        {v.values.map((val, i) => (
          <div key={i} style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 12 }}>
            <div style={{ width: '100%', height: 480, backgroundColor: theme.card, borderRadius: 10, position: 'relative' }}>
              <div
                style={{
                  position: 'absolute',
                  bottom: 0,
                  width: '100%',
                  height: `${(val / max) * 100 * s}%`,
                  backgroundColor: val === max ? theme.ink : theme.muted,
                  borderRadius: 10,
                }}
              />
            </div>
            <div style={{ fontFamily: MONO, fontSize: 20, color: theme.muted }}>{v.labels[i]}</div>
          </div>
        ))}
      </div>
    </Frame>
  );
};

const Ranking: React.FC<P<'ranking'>> = ({ v, theme }) => {
  const frame = useCurrentFrame();
  return (
    <Frame label={v.label} theme={theme}>
      <div style={{ width: '100%', backgroundColor: theme.card, borderRadius: 16, padding: 30 }}>
        {v.rows.map((row, i) => {
          const s = spring({ frame: frame - i * 4, fps: 30, config: { damping: 16 } });
          return (
            <div
              key={i}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 24,
                padding: '16px 0',
                opacity: s,
                transform: `translateX(${interpolate(s, [0, 1], [40, 0])}px)`,
              }}
            >
              <div style={{ width: 80, height: 48, borderRadius: 6, backgroundColor: theme.ink }} />
              <div style={{ flex: 1, fontFamily: FONT, fontSize: 30, color: theme.ink }}>{row.text}</div>
              <div style={{ fontFamily: FONT, fontWeight: 800, fontSize: 32, color: theme.ink }}>{row.value}</div>
            </div>
          );
        })}
      </div>
    </Frame>
  );
};

const Checklist: React.FC<P<'checklist'>> = ({ v, theme }) => {
  const frame = useCurrentFrame();
  return (
    <Frame label={v.label} theme={theme}>
      <Window theme={theme}>
        {v.items.map((item, i) =>
          frame >= i * 8 ? (
            <div key={i} style={{ display: 'flex', gap: 20, fontFamily: MONO, fontSize: 30, lineHeight: 1.7 }}>
              <span style={{ color: item.ok ? '#28C840' : RED }}>{item.ok ? 'ok' : '✕'}</span>
              <span style={{ color: '#EDEDED' }}>{item.text}</span>
            </div>
          ) : null,
        )}
      </Window>
    </Frame>
  );
};

const Score: React.FC<P<'score'>> = ({ v, theme }) => {
  const s = useIn(4);
  return (
    <Frame label={v.label} theme={theme}>
      <Window theme={theme}>
        <div style={{ fontFamily: MONO, fontSize: 30, color: '#EDEDED', marginBottom: 20 }}>"{v.title}"</div>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end' }}>
          <div style={{ fontFamily: MONO, fontSize: 22, color: '#8A8A8A' }}>{v.title.length} caracteres</div>
          <div style={{ fontFamily: FONT, fontWeight: 900, fontSize: 96, color: '#FFFFFF' }}>
            {Math.round(v.score * s)}/100
          </div>
        </div>
        {v.notes.map((n) => (
          <div key={n} style={{ fontFamily: MONO, fontSize: 24, color: RED, marginTop: 10 }}>
            ✕ {n}
          </div>
        ))}
      </Window>
    </Frame>
  );
};

export const VisualView: React.FC<{ visual: Visual; theme: Theme }> = ({ visual, theme }) => {
  switch (visual.type) {
    case 'headline':
      return <Headline v={visual} theme={theme} />;
    case 'bigNumber':
      return <BigNumber v={visual} theme={theme} />;
    case 'terminal':
      return <Terminal v={visual} theme={theme} />;
    case 'iconGrid':
      return <IconGrid v={visual} theme={theme} />;
    case 'bars':
      return <Bars v={visual} theme={theme} />;
    case 'ranking':
      return <Ranking v={visual} theme={theme} />;
    case 'checklist':
      return <Checklist v={visual} theme={theme} />;
    case 'score':
      return <Score v={visual} theme={theme} />;
  }
};
