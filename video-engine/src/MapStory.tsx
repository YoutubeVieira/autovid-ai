import React from "react";
import { AbsoluteFill, Audio, Easing, Sequence, interpolate, spring, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import { FREE_ZONE, H, W, cameraTransform, features, polygonPath, toScreen } from "./geo";
import { FLAGS, Flag } from "./flags";
import type { Camera, FillKey, Item, Scene, StoryProps } from "./types";

const FONT = "Inter, 'DejaVu Sans', sans-serif";
const TINT: Record<string, string> = { gray: "#b9b6ab", red: "#b3322d", yellow: "#dcb52a" };
const FADE = 14; // images de fondu quand un pays change de remplissage
const CAM_MOVE = 26; // images de déplacement de caméra en début de scène

const ease = Easing.bezier(0.45, 0, 0.2, 1);

/* ---------- état cumulé : remplissages et caméra ---------- */
function fillsAt(scenes: Scene[], i: number): Record<string, FillKey> {
  const out: Record<string, FillKey> = {};
  for (let k = 0; k <= i; k++) Object.assign(out, scenes[k].fills || {});
  return out;
}

function cameraAt(scenes: Scene[], i: number, f: number): Camera {
  const cur = scenes[i].camera, prev = i > 0 ? scenes[i - 1].camera : cur;
  const t = ease(interpolate(f, [0, CAM_MOVE], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }));
  const drift = 1 + 0.05 * (f / Math.max(1, scenes[i].durationInFrames));
  return {
    lon: prev.lon + (cur.lon - prev.lon) * t,
    lat: prev.lat + (cur.lat - prev.lat) * t,
    zoom: (prev.zoom + (cur.zoom - prev.zoom) * t) * (i > 0 ? 1 : 1) * drift
  };
}

/* ---------- fond : océan ---------- */
const Ocean: React.FC<{ bg?: string }> = ({ bg }) => (
  <AbsoluteFill style={{ background: bg || "radial-gradient(ellipse at 50% 40%, #145466 0%, #0c3c4d 55%, #08242f 100%)" }}>
    <svg width={W} height={H} style={{ opacity: 0.22, mixBlendMode: "overlay" }}>
      <filter id="grain"><feTurbulence type="fractalNoise" baseFrequency="0.006 0.012" numOctaves="3" seed="7" /><feColorMatrix values="0 0 0 0 1  0 0 0 0 1  0 0 0 0 1  0 0 0 1.2 -0.2" /></filter>
      <rect width={W} height={H} filter="url(#grain)" />
    </svg>
  </AbsoluteFill>
);

/* ---------- carte ---------- */
const FillLayer: React.FC<{ f: (typeof features)[number]; k: FillKey; opacity: number }> = ({ f, k, opacity }) => {
  if (k === "land" || opacity <= 0) return null;
  if (k === "flag") {
    const id = f.id === "GBR" ? "gbr" : f.id === "FRA" ? "fra" : f.id === "DEU" ? "deu" : null;
    if (!id) return null;
    return (
      <g opacity={opacity}>
        <path d={f.d} fill={`url(#flag-${f.id})`} />
        <path d={f.d} fill="#000" opacity="0.16" />
      </g>
    );
  }
  if (k === "split") {
    return (
      <g opacity={opacity}>
        <path d={f.d} fill={TINT.red} />
        <path d={f.d} fill={TINT.yellow} clipPath="url(#free-zone)" />
      </g>
    );
  }
  return <path d={f.d} fill={TINT[k]} opacity={opacity * 0.94} />;
};

const MapLayer: React.FC<{ scenes: Scene[]; i: number; f: number }> = ({ scenes, i, f }) => {
  const cam = cameraAt(scenes, i, f);
  const cur = fillsAt(scenes, i), prev = i > 0 ? fillsAt(scenes, i - 1) : {};
  const a = interpolate(f, [0, FADE], [0, 1], { extrapolateRight: "clamp" });
  return (
    <svg width={W} height={H} style={{ position: "absolute", inset: 0 }}>
      <defs>
        {features.filter(x => FLAGS[x.id.toLowerCase()]).map(x => (
          <pattern key={x.id} id={`flag-${x.id}`} patternUnits="userSpaceOnUse" x={x.flagBox[0]} y={x.flagBox[1]} width={x.flagBox[2]} height={x.flagBox[3]}>
            <Flag id={x.id.toLowerCase()} width={x.flagBox[2]} height={x.flagBox[3]} />
          </pattern>
        ))}
        <clipPath id="free-zone"><path d={polygonPath(FREE_ZONE)} /></clipPath>
        <filter id="shadow"><feDropShadow dx="0" dy="0" stdDeviation="2.5" floodColor="#000" floodOpacity="0.55" /></filter>
      </defs>
      <g transform={cameraTransform(cam)}>
        <g filter="url(#shadow)">
          {features.map(x => <path key={x.id} d={x.d} fill="#374a3d" />)}
        </g>
        {features.map(x => {
          const c = cur[x.id] || "land", p = prev[x.id] || "land";
          return (
            <g key={x.id}>
              {c !== p && <FillLayer f={x} k={p} opacity={1} />}
              <FillLayer f={x} k={c} opacity={c !== p ? a : 1} />
            </g>
          );
        })}
        {/* liseré blanc des frontières, épaisseur constante à l'écran */}
        {features.map(x => <path key={x.id} d={x.d} fill="none" stroke="#fff" strokeOpacity="0.85" strokeWidth="1.6" vectorEffect="non-scaling-stroke" />)}
      </g>
    </svg>
  );
};

/* ---------- éléments : hexagones, médaillons, bulles ---------- */
const hex = (r: number) => Array.from({ length: 6 }, (_, k) => { const a = Math.PI / 3 * k - Math.PI / 6; return `${(r * Math.cos(a)).toFixed(1)},${(r * Math.sin(a)).toFixed(1)}`; }).join(" ");

const Hex: React.FC<{ r?: number; children?: React.ReactNode; fill?: string }> = ({ r = 90, children, fill = "#f4f4f0" }) => (
  <svg width={r * 2.2} height={r * 2.2} viewBox={`${-r * 1.1} ${-r * 1.1} ${r * 2.2} ${r * 2.2}`} style={{ overflow: "visible" }}>
    <polygon points={hex(r)} fill="#9aa4a6" />
    <polygon points={hex(r * 0.9)} fill={fill} />
    {children}
  </svg>
);

const Person: React.FC<{ label: string; img?: string; ring?: string }> = ({ label, img, ring }) => (
  <div style={{ width: 190, display: "flex", flexDirection: "column", alignItems: "center" }}>
    <div style={{ width: 150, height: 150, borderRadius: 75, overflow: "hidden", background: "#2a2d30", border: `6px solid ${ring || "#e9e9e4"}`, boxShadow: "0 6px 18px #0008" }}>
      {img ? <img src={staticFile(img)} style={{ width: "100%", height: "100%", objectFit: "cover", filter: "grayscale(1)" }} /> : (
        <svg viewBox="0 0 100 100" width="100%" height="100%"><rect width="100" height="100" fill="#3a3f43" /><circle cx="50" cy="38" r="17" fill="#8d959a" /><path d="M14,100 C16,70 84,70 86,100Z" fill="#8d959a" /></svg>
      )}
    </div>
    <div style={{ marginTop: -14, background: "#0c0c0c", color: "#e9e6dc", fontFamily: "'DejaVu Serif', serif", fontWeight: 700, fontSize: 24, padding: "4px 14px", borderRadius: 4, letterSpacing: 1 }}>{label}</div>
  </div>
);

const Bubble: React.FC<{ text?: string; emoji?: string; tail?: "left" | "right" }> = ({ text, emoji, tail = "left" }) => (
  <div style={{ position: "relative", background: "#fff", borderRadius: 26, padding: emoji ? "10px 26px" : "16px 28px", maxWidth: 340, boxShadow: "0 6px 16px #0007", textAlign: "center", fontFamily: FONT, fontWeight: 900, fontSize: 36, lineHeight: 1.1, color: "#161616" }}>
    {emoji ? <span style={{ fontSize: 76 }}>{emoji}</span> : text}
    <div style={{ position: "absolute", bottom: -20, [tail]: 34, width: 0, height: 0, borderLeft: "16px solid transparent", borderRight: "16px solid transparent", borderTop: "24px solid #fff" } as React.CSSProperties} />
  </div>
);

const Pop: React.FC<{ delay: number; end: number; children: React.ReactNode; style: React.CSSProperties }> = ({ delay, end, children, style }) => {
  const f = useCurrentFrame(), { fps } = useVideoConfig();
  const s = spring({ frame: f - delay, fps, config: { damping: 12, stiffness: 180, mass: 0.7 } });
  const out = interpolate(f, [end - 6, end], [1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const sc = Math.max(0, s) * out;
  if (f < delay || sc <= 0.001) return null;
  return <div style={{ position: "absolute", transform: `translate(-50%, -50%) scale(${sc})`, ...style }}>{children}</div>;
};

const ItemView: React.FC<{ it: Item; cam: Camera; dur: number }> = ({ it, cam, dur }) => {
  const { fps } = useVideoConfig();
  const delay = Math.round((it.delay ?? 0.2) * fps), end = it.until ? Math.round(it.until * fps) : dur;
  const base = it.screen ? it.screen : it.at ? toScreen(it.at, cam) : [W / 2, H / 2];
  const left = base[0] + (it.dx || 0), top = base[1] + (it.dy || 0);
  const pos = { left, top } as React.CSSProperties;
  switch (it.kind) {
    case "icon": return <Pop delay={delay} end={end} style={pos}><Hex r={92}><text textAnchor="middle" dominantBaseline="central" fontSize="92">{it.emoji}</text></Hex></Pop>;
    case "flagBadge": return (
      <Pop delay={delay} end={end} style={pos}>
        <Hex r={92}>
          <clipPath id={"fb-" + it.flag}><polygon points={hex(92 * 0.82)} /></clipPath>
          <g clipPath={`url(#fb-${it.flag})`}><Flag id={it.flag} x={-92} y={-92} width={184} height={184} /></g>
          {it.emoji && <text textAnchor="middle" dominantBaseline="central" fontSize="84" y="4">{it.emoji}</text>}
        </Hex>
      </Pop>
    );
    case "person": return <Pop delay={delay} end={end} style={pos}><Person label={it.label} img={it.img} ring={it.ring} /></Pop>;
    case "bubble": return <Pop delay={delay} end={end} style={{ ...pos, transformOrigin: "50% 100%" }}><Bubble text={it.text} emoji={it.emoji} tail={it.tail} /></Pop>;
    case "tag": return <Pop delay={delay} end={end} style={pos}><div style={{ fontFamily: FONT, fontWeight: 800, fontSize: 30, letterSpacing: 2, color: "#e4e4de", background: "#7c8386cc", padding: "6px 18px", borderRadius: 6 }}>{it.text}</div></Pop>;
    case "title": return (
      <Pop delay={delay} end={end} style={{ left: W / 2, top: it.screen ? it.screen[1] : 190 }}>
        <div style={{ fontFamily: FONT, fontWeight: 900, fontSize: 54, color: "#fff", textAlign: "center", whiteSpace: "nowrap", textShadow: "0 3px 10px #000a" }}>{it.text}{it.sub && <div style={{ fontSize: 36, fontWeight: 700, opacity: 0.85 }}>{it.sub}</div>}</div>
      </Pop>
    );
  }
};

/* ---------- sous-titres : groupes de mots, jaune à contour noir ---------- */
const Subtitles: React.FC<{ scene: Scene; f: number }> = ({ scene, f }) => {
  const { fps } = useVideoConfig();
  const t = f / fps;
  const cur = scene.subtitles.find(s => t >= s.from && t < s.to) || (t >= (scene.subtitles.at(-1)?.to ?? 0) ? scene.subtitles.at(-1) : undefined);
  if (!cur) return null;
  const k = interpolate(t - cur.from, [0, 0.12], [0.86, 1], { extrapolateRight: "clamp" });
  return (
    <div style={{ position: "absolute", left: 0, right: 0, top: H * 0.74, display: "flex", justifyContent: "center", padding: "0 60px" }}>
      <div style={{ fontFamily: FONT, fontWeight: 900, fontSize: 92, textTransform: "uppercase", textAlign: "center", color: "#ffd60a", WebkitTextStroke: "14px #000", paintOrder: "stroke fill", transform: `scale(${k})`, lineHeight: 1.05, textShadow: "0 8px 0 #000" }}>
        {cur.text}
      </div>
    </div>
  );
};

/* ---------- vidéo ---------- */
export const MapStory: React.FC<StoryProps> = ({ scenes, bg }) => {
  const frame = useCurrentFrame();
  let start = 0, idx = 0;
  const starts = scenes.map(s => { const a = start; start += s.durationInFrames; return a; });
  for (let k = 0; k < scenes.length; k++) if (frame >= starts[k]) idx = k;
  const scene = scenes[idx], f = frame - starts[idx];
  const cam = cameraAt(scenes, idx, f);
  return (
    <AbsoluteFill style={{ background: "#08242f" }}>
      <Ocean bg={bg} />
      <MapLayer scenes={scenes} i={idx} f={f} />
      <Sequence from={starts[idx]} durationInFrames={scene.durationInFrames} layout="none">
        {(scene.items || []).map((it, n) => <ItemView key={idx + "-" + n} it={it} cam={cam} dur={scene.durationInFrames} />)}
      </Sequence>
      <Subtitles scene={scene} f={f} />
      {scenes.map((s, k) => s.audio ? <Sequence key={s.id} from={starts[k]} durationInFrames={s.durationInFrames}><Audio src={staticFile(s.audio)} /></Sequence> : null)}
      <AbsoluteFill style={{ boxShadow: "inset 0 0 260px 40px #000b", pointerEvents: "none" }} />
    </AbsoluteFill>
  );
};
