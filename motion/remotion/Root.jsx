import React from "react";
import { Composition } from "remotion";
import { Outro } from "./Outro.jsx";

export const Root = () => (
  <Composition
    id="Outro"
    component={Outro}
    durationInFrames={90}
    fps={30}
    width={1080}
    height={1920}
    defaultProps={{
      handle: "@capoeirajacobina",
      teaser: "PARTIE 2 : LA DÉFENSE",
      cta: "ABONNE-TOI",
      save: "ENREGISTRE ET ESSAIE",
      accent: "#39ff14",
    }}
  />
);
