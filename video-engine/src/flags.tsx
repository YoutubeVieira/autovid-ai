import React from "react";

export type FlagDef = { w: number; h: number; node: React.ReactNode };

export const FLAGS: Record<string, FlagDef> = {
  gbr: {
    w: 60, h: 30,
    node: (
      <>
        <rect width="60" height="30" fill="#012169" />
        <path d="M0,0 L60,30 M60,0 L0,30" stroke="#fff" strokeWidth="6" />
        <path d="M0,0 L60,30 M60,0 L0,30" stroke="#C8102E" strokeWidth="2.4" />
        <path d="M30,0 V30 M0,15 H60" stroke="#fff" strokeWidth="10" />
        <path d="M30,0 V30 M0,15 H60" stroke="#C8102E" strokeWidth="6" />
      </>
    )
  },
  fra: {
    w: 3, h: 2,
    node: (
      <>
        <rect width="1" height="2" fill="#0055A4" />
        <rect x="1" width="1" height="2" fill="#fff" />
        <rect x="2" width="1" height="2" fill="#EF4135" />
      </>
    )
  },
  deu: {
    w: 5, h: 3,
    node: (
      <>
        <rect width="5" height="1" fill="#111" />
        <rect y="1" width="5" height="1" fill="#DD0000" />
        <rect y="2" width="5" height="1" fill="#FFCE00" />
      </>
    )
  }
};

export const Flag: React.FC<{ id: string; width: number; height: number; x?: number; y?: number; slice?: boolean }> = ({ id, width, height, x = 0, y = 0, slice = false }) => {
  const f = FLAGS[id];
  return (
    <svg x={x} y={y} width={width} height={height} viewBox={`0 0 ${f.w} ${f.h}`} preserveAspectRatio={slice ? "xMidYMid slice" : "none"}>
      {f.node}
    </svg>
  );
};
