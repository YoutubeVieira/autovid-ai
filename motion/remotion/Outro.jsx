import React from "react";
import { AbsoluteFill, interpolate, spring, staticFile, useCurrentFrame, useVideoConfig } from "remotion";

const fonts = `
@font-face { font-family: "Anton"; src: url("${staticFile("Anton-Regular.ttf")}") format("truetype"); }
@font-face { font-family: "Marker"; src: url("${staticFile("PermanentMarker-Regular.ttf")}") format("truetype"); }
`;

// Carte de fin : bouton « s'abonner » cliqué, cloche, teaser de la suite, rappel « enregistre ».
export const Outro = ({ handle, teaser, cta, save, accent }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const pop = (delay) => spring({ frame: frame - delay, fps, config: { damping: 11, stiffness: 160 } });

  const titleScale = interpolate(pop(2), [0, 1], [2.2, 1]);
  const press = frame >= 30 && frame < 36 ? 0.92 : 1;           // le « clic » sur le bouton
  const subscribed = frame >= 33;
  const cursorX = interpolate(frame, [12, 30], [880, 560], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const cursorY = interpolate(frame, [12, 30], [1500, 1035], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const ring = interpolate(frame % 30, [0, 29], [0, 1]);
  const bell = subscribed ? Math.sin((frame - 33) * 0.9) * interpolate(frame, [33, 60], [22, 0], { extrapolateRight: "clamp" }) : 0;
  const flash = interpolate(frame, [0, 4], [0.9, 0], { extrapolateRight: "clamp" });

  return (
    <AbsoluteFill style={{ background: "radial-gradient(110% 60% at 50% 45%, #151a22 0%, #050608 72%)", fontFamily: "Anton", color: "#fff" }}>
      <style>{fonts}</style>
      {/* anneaux néon qui se propagent */}
      {[0, 0.5].map((o) => {
        const r = ((ring + o) % 1);
        return (
          <div key={o} style={{ position: "absolute", left: 540 - 200 - r * 380, top: 760 - 200 - r * 380, width: 400 + r * 760,
            height: 400 + r * 760, borderRadius: "50%", border: `6px solid ${accent}`, opacity: (1 - r) * 0.35 }} />
        );
      })}
      <div style={{ position: "absolute", top: 600, width: "100%", textAlign: "center", fontSize: 170, transform: `scale(${titleScale})`,
        textShadow: `0 0 34px ${accent}, 0 12px 0 #000` }}>{cta}</div>
      <div style={{ position: "absolute", top: 860, width: "100%", textAlign: "center", fontSize: 64, color: "#ffe600",
        opacity: pop(10), transform: `translateY(${(1 - pop(10)) * 40}px)` }}>{teaser}</div>

      {/* bouton s'abonner + cloche */}
      <div style={{ position: "absolute", top: 990, left: 0, width: "100%", display: "flex", justifyContent: "center", gap: 30,
        opacity: pop(14), transform: `scale(${press})` }}>
        <div style={{ padding: "22px 54px", borderRadius: 60, fontSize: 58, letterSpacing: 2,
          background: subscribed ? "#2a2f38" : "#ff0033", color: subscribed ? "#cfd3da" : "#fff" }}>
          {subscribed ? "ABONNÉ ✓" : "S'ABONNER"}
        </div>
        <div style={{ width: 110, height: 110, borderRadius: 55, background: "#2a2f38", display: "flex", alignItems: "center",
          justifyContent: "center", fontSize: 64, transform: `rotate(${bell}deg)` }}>🔔</div>
      </div>

      {/* curseur qui vient cliquer */}
      <div style={{ position: "absolute", left: cursorX, top: cursorY, fontSize: 90, opacity: frame < 50 ? pop(12) : 0,
        transform: `scale(${press})`, filter: "drop-shadow(0 6px 10px rgba(0,0,0,.7))" }}>👆</div>

      {save ? (  // une seule demande par vidéo (règle humanize) : le rappel « enregistre » est optionnel
        <div style={{ position: "absolute", top: 1240, width: "100%", textAlign: "center", fontFamily: "Marker", fontSize: 58, color: accent,
          opacity: pop(40), transform: `scale(${interpolate(pop(40), [0, 1], [0.6, 1])})` }}>🔖 {save}</div>
      ) : null}
      <div style={{ position: "absolute", bottom: 170, width: "100%", textAlign: "center", fontSize: 50, letterSpacing: 3,
        color: "rgba(255,255,255,.75)", opacity: pop(48) }}>{handle}</div>
      <AbsoluteFill style={{ background: "#fff", opacity: flash }} />
    </AbsoluteFill>
  );
};
