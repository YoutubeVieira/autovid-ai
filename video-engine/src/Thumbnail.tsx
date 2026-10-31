import React from "react";
import { AbsoluteFill, useVideoConfig } from "remotion";
import { toScreen } from "./geo";
import { Arrow, EMOJI, FONT, Hex, MapLayer, Stat } from "./MapStory";
import type { Camera, LonLat, Scene } from "./types";

/* Miniature : carte France / Allemagne, flèche d'attaque de Francfort vers la France, gros texte jaune, chiffre d'exemple. */
export type ThumbProps = { line1: string; line2: string; stat: { value: number; prefix?: string; suffix: string; label: string } };

const FRANKFURT: LonLat = [8.68, 50.11], PARIS: LonLat = [2.35, 48.86];
const scene: Scene = { id: "thumb", text: "", camera: { lon: 0, lat: 0, zoom: 1 }, fills: { FRA: "flag", DEU: "flag" }, durationInFrames: 90, subtitles: [] };

const Outline: React.CSSProperties = { WebkitTextStroke: "16px #000", paintOrder: "stroke fill", textShadow: "0 10px 0 #000", filter: "drop-shadow(0 12px 16px #000b)" };

export const Thumbnail: React.FC<ThumbProps> = ({ line1, line2, stat }) => {
  const { width: w, height: h } = useVideoConfig();
  const wide = w > h;
  const cam: Camera = wide ? { lon: -2.2, lat: 48.6, zoom: 2.35 } : { lon: 3.2, lat: 48.0, zoom: 2.35 };
  const fr = toScreen(FRANKFURT, cam, w, h), pa = toScreen(PARIS, cam, w, h);
  const fs = wide ? 150 : 170;
  return (
    <AbsoluteFill style={{ background: "#0a1f29" }}>
      <MapLayer scenes={[scene]} i={0} f={99} cam={cam} blur={0} w={w} h={h} />
      <AbsoluteFill style={{ background: wide ? "linear-gradient(90deg, #000d 0%, #0008 38%, #0000 70%)" : "linear-gradient(180deg, #000d 0%, #0006 28%, #0000 52%, #0007 100%)" }} />
      <Arrow from={fr} to={pa} delay={0} color="#ff3b30" />
      <div style={{ position: "absolute", left: fr[0], top: fr[1] - (wide ? 20 : 30), transform: "translate(-50%,-50%)" }}><Hex r={wide ? 70 : 86}><text textAnchor="middle" dominantBaseline="central" fontSize={wide ? 76 : 92} y="4" fontFamily={EMOJI}>🏦</text></Hex></div>
      <div style={{ position: "absolute", left: pa[0] - (wide ? 40 : 60), top: pa[1] + (wide ? 70 : 150), transform: "translate(-50%,-50%)" }}><Hex r={wide ? 70 : 86}><text textAnchor="middle" dominantBaseline="central" fontSize={wide ? 76 : 92} y="4" fontFamily={EMOJI}>🏠</text></Hex></div>
      <div style={{ position: "absolute", left: wide ? 50 : 0, right: wide ? undefined : 0, top: wide ? 70 : 150, textAlign: wide ? "left" : "center", fontFamily: FONT, fontWeight: 900, textTransform: "uppercase", lineHeight: 0.98, fontSize: fs }}>
        <div style={{ color: "#fff", ...Outline }}>{line1}</div>
        <div style={{ color: "#ffd60a", ...Outline }}>{line2}</div>
      </div>
      <div style={{ position: "absolute", left: wide ? 50 : w / 2, bottom: wide ? 46 : 150, transform: wide ? "none" : "translateX(-50%) scale(1.15)", transformOrigin: wide ? "left bottom" : "center bottom" }}>
        <Stat it={{ kind: "stat", value: stat.value, prefix: stat.prefix, suffix: stat.suffix, label: stat.label, color: "#ff4d4d" }} delay={-60} />
      </div>
    </AbsoluteFill>
  );
};
