import React from "react";
import { interpolate, useCurrentFrame } from "remotion";
import type { CastMember, Pose, SetId, Stage as StageCfg, StageObj, Who } from "./types";

const EMOJI = "'Noto Color Emoji'";
const FONT = `Inter, ${EMOJI}, 'DejaVu Sans', sans-serif`;

/* ---------------- décors (1920 x 1080) ---------------- */
const Window: React.FC<{ x: number; y: number; w: number; h: number; night?: boolean }> = ({ x, y, w, h, night }) => (
  <g>
    <rect x={x - 12} y={y - 12} width={w + 24} height={h + 24} rx="8" fill="#f8f4ea" />
    <rect x={x} y={y} width={w} height={h} fill={night ? "#1d2b4a" : "url(#sky)"} />
    <circle cx={x + w * 0.75} cy={y + h * 0.3} r={w * 0.07} fill="#ffe27a" opacity="0.95" />
    <path d={`M${x},${y + h} L${x},${y + h * 0.75} Q${x + w * 0.3},${y + h * 0.6} ${x + w * 0.55},${y + h * 0.78} T${x + w},${y + h * 0.72} L${x + w},${y + h} Z`} fill="#7fb069" />
    <rect x={x + w / 2 - 5} y={y} width="10" height={h} fill="#f8f4ea" />
    <rect x={x} y={y + h / 2 - 5} width={w} height="10" fill="#f8f4ea" />
  </g>
);

const Defs: React.FC = () => (
  <defs>
    <linearGradient id="sky" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stopColor="#8fd3f4" /><stop offset="1" stopColor="#d9f1ff" /></linearGradient>
    <linearGradient id="wallWarm" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stopColor="#f7e7c6" /><stop offset="1" stopColor="#efd8ad" /></linearGradient>
    <linearGradient id="wallCool" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stopColor="#dbe7f3" /><stop offset="1" stopColor="#c7d8ea" /></linearGradient>
    <linearGradient id="shade" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stopColor="#000" stopOpacity="0" /><stop offset="1" stopColor="#000" stopOpacity="0.28" /></linearGradient>
    <radialGradient id="glow"><stop offset="0" stopColor="#fff6c9" stopOpacity="0.9" /><stop offset="1" stopColor="#fff6c9" stopOpacity="0" /></radialGradient>
  </defs>
);

const Cuisine: React.FC = () => (
  <g>
    <rect width="1920" height="1080" fill="url(#wallWarm)" />
    <rect y="800" width="1920" height="280" fill="#c79a6b" />
    <rect y="800" width="1920" height="10" fill="#a87a4e" />
    <Window x={1250} y={150} w={400} h={300} />
    {/* meubles hauts et plan de travail */}
    <rect x="80" y="130" width="780" height="230" rx="10" fill="#8d6b4f" />
    {[0, 1, 2, 3].map(i => <rect key={i} x={100 + i * 190} y="150" width="170" height="190" rx="8" fill="#a67c5b" />)}
    <rect x="80" y="560" width="860" height="240" rx="10" fill="#8d6b4f" />
    <rect x="60" y="545" width="900" height="30" rx="8" fill="#e8e1d3" />
    {[0, 1, 2, 3].map(i => <rect key={i} x={100 + i * 205} y="600" width="185" height="180" rx="8" fill="#a67c5b" />)}
    <circle cx="260" cy="535" r="26" fill="#d0d4d8" /><circle cx="360" cy="535" r="26" fill="#d0d4d8" />
    {/* frigo */}
    <rect x="1010" y="220" width="190" height="580" rx="16" fill="#e9eef2" />
    <rect x="1010" y="500" width="190" height="8" fill="#b9c3cc" />
    <rect x="1170" y="300" width="10" height="120" rx="5" fill="#9aa5ae" /><rect x="1170" y="540" width="10" height="150" rx="5" fill="#9aa5ae" />
    {/* table de premier plan */}
    <rect x="420" y="830" width="1080" height="38" rx="12" fill="#b9814f" />
    <rect x="470" y="868" width="26" height="170" fill="#9a6a3d" /><rect x="1424" y="868" width="26" height="170" fill="#9a6a3d" />
    <rect width="1920" height="1080" fill="url(#shade)" />
  </g>
);

const Salon: React.FC = () => (
  <g>
    <rect width="1920" height="1080" fill="url(#wallCool)" />
    <rect y="780" width="1920" height="300" fill="#b08968" />
    <rect y="780" width="1920" height="10" fill="#8a6a4f" />
    <Window x={160} y={140} w={340} h={380} />
    {/* tableau et thermostat */}
    <rect x="700" y="150" width="240" height="170" rx="6" fill="#f4efe3" stroke="#8d6b4f" strokeWidth="10" />
    <circle cx="790" cy="230" r="34" fill="#e9a23b" /><rect x="720" y="270" width="200" height="30" fill="#7fb069" />
    <rect x="1030" y="240" width="110" height="140" rx="16" fill="#f4f4f4" stroke="#b9c3cc" strokeWidth="6" />
    <circle cx="1085" cy="300" r="40" fill="#e8f1f8" stroke="#8aa1b5" strokeWidth="5" />
    <text x="1085" y="314" textAnchor="middle" fontFamily={FONT} fontWeight="900" fontSize="34" fill="#2d4a63">19°</text>
    {/* meuble TV */}
    <rect x="1230" y="560" width="520" height="200" rx="12" fill="#6b4a33" />
    <rect x="1270" y="260" width="440" height="270" rx="12" fill="#1e2530" />
    <rect x="1285" y="275" width="410" height="240" rx="6" fill="#2a3a52" />
    <circle cx="1490" cy="395" r="120" fill="url(#glow)" opacity="0.35" />
    {/* canapé */}
    <rect x="230" y="560" width="760" height="230" rx="46" fill="#c8553d" />
    <rect x="270" y="500" width="680" height="120" rx="40" fill="#d96a51" />
    <rect x="200" y="590" width="90" height="200" rx="36" fill="#b3452e" /><rect x="930" y="590" width="90" height="200" rx="36" fill="#b3452e" />
    {/* tapis et lampe */}
    <ellipse cx="960" cy="930" rx="520" ry="80" fill="#e9c46a" opacity="0.8" />
    <rect x="1780" y="400" width="14" height="380" fill="#4a3b2a" /><path d="M1730,400 L1844,400 L1816,320 L1758,320 Z" fill="#f6d77a" />
    <rect width="1920" height="1080" fill="url(#shade)" />
  </g>
);

const Supermarche: React.FC = () => {
  const cols = ["#e63946", "#f4a261", "#2a9d8f", "#457b9d", "#e9c46a", "#8ecae6", "#bc6c25", "#90be6d"];
  return (
    <g>
      <rect width="1920" height="1080" fill="#f6f2e8" />
      <rect y="760" width="1920" height="320" fill="#dcdcd6" />
      {[0, 1, 2, 3, 4, 5, 6, 7].map(i => <line key={i} x1={i * 280} y1="760" x2={960 + (i - 3.5) * 520} y2="1080" stroke="#c9c9c2" strokeWidth="3" />)}
      {[0, 1, 2].map(r => (
        <g key={r}>
          <rect x="60" y={160 + r * 190} width="1800" height="14" fill="#9aa5ae" />
          {Array.from({ length: 18 }).map((_, i) => <rect key={i} x={80 + i * 99} y={90 + r * 190} width="78" height="70" rx="6" fill={cols[(i * 3 + r * 5) % cols.length]} />)}
        </g>
      ))}
      <rect x="560" y="30" width="800" height="70" rx="12" fill="#e63946" />
      <text x="960" y="80" textAnchor="middle" fontFamily={FONT} fontWeight="900" fontSize="42" fill="#fff">PRIX AU KILO · PRIX AU LITRE</text>
      <rect width="1920" height="1080" fill="url(#shade)" />
    </g>
  );
};

const Route: React.FC = () => (
  <g>
    <rect width="1920" height="1080" fill="url(#sky)" />
    <circle cx="300" cy="190" r="70" fill="#ffe27a" />
    <path d="M0,640 Q300,480 620,600 T1240,560 T1920,600 L1920,760 L0,760 Z" fill="#7fb069" />
    <path d="M0,700 Q400,600 900,690 T1920,680 L1920,780 L0,780 Z" fill="#5a9a4b" />
    <rect y="760" width="1920" height="320" fill="#4b5058" />
    {Array.from({ length: 9 }).map((_, i) => <rect key={i} x={40 + i * 220} y="900" width="120" height="14" rx="6" fill="#f3e9c6" />)}
    {/* station-service */}
    <rect x="1420" y="520" width="360" height="30" rx="8" fill="#e63946" />
    <rect x="1450" y="550" width="18" height="230" fill="#c9c9c9" /><rect x="1730" y="550" width="18" height="230" fill="#c9c9c9" />
    <rect x="1540" y="600" width="130" height="180" rx="14" fill="#e63946" />
    <rect x="1560" y="625" width="90" height="60" rx="8" fill="#e8f1f8" />
    <rect width="1920" height="1080" fill="url(#shade)" opacity="0.5" />
  </g>
);

const Bureau: React.FC = () => (
  <g>
    <rect width="1920" height="1080" fill="#ebe5d6" />
    <rect y="800" width="1920" height="280" fill="#c1a27a" />
    <Window x={1300} y={150} w={360} h={280} />
    {/* calendrier et étagère */}
    <rect x="160" y="150" width="260" height="300" rx="10" fill="#fff" stroke="#c0392b" strokeWidth="10" />
    <rect x="160" y="150" width="260" height="70" rx="8" fill="#c0392b" />
    {Array.from({ length: 20 }).map((_, i) => <rect key={i} x={185 + (i % 5) * 46} y={250 + Math.floor(i / 5) * 46} width="34" height="34" rx="5" fill={i === 12 ? "#ffd60a" : "#ecebe5"} />)}
    <rect x="620" y="260" width="500" height="18" fill="#8d6b4f" />
    {[0, 1, 2, 3, 4, 5].map(i => <rect key={i} x={640 + i * 78} y={170 + (i % 2) * 14} width="62" height={90 - (i % 2) * 14} rx="4" fill={["#457b9d", "#e76f51", "#2a9d8f", "#e9c46a", "#8d6b4f", "#6a4c93"][i]} />)}
    {/* bureau */}
    <rect x="300" y="700" width="1320" height="44" rx="12" fill="#9a6a3d" />
    <rect x="360" y="744" width="30" height="300" fill="#7e5530" /><rect x="1530" y="744" width="30" height="300" fill="#7e5530" />
    <rect x="1010" y="570" width="340" height="130" rx="10" fill="#cfd6dd" /><rect x="1040" y="530" width="280" height="40" rx="6" fill="#2b3340" />
    <rect x="1000" y="360" width="360" height="220" rx="12" fill="#22303f" /><rect x="1018" y="378" width="324" height="184" rx="6" fill="#d9ecff" />
    <rect x="520" y="660" width="220" height="40" rx="4" fill="#fff" transform="rotate(-3 520 680)" /><rect x="540" y="630" width="220" height="40" rx="4" fill="#f4efe3" transform="rotate(2 540 650)" />
    <rect width="1920" height="1080" fill="url(#shade)" />
  </g>
);

const Exterieur: React.FC = () => (
  <g>
    <rect width="1920" height="1080" fill="url(#sky)" />
    <circle cx="1640" cy="170" r="80" fill="#ffe27a" />
    <ellipse cx="360" cy="190" rx="130" ry="46" fill="#fff" opacity="0.85" /><ellipse cx="470" cy="170" rx="100" ry="40" fill="#fff" opacity="0.85" />
    <rect y="900" width="1920" height="180" fill="#6fb552" />
    {/* maison en coupe */}
    <path d="M360,330 L960,110 L1560,330 Z" fill="#b5523b" />
    <rect x="400" y="330" width="1120" height="570" fill="#f4e6c8" />
    <rect x="400" y="330" width="1120" height="570" fill="none" stroke="#7e5530" strokeWidth="12" />
    <rect x="400" y="610" width="1120" height="12" fill="#7e5530" /><rect x="954" y="330" width="12" height="570" fill="#7e5530" />
    <rect x="412" y="342" width="536" height="262" fill="#e8d9ff" /><rect x="972" y="342" width="536" height="262" fill="#ffe4cf" />
    <rect x="412" y="634" width="536" height="258" fill="#fff0c2" /><rect x="972" y="634" width="536" height="258" fill="#d6f0e4" />
    <rect x="1280" y="680" width="200" height="212" rx="10" fill="#8d6b4f" opacity="0.8" />
    <rect x="450" y="760" width="300" height="130" rx="30" fill="#c8553d" opacity="0.85" />
    <rect x="470" y="420" width="190" height="120" rx="10" fill="#8ecae6" /><rect x="1100" y="420" width="190" height="120" rx="10" fill="#c9e4de" />
    <text x="680" y="400" fontFamily={FONT} fontWeight="900" fontSize="30" fill="#7e5530" opacity="0.8">CHAMBRES</text>
    <text x="680" y="670" fontFamily={FONT} fontWeight="900" fontSize="30" fill="#7e5530" opacity="0.8">SALON</text>
    <text x="1230" y="670" fontFamily={FONT} fontWeight="900" fontSize="30" fill="#7e5530" opacity="0.8">CUISINE</text>
    <rect x="360" y="900" width="1200" height="20" fill="#8a8f98" />
  </g>
);

const SETS: Record<SetId, React.FC> = { cuisine: Cuisine, salon: Salon, supermarche: Supermarche, route: Route, bureau: Bureau, exterieur: Exterieur };

/* ---------------- personnages ---------------- */
type Look = { skin: string; hair: string; top: string; bottom: string; scale: number; long?: boolean; tails?: boolean; dress?: boolean };
const LOOK: Record<Who, Look> = {
  claire: { skin: "#f1c9a5", hair: "#6b3e26", top: "#2a9d8f", bottom: "#33435c", scale: 1.0, long: true },
  thomas: { skin: "#e0ac86", hair: "#1f1a17", top: "#e76f51", bottom: "#3a4f7a", scale: 1.07 },
  lea: { skin: "#f6d4b4", hair: "#e9c46a", top: "#f4a1b8", bottom: "#f4a1b8", scale: 0.74, tails: true, dress: true },
  hugo: { skin: "#e8b992", hair: "#9b5a2d", top: "#4cc9f0", bottom: "#355070", scale: 0.56 }
};

const HANDS: Record<Pose, [[number, number], [number, number]]> = {
  idle: [[-92, -215], [92, -215]],
  worry: [[-44, -405], [44, -405]],
  happy: [[-100, -250], [100, -250]],
  point: [[-92, -215], [190, -385]],
  think: [[-92, -215], [38, -395]],
  talk: [[-92, -215], [150, -330]],
  cheer: [[-120, -500], [120, -500]]
};

const Person: React.FC<{ m: CastMember; f: number }> = ({ m, f }) => {
  const L = LOOK[m.who], pose = m.pose ?? "idle";
  const ph = (m.who.length * 7) % 11;
  const bob = Math.sin((f + ph * 5) / 14) * 5, talkWob = pose === "talk" ? Math.sin(f / 4) * 14 : pose === "cheer" ? Math.sin(f / 5) * 18 : 0;
  const blink = (f + ph * 9) % 110 < 5;
  const sc = (m.scale ?? 1) * L.scale;
  const hands = HANDS[pose].map(([x, y], i) => [x + (i === 1 ? talkWob : -talkWob * 0.4), y + (pose === "cheer" ? Math.abs(talkWob) * -0.4 : 0)]) as [number, number][];
  const brow = pose === "worry" ? 9 : pose === "think" ? 4 : 0;
  const mouth = pose === "worry" ? "M-16,-408 Q0,-420 16,-408" : pose === "happy" || pose === "cheer" ? "M-20,-414 Q0,-390 20,-414 Z" : pose === "talk" ? (Math.floor(f / 5) % 2 ? "M-14,-412 Q0,-396 14,-412 Z" : "M-14,-410 Q0,-406 14,-410") : "M-14,-410 Q0,-402 14,-410";
  const mouthFill = pose === "happy" || pose === "cheer" || (pose === "talk" && Math.floor(f / 5) % 2) ? "#8b2d2d" : "none";
  const y = m.y ?? 1000;
  return (
    <g transform={`translate(${m.x} ${y + bob * 0.4}) scale(${m.flip ? -sc : sc} ${sc})`}>
      <ellipse cx="0" cy="8" rx="95" ry="16" fill="#000" opacity="0.18" />
      {L.long ? <path d="M-64,-430 Q-80,-300 -50,-262 L50,-262 Q80,-300 64,-430 Z" fill={L.hair} /> : null}
      {/* jambes */}
      {L.dress ? <path d="M-70,-210 L70,-210 L96,-110 L-96,-110 Z" fill={L.bottom} /> : null}
      <rect x="-48" y={L.dress ? -120 : -190} width="38" height={L.dress ? 120 : 190} rx="12" fill={L.dress ? L.skin : L.bottom} />
      <rect x="10" y={L.dress ? -120 : -190} width="38" height={L.dress ? 120 : 190} rx="12" fill={L.dress ? L.skin : L.bottom} />
      <ellipse cx="-30" cy="0" rx="34" ry="14" fill="#2b2b33" /><ellipse cx="30" cy="0" rx="34" ry="14" fill="#2b2b33" />
      {/* tronc */}
      <rect x="-64" y="-372" width="128" height="196" rx="36" fill={L.top} />
      {/* bras */}
      {hands.map(([hx, hy], i) => (
        <g key={i}>
          <line x1={i === 0 ? -58 : 58} y1="-346" x2={hx} y2={hy} stroke={L.top} strokeWidth="32" strokeLinecap="round" />
          <circle cx={hx} cy={hy} r="19" fill={L.skin} />
        </g>
      ))}
      {/* tête */}
      <rect x="-14" y="-396" width="28" height="30" fill={L.skin} />
      <circle cx="0" cy="-430" r="58" fill={L.skin} />
      <path d={L.long ? "M-60,-436 Q-52,-500 0,-498 Q56,-500 62,-432 Q30,-462 -10,-450 Q-40,-446 -60,-436 Z" : "M-58,-440 Q-50,-494 0,-492 Q52,-494 58,-440 Q30,-470 0,-466 Q-30,-470 -58,-440 Z"} fill={L.hair} />
      {L.tails ? <><circle cx="-70" cy="-420" r="22" fill={L.hair} /><circle cx="70" cy="-420" r="22" fill={L.hair} /></> : null}
      {/* visage */}
      {blink ? <><line x1="-30" y1="-436" x2="-12" y2="-436" stroke="#2b2b33" strokeWidth="5" strokeLinecap="round" /><line x1="12" y1="-436" x2="30" y2="-436" stroke="#2b2b33" strokeWidth="5" strokeLinecap="round" /></>
        : <><ellipse cx="-21" cy="-434" rx="7" ry="9" fill="#2b2b33" /><ellipse cx="21" cy="-434" rx="7" ry="9" fill="#2b2b33" /></>}
      <line x1="-34" y1={-458 + brow} x2="-10" y2={-466 - brow * 0.2} stroke="#3b2a1c" strokeWidth="5" strokeLinecap="round" />
      <line x1="34" y1={-458 + brow} x2="10" y2={-466 - brow * 0.2} stroke="#3b2a1c" strokeWidth="5" strokeLinecap="round" />
      <path d={mouth} fill={mouthFill} stroke="#8b2d2d" strokeWidth="5" strokeLinecap="round" strokeLinejoin="round" />
      {pose === "worry" ? <path d="M58,-470 Q66,-450 58,-440 Q50,-450 58,-470 Z" fill="#8ecae6" /> : null}
    </g>
  );
};

const Bubble: React.FC<{ m: CastMember; f: number }> = ({ m, f }) => {
  if (!m.say) return null;
  const L = LOOK[m.who], sc = (m.scale ?? 1) * L.scale, y = (m.y ?? 1000) - 560 * sc;
  const d = (m.sayDelay ?? 0.6) * 30, k = Math.max(0, Math.min(1, (f - d) / 8));
  if (k <= 0) return null;
  const emoji = m.say.length <= 3;
  const w = emoji ? 150 : Math.max(260, m.say.length * 20);
  return (
    <g transform={`translate(${m.x} ${y}) scale(${0.6 + 0.4 * k})`} opacity={k}>
      <rect x={-w / 2} y="-110" width={w} height="110" rx="30" fill="#fff" stroke="#2b2b33" strokeWidth="5" />
      <path d="M-20,0 L0,34 L20,0 Z" fill="#fff" stroke="#2b2b33" strokeWidth="5" strokeLinejoin="round" />
      <rect x="-24" y="-8" width="48" height="12" fill="#fff" />
      <text x="0" y={emoji ? -28 : -42} textAnchor="middle" fontFamily={FONT} fontWeight={800} fontSize={emoji ? 76 : 30} fill="#2b2b33">{m.say}</text>
    </g>
  );
};

const Obj: React.FC<{ o: StageObj; f: number }> = ({ o, f }) => {
  const d = (o.delay ?? 0.3) * 30, k = Math.max(0, Math.min(1, (f - d) / 9));
  if (k <= 0) return null;
  const pop = k < 1 ? 1 + 0.25 * Math.sin(k * Math.PI) : 1;
  const by = o.bob ? Math.sin((f - d) / 10) * 8 : 0;
  return <text x={o.x} y={o.y + by} textAnchor="middle" fontFamily={EMOJI} fontSize={(o.size ?? 110) * k * pop} style={{ filter: "drop-shadow(0 6px 6px #0006)" }}>{o.emoji}</text>;
};

export const StageView: React.FC<{ stage: StageCfg; f: number; dur: number; w: number; h: number }> = ({ stage, f, dur, w, h }) => {
  const Set = SETS[stage.set];
  const push = interpolate(f, [0, dur], [1.0, 1.06], { extrapolateRight: "clamp" });
  const fade = interpolate(f, [0, 7], [0, 1], { extrapolateRight: "clamp" });
  return (
    <svg width={w} height={h} viewBox="0 0 1920 1080" style={{ position: "absolute", inset: 0, opacity: fade }}>
      <Defs />
      <g transform={`translate(960 600) scale(${push}) translate(-960 -600)`}>
        <Set />
        {(stage.objs || []).map((o, i) => <Obj key={i} o={o} f={f} />)}
        {(stage.cast || []).map((m, i) => <Person key={i} m={m} f={f} />)}
        {(stage.cast || []).map((m, i) => <Bubble key={"b" + i} m={m} f={f} />)}
      </g>
    </svg>
  );
};

/* Jauge de défi persistante (haut à droite). */
export const HudView: React.FC<{ label: string; goal: number; value: number; unit: string; color: string; w: number }> = ({ label, goal, value, unit, color, w }) => {
  const frac = Math.min(1, value / goal);
  return (
    <div style={{ position: "absolute", right: 40, top: 36, width: Math.min(620, w * 0.33), background: "#0b0f12ee", border: "4px solid #f0efe8", borderRadius: 18, padding: "12px 20px 14px", boxShadow: "0 10px 24px #000a", fontFamily: FONT }}>
      <div style={{ fontWeight: 900, fontSize: 24, color: "#ffd60a", letterSpacing: 2, textTransform: "uppercase" }}>{label}</div>
      <div style={{ marginTop: 8, height: 26, background: "#2a3236", borderRadius: 13, overflow: "hidden" }}><div style={{ width: `${frac * 100}%`, height: "100%", background: color, borderRadius: 13 }} /></div>
      <div style={{ display: "flex", justifyContent: "space-between", marginTop: 6, fontWeight: 900, fontSize: 28, color: "#f2f2ec" }}><span style={{ color }}>{Math.round(value)}{unit}</span><span>objectif {goal}{unit}</span></div>
    </div>
  );
};
