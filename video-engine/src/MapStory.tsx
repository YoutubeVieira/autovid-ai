import React from "react";
import { AbsoluteFill, Audio, Sequence, interpolate, spring, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import { FREE_ZONE, H, W, cameraTransform, features, polygonPath, project, toScreen } from "./geo";
import { FLAGS, Flag } from "./flags";
import basemap from "../public/geo/basemap.json";
import type { Camera, FillKey, Item, LonLat, Scene, StoryProps } from "./types";

export const EMOJI = "'Noto Color Emoji'";
export const FONT = `Inter, ${EMOJI}, 'DejaVu Sans', sans-serif`;
const TINT: Record<string, string> = { gray: "#b9b6ab", red: "#b3322d", yellow: "#dcb52a" };
const FADE = 14; // images de fondu quand un pays change de remplissage
const clamp = (v: number, a = 0, b = 1) => Math.min(b, Math.max(a, v));
const hash = (n: number) => { const x = Math.sin(n * 127.1 + 311.7) * 43758.5453; return x - Math.floor(x); };

/* ---------- état cumulé : remplissages et caméra ---------- */
function fillsAt(scenes: Scene[], i: number): Record<string, FillKey> {
  const out: Record<string, FillKey> = {};
  for (let k = 0; k <= i; k++) Object.assign(out, scenes[k].fills || {});
  return out;
}

/* Caméra : ressort avec rebond entre la scène précédente et la scène courante (zoom en progression géométrique),
   dérive lente, coup de zoom et secousse à chaque impact. */
function cameraAt(scenes: Scene[], i: number, f: number, fps: number): { cam: Camera; shake: [number, number] } {
  const sc = scenes[i], cur = sc.camera;
  const mv = sc.move ?? (i === 0 ? "zoomin" : "pan");
  let prev: Camera = i > 0 ? scenes[i - 1].camera : { ...cur, zoom: cur.zoom * 0.72 };
  if (mv === "zoomin") prev = { ...cur, zoom: cur.zoom * 0.7 };
  if (mv === "zoomout") prev = { ...cur, zoom: cur.zoom * 1.4 };
  if (mv === "cut") prev = cur;
  const p = spring({ frame: f, fps, config: { damping: 11, stiffness: 95, mass: 0.8 } });
  const drift = 1 + 0.06 * (f / Math.max(1, sc.durationInFrames));
  let kick = 1, sx = 0, sy = 0;
  for (const t0 of sc.impacts || []) {
    const dt = f / fps - t0;
    if (dt < 0 || dt > 1.2) continue;
    const a = Math.exp(-dt * 5.5);
    kick *= 1 + 0.06 * Math.exp(-dt * 8);
    sx += 34 * a * Math.sin(dt * 61 + t0); sy += 28 * a * Math.cos(dt * 49 + 2 * t0);
  }
  return {
    cam: {
      lon: prev.lon + (cur.lon - prev.lon) * clamp(p, -0.3, 1.3),
      lat: prev.lat + (cur.lat - prev.lat) * clamp(p, -0.3, 1.3),
      zoom: prev.zoom * Math.pow(cur.zoom / prev.zoom, p) * drift * kick
    },
    shake: [sx, sy]
  };
}

/* ---------- carte satellite + pays ---------- */
const FillLayer: React.FC<{ f: (typeof features)[number]; k: FillKey; opacity: number }> = ({ f, k, opacity }) => {
  if (k === "land" || opacity <= 0) return null;
  if (k === "flag") {
    if (!FLAGS[f.id.toLowerCase()]) return null;
    return (
      <g opacity={opacity * 0.9}>
        <path d={f.d} fill={`url(#flag-${f.id})`} />
        <path d={f.d} fill="#000" opacity="0.14" />
      </g>
    );
  }
  if (k === "split") {
    return (
      <g opacity={opacity * 0.9}>
        <path d={f.d} fill={TINT.red} />
        <path d={f.d} fill={TINT.yellow} clipPath="url(#free-zone)" />
      </g>
    );
  }
  return <path d={f.d} fill={TINT[k]} opacity={opacity * 0.88} />;
};

export const MapLayer: React.FC<{ scenes: Scene[]; i: number; f: number; cam: Camera; blur: number; w?: number; h?: number }> = ({ scenes, i, f, cam, blur, w = W, h = H }) => {
  const cur = fillsAt(scenes, i), prev = i > 0 ? fillsAt(scenes, i - 1) : {};
  const a = interpolate(f, [0, FADE], [0, 1], { extrapolateRight: "clamp" });
  return (
    <svg width={w} height={h} style={{ position: "absolute", inset: 0, filter: blur > 0.6 ? `blur(${blur.toFixed(1)}px)` : undefined }}>
      <defs>
        {features.filter(x => FLAGS[x.id.toLowerCase()]).map(x => (
          <pattern key={x.id} id={`flag-${x.id}`} patternUnits="userSpaceOnUse" x={x.flagBox[0]} y={x.flagBox[1]} width={x.flagBox[2]} height={x.flagBox[3]}>
            <Flag id={x.id.toLowerCase()} width={x.flagBox[2]} height={x.flagBox[3]} />
          </pattern>
        ))}
        <clipPath id="free-zone"><path d={polygonPath(FREE_ZONE)} /></clipPath>
        <filter id="glow" x="-10%" y="-10%" width="120%" height="120%"><feGaussianBlur stdDeviation="5" /></filter>
      </defs>
      <g transform={cameraTransform(cam, w, h)}>
        <image href={staticFile("geo/basemap.jpg")} x={basemap.x} y={basemap.y} width={basemap.width} height={basemap.height} />
        {features.map(x => {
          const c = cur[x.id] || "land", p = prev[x.id] || "land";
          return (
            <g key={x.id}>
              {c !== p && <FillLayer f={x} k={p} opacity={1} />}
              <FillLayer f={x} k={c} opacity={c !== p ? a : 1} />
            </g>
          );
        })}
        {/* halo lumineux des pays en jeu */}
        {features.filter(x => (cur[x.id] || "land") !== "land").map(x => (
          <path key={"g" + x.id} d={x.d} fill="none" stroke="#fff" strokeOpacity="0.55" strokeWidth="5" vectorEffect="non-scaling-stroke" filter="url(#glow)" />
        ))}
        {features.map(x => <path key={x.id} d={x.d} fill="none" stroke="#fff" strokeOpacity={(cur[x.id] || "land") !== "land" ? 0.95 : 0.6} strokeWidth="1.7" vectorEffect="non-scaling-stroke" strokeLinejoin="round" />)}
      </g>
    </svg>
  );
};

/* ---------- éléments : hexagones, médaillons, bulles ---------- */
const hex = (r: number) => Array.from({ length: 6 }, (_, k) => { const a = Math.PI / 3 * k - Math.PI / 6; return `${(r * Math.cos(a)).toFixed(1)},${(r * Math.sin(a)).toFixed(1)}`; }).join(" ");
const GLOW = "drop-shadow(0 0 14px #ffffffaa) drop-shadow(0 8px 10px #000a)";

export const Hex: React.FC<{ r?: number; children?: React.ReactNode; fill?: string }> = ({ r = 90, children, fill = "#f4f4f0" }) => (
  <svg width={r * 2.2} height={r * 2.2} viewBox={`${-r * 1.1} ${-r * 1.1} ${r * 2.2} ${r * 2.2}`} style={{ overflow: "visible", filter: GLOW }}>
    <polygon points={hex(r)} fill="#9aa4a6" />
    <polygon points={hex(r * 0.9)} fill={fill} />
    {children}
  </svg>
);

const Person: React.FC<{ label: string; img?: string; ring?: string }> = ({ label, img, ring }) => (
  <div style={{ width: 210, display: "flex", flexDirection: "column", alignItems: "center", filter: "drop-shadow(0 8px 12px #000a)" }}>
    <div style={{ width: 170, height: 170, borderRadius: 85, overflow: "hidden", background: "#2a2d30", border: `7px solid ${ring || "#f0efe8"}` }}>
      {img ? <img src={staticFile(img)} style={{ width: "100%", height: "100%", objectFit: "cover", filter: "grayscale(1) contrast(1.1)" }} /> : (
        <svg viewBox="0 0 100 100" width="100%" height="100%"><rect width="100" height="100" fill="#3a3f43" /><circle cx="50" cy="38" r="17" fill="#8d959a" /><path d="M14,100 C16,70 84,70 86,100Z" fill="#8d959a" /></svg>
      )}
    </div>
    <div style={{ marginTop: -16, background: "#0c0c0c", color: "#e9e6dc", fontFamily: "'DejaVu Serif', serif", fontWeight: 700, fontSize: 27, padding: "4px 16px", borderRadius: 4, letterSpacing: 1 }}>{label}</div>
  </div>
);

const Bubble: React.FC<{ text?: string; emoji?: string; tail?: "left" | "right" }> = ({ text, emoji, tail = "left" }) => (
  <div style={{ position: "relative", background: "#fff", borderRadius: 30, padding: emoji ? "12px 30px" : "18px 32px", maxWidth: 380, boxShadow: "0 8px 18px #0008", textAlign: "center", fontFamily: FONT, fontWeight: 900, fontSize: 40, lineHeight: 1.08, color: "#161616" }}>
    {emoji ? <span style={{ fontFamily: EMOJI, fontSize: 96, filter: "drop-shadow(0 4px 4px #0004)" }}>{emoji}</span> : text}
    <div style={{ position: "absolute", bottom: -22, [tail]: 36, width: 0, height: 0, borderLeft: "18px solid transparent", borderRight: "18px solid transparent", borderTop: "26px solid #fff" } as React.CSSProperties} />
  </div>
);

/* Apparition « punchy » : ressort à fort rebond, bascule, léger flottement, sortie rapide. */
const Pop: React.FC<{ delay: number; end: number; children: React.ReactNode; style: React.CSSProperties; rot?: number }> = ({ delay, end, children, style, rot = 0 }) => {
  const f = useCurrentFrame(), { fps } = useVideoConfig();
  const s = spring({ frame: f - delay, fps, config: { damping: 7, stiffness: 210, mass: 0.55 } });
  const out = interpolate(f, [end - 7, end], [1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const k = Math.max(0, f - delay);
  const sc = Math.max(0, s) * out * (1 + 0.03 * Math.sin(k / 5));
  if (f < delay || sc <= 0.001) return null;
  return <div style={{ position: "absolute", transform: `translate(-50%, -50%) translateY(${4 * Math.sin(k / 9)}px) scale(${sc}) rotate(${(1 - s) * rot}deg)`, ...style }}>{children}</div>;
};

const Ring: React.FC<{ delay: number; at: [number, number]; color?: string; size?: number }> = ({ delay, at, color = "#fff", size = 150 }) => {
  const f = useCurrentFrame();
  const t = (f - delay) / 14;
  if (t < 0 || t > 1) return null;
  const r = size * (0.4 + 1.3 * (1 - Math.pow(1 - t, 3)));
  return <div style={{ position: "absolute", left: at[0] - r, top: at[1] - r, width: r * 2, height: r * 2, borderRadius: "50%", border: `${10 * (1 - t) + 2}px solid ${color}`, opacity: 1 - t }} />;
};

const Burst: React.FC<{ at: [number, number]; delay: number; emoji: string }> = ({ at, delay, emoji }) => {
  const f = useCurrentFrame(), { fps } = useVideoConfig();
  const k = f - delay;
  if (k < 0 || k > 70) return null;
  const s = spring({ frame: k, fps, config: { damping: 6, stiffness: 260, mass: 0.6 } });
  const fadeOut = interpolate(k, [38, 60], [1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const t = clamp(k / 16);
  const sparks = Array.from({ length: 16 }, (_, n) => { const a = n * (Math.PI * 2 / 16) + hash(n) * 0.4, r0 = 60 + 220 * (1 - Math.pow(1 - t, 3)), len = 70 * (1 - t) + 10; return { x1: Math.cos(a) * r0, y1: Math.sin(a) * r0, x2: Math.cos(a) * (r0 + len), y2: Math.sin(a) * (r0 + len), c: n % 2 ? "#ffd60a" : "#ff7a1a" }; });
  return (
    <div style={{ position: "absolute", left: at[0], top: at[1], opacity: fadeOut }}>
      <svg width={700} height={700} viewBox="-350 -350 700 700" style={{ position: "absolute", left: -350, top: -350, overflow: "visible" }}>
        <circle r={40 + 260 * (1 - Math.pow(1 - t, 3))} fill="none" stroke="#fff" strokeWidth={16 * (1 - t) + 1} opacity={1 - t} />
        {sparks.map((p, n) => <line key={n} {...p} stroke={p.c} strokeWidth="9" strokeLinecap="round" opacity={1 - t * 0.6} />)}
      </svg>
      <div style={{ position: "absolute", transform: `translate(-50%, -50%) scale(${Math.max(0, s) * 1.15}) rotate(${(1 - s) * -25}deg)`, fontFamily: EMOJI, fontSize: 250, lineHeight: 1, filter: "drop-shadow(0 0 30px #ff8a00cc)" }}>{emoji}</div>
    </div>
  );
};

const Ping: React.FC<{ at: [number, number]; delay: number; color: string }> = ({ at, delay, color }) => {
  const f = useCurrentFrame();
  return (
    <>
      {[0, 14, 28].map(o => {
        const t = (((f - delay - o) % 42) + 42) % 42 / 42;
        if (f - delay - o < 0) return null;
        const r = 20 + 120 * t;
        return <div key={o} style={{ position: "absolute", left: at[0] - r, top: at[1] - r, width: r * 2, height: r * 2, borderRadius: "50%", border: `6px solid ${color}`, opacity: 1 - t }} />;
      })}
      <div style={{ position: "absolute", left: at[0] - 11, top: at[1] - 11, width: 22, height: 22, borderRadius: 11, background: color, boxShadow: `0 0 18px ${color}` }} />
    </>
  );
};

export const Arrow: React.FC<{ from: [number, number]; to: [number, number]; delay: number; color: string }> = ({ from, to, delay, color }) => {
  const f = useCurrentFrame(), { fps } = useVideoConfig();
  const p = clamp((f - delay) / (fps * 0.9));
  if (f < delay) return null;
  const e = 1 - Math.pow(1 - p, 3);
  const mx = (from[0] + to[0]) / 2, my = (from[1] + to[1]) / 2, dx = to[0] - from[0], dy = to[1] - from[1];
  const c: [number, number] = [mx - dy * 0.22, my + dx * 0.22];
  const q = (t: number): [number, number] => [(1 - t) ** 2 * from[0] + 2 * (1 - t) * t * c[0] + t * t * to[0], (1 - t) ** 2 * from[1] + 2 * (1 - t) * t * c[1] + t * t * to[1]];
  const head = q(e), ahead = q(Math.min(1, e + 0.02)), ang = Math.atan2(ahead[1] - head[1], ahead[0] - head[0]) * 180 / Math.PI;
  return (
    <svg width={W} height={H} style={{ position: "absolute", inset: 0, overflow: "visible", filter: `drop-shadow(0 0 14px ${color})` }}>
      <path d={`M${from[0]},${from[1]} Q${c[0]},${c[1]} ${to[0]},${to[1]}`} pathLength={1} fill="none" stroke={color} strokeWidth="22" strokeLinecap="round" strokeDasharray={`${e} 1`} />
      <polygon points="0,-34 62,0 0,34" fill={color} transform={`translate(${head[0]} ${head[1]}) rotate(${ang})`} />
    </svg>
  );
};

/* Gros chiffre qui défile (finance) : carte sombre, nombre en police grasse, intitulé dessous. */
export const Stat: React.FC<{ it: Extract<Item, { kind: "stat" }>; delay: number }> = ({ it, delay }) => {
  const f = useCurrentFrame(), { fps } = useVideoConfig();
  const p = 1 - Math.pow(1 - clamp((f - delay - 4) / (fps * 1.2)), 3);
  const v = (it.from ?? 0) + (it.value - (it.from ?? 0)) * p;
  const txt = (it.prefix || "") + v.toLocaleString("fr-FR", { minimumFractionDigits: it.decimals ?? 0, maximumFractionDigits: it.decimals ?? 0 }) + (it.suffix || "");
  const c = it.color || "#ffd60a";
  return (
    <div style={{ background: "#0b0f12ee", border: `6px solid ${c}`, borderRadius: 28, padding: "22px 44px 26px", textAlign: "center", boxShadow: `0 0 40px ${c}66, 0 10px 24px #000b`, minWidth: 560 }}>
      <div style={{ fontFamily: FONT, fontWeight: 900, fontSize: 118, color: c, lineHeight: 1, fontVariantNumeric: "tabular-nums", whiteSpace: "nowrap", WebkitTextStroke: "3px #000", paintOrder: "stroke fill" }}>{txt}</div>
      <div style={{ fontFamily: FONT, fontWeight: 800, fontSize: 38, color: "#f2f2ec", marginTop: 10, letterSpacing: 1, textTransform: "uppercase" }}>{it.label}</div>
    </div>
  );
};

const ItemView: React.FC<{ it: Item; cam: Camera; dur: number; n: number }> = ({ it, cam, dur, n }) => {
  const { fps } = useVideoConfig();
  const delay = Math.round((it.delay ?? 0.2) * fps), end = it.until ? Math.round(it.until * fps) : dur;
  const base = it.screen ? it.screen : it.at ? toScreen(it.at, cam) : [W / 2, H / 2];
  const left = base[0] + (it.dx || 0), top = base[1] + (it.dy || 0);
  const pos = { left, top } as React.CSSProperties;
  const rot = (hash(n + 3) > 0.5 ? 1 : -1) * (14 + 12 * hash(n));
  const ring = <Ring delay={delay} at={[left, top]} />;
  switch (it.kind) {
    case "icon": return <>{ring}<Pop delay={delay} end={end} rot={rot} style={pos}><Hex r={104}><text textAnchor="middle" dominantBaseline="central" fontSize="108" y="4" fontFamily={EMOJI}>{it.emoji}</text></Hex></Pop></>;
    case "flagBadge": return (
      <>{ring}
        <Pop delay={delay} end={end} rot={rot} style={pos}>
          <Hex r={104}>
            <clipPath id={"fb-" + n}><polygon points={hex(104 * 0.82)} /></clipPath>
            <g clipPath={`url(#fb-${n})`}><Flag id={it.flag} x={-104} y={-104} width={208} height={208} /></g>
            {it.emoji && <text textAnchor="middle" dominantBaseline="central" fontSize="100" y="6" fontFamily={EMOJI} style={{ filter: "drop-shadow(0 4px 4px #0008)" }}>{it.emoji}</text>}
          </Hex>
        </Pop>
      </>
    );
    case "person": return <>{ring}<Pop delay={delay} end={end} rot={rot * 0.5} style={pos}><Person label={it.label} img={it.img} ring={it.ring} /></Pop></>;
    case "bubble": return <Pop delay={delay} end={end} rot={rot * 0.6} style={{ ...pos, transformOrigin: "50% 100%" }}><Bubble text={it.text} emoji={it.emoji} tail={it.tail} /></Pop>;
    case "tag": return <Pop delay={delay} end={end} rot={rot * 0.3} style={pos}><div style={{ fontFamily: FONT, fontWeight: 900, fontSize: 34, letterSpacing: 3, color: "#f0f0ea", background: "#6b7377dd", padding: "7px 22px", borderRadius: 7, boxShadow: "0 6px 12px #0007" }}>{it.text}</div></Pop>;
    case "title": return (
      <Pop delay={delay} end={end} style={{ left: W / 2, top: it.screen ? it.screen[1] : 200 }}>
        <div style={{ fontFamily: FONT, fontWeight: 900, fontSize: 64, color: "#fff", textAlign: "center", whiteSpace: "nowrap", WebkitTextStroke: "8px #000", paintOrder: "stroke fill", textShadow: "0 5px 0 #000" }}>{it.text}{it.sub && <div style={{ fontSize: 40, fontWeight: 800, opacity: 0.9 }}>{it.sub}</div>}</div>
      </Pop>
    );
    case "stat": return <Pop delay={delay} end={end} rot={rot * 0.3} style={it.at || it.screen ? pos : { left: W / 2, top: 640 }}><Stat it={it} delay={delay} /></Pop>;
    case "ping": return <Ping at={[left, top]} delay={delay} color={it.color || "#ffd60a"} />;
    case "burst": return <Burst at={[left, top]} delay={delay} emoji={it.emoji || "💥"} />;
    case "arrow": {
      const a = toScreen(it.from, cam), b = toScreen(it.to, cam);
      return <Arrow from={a} to={b} delay={delay} color={it.color || "#ff3b30"} />;
    }
  }
};

/* ---------- sous-titres : groupes de mots qui claquent à l'écran ---------- */
const Subtitles: React.FC<{ scene: Scene; f: number }> = ({ scene, f }) => {
  const { fps } = useVideoConfig();
  const t = f / fps;
  const idx = scene.subtitles.findIndex(s => t >= s.from && t < s.to);
  const cur = idx >= 0 ? scene.subtitles[idx] : (t >= (scene.subtitles.at(-1)?.to ?? 0) ? scene.subtitles.at(-1) : undefined);
  if (!cur) return null;
  const s = spring({ frame: Math.round((t - cur.from) * fps), fps, config: { damping: 8, stiffness: 320, mass: 0.5 } });
  const n = scene.subtitles.indexOf(cur);
  return (
    <div style={{ position: "absolute", left: 0, right: 0, top: H * 0.72, display: "flex", justifyContent: "center", padding: "0 50px" }}>
      <div style={{ fontFamily: FONT, fontWeight: 900, fontSize: 104, textTransform: "uppercase", textAlign: "center", color: "#ffd60a", WebkitTextStroke: "16px #000", paintOrder: "stroke fill", transform: `scale(${0.55 + 0.45 * s}) rotate(${(1 - s) * (n % 2 ? 4 : -4)}deg)`, lineHeight: 1.04, textShadow: "0 10px 0 #000", filter: "drop-shadow(0 8px 10px #000a)" }}>
        {cur.text}
      </div>
    </div>
  );
};

/* ---------- bruitages calés sur l'image ---------- */
type Ev = { name: string; frame: number; volume: number; rate?: number };
const DUR: Record<string, number> = { whoosh: 0.7, pop: 0.2, impact: 1.5, ding: 1.1, riser: 1.8 };
function soundEvents(scenes: Scene[], starts: number[], fps: number): Ev[] {
  const ev: Ev[] = [];
  scenes.forEach((s, i) => {
    const b = starts[i];
    if ((s.move ?? (i === 0 ? "zoomin" : "pan")) !== "cut") ev.push({ name: "whoosh", frame: b, volume: 0.5 });
    (s.items || []).forEach((it, n) => {
      const fr = b + Math.round((it.delay ?? 0.2) * fps);
      if (["icon", "person", "flagBadge", "bubble", "tag", "title"].includes(it.kind)) ev.push({ name: "pop", frame: fr, volume: 0.55, rate: 0.9 + 0.3 * hash(n + i * 7) });
      if (it.kind === "icon") ev.push({ name: "ding", frame: fr + 4, volume: 0.28 });
      if (it.kind === "stat") { ev.push({ name: "pop", frame: fr, volume: 0.6 }); ev.push({ name: "ding", frame: fr + Math.round(fps * 1.2), volume: 0.35 }); }
      if (it.kind === "burst") ev.push({ name: "impact", frame: fr, volume: 0.9 });
      if (it.kind === "arrow") ev.push({ name: "whoosh", frame: fr, volume: 0.55, rate: 1.25 });
    });
    (s.impacts || []).forEach(t => ev.push({ name: "impact", frame: b + Math.round(t * fps), volume: 0.8 }));
    (s.sfx || []).forEach(x => ev.push({ name: x.name, frame: b + Math.round(x.at * fps), volume: x.volume ?? 0.6 }));
  });
  return ev;
}

/* ---------- vidéo ---------- */
export const MapStory: React.FC<StoryProps> = ({ scenes, bg }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  let acc = 0, idx = 0;
  const starts = scenes.map(s => { const a = acc; acc += s.durationInFrames; return a; });
  for (let k = 0; k < scenes.length; k++) if (frame >= starts[k]) idx = k;
  const scene = scenes[idx], f = frame - starts[idx];
  const { cam, shake } = cameraAt(scenes, idx, f, fps);
  const prevCam = f > 0 ? cameraAt(scenes, idx, f - 1, fps).cam : cam;
  const [x1, y1] = project([cam.lon, cam.lat]), [x0, y0] = project([prevCam.lon, prevCam.lat]);
  const speed = Math.hypot((x1 - x0) * cam.zoom, (y1 - y0) * cam.zoom) + Math.abs(cam.zoom - prevCam.zoom) * 700;
  const blur = Math.min(14, speed * 0.22);
  const flashes = [...(scene.impacts || []), ...(scene.flash || [])].map(t => f / fps - t).filter(dt => dt >= 0 && dt < 0.4);
  const flash = flashes.length ? Math.max(...flashes.map(dt => 0.6 * Math.exp(-dt * 14))) : 0;
  const grainShift = [Math.floor(hash(frame) * 200), Math.floor(hash(frame + 99) * 200)];
  const events = soundEvents(scenes, starts, fps);
  return (
    <AbsoluteFill style={{ background: bg || "#0a1f29" }}>
      <AbsoluteFill style={{ transform: `translate(${shake[0]}px, ${shake[1]}px)` }}>
        <MapLayer scenes={scenes} i={idx} f={f} cam={cam} blur={blur} />
        <Sequence from={starts[idx]} durationInFrames={scene.durationInFrames} layout="none">
          {(scene.items || []).map((it, n) => <ItemView key={idx + "-" + n} it={it} cam={cam} dur={scene.durationInFrames} n={n + idx * 10} />)}
        </Sequence>
      </AbsoluteFill>
      <Subtitles scene={scene} f={f} />
      {/* grain de pellicule + vignette + flash */}
      <svg width={W + 200} height={H + 200} style={{ position: "absolute", left: -grainShift[0], top: -grainShift[1], opacity: 0.2, mixBlendMode: "overlay", pointerEvents: "none" }}>
        <filter id="grain"><feTurbulence type="fractalNoise" baseFrequency="0.85" numOctaves="2" seed="3" /><feColorMatrix values="0 0 0 0 1  0 0 0 0 1  0 0 0 0 1  0 0 0 1.6 -0.3" /></filter>
        <rect width={W + 200} height={H + 200} filter="url(#grain)" />
      </svg>
      <AbsoluteFill style={{ boxShadow: "inset 0 0 280px 60px #000c", pointerEvents: "none" }} />
      {flash > 0.01 && <AbsoluteFill style={{ background: "#fff", opacity: flash, pointerEvents: "none" }} />}
      {/* voix par scène, nappe sonore et bruitages */}
      {scenes.map((s, k) => s.audio ? <Sequence key={s.id} from={starts[k]} durationInFrames={s.durationInFrames}><Audio src={staticFile(s.audio)} /></Sequence> : null)}
      <Audio src={staticFile("sfx/bed.wav")} loop volume={0.17} />
      {events.map((e, n) => (
        <Sequence key={n} from={e.frame} durationInFrames={Math.ceil((DUR[e.name] ?? 1) * fps / (e.rate ?? 1)) + 2}>
          <Audio src={staticFile(`sfx/${e.name}.wav`)} volume={e.volume} playbackRate={e.rate ?? 1} />
        </Sequence>
      ))}
    </AbsoluteFill>
  );
};
