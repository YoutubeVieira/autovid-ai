import React from "react";
import { Composition } from "remotion";
import { MapStory } from "./MapStory";
import { Thumbnail } from "./Thumbnail";
import { H, W } from "./geo";
import type { StoryProps } from "./types";

const FPS = 30;
const demo: StoryProps = {
  scenes: [{ id: "demo", text: "Exemple", camera: { lon: 2, lat: 49, zoom: 2.4 }, fills: { FRA: "flag", GBR: "flag" }, durationInFrames: 90, subtitles: [{ text: "Exemple", from: 0, to: 3 }] }]
};

const thumbDefaults = { line1: "TON CRÉDIT", line2: "MONTE ?", stat: { value: 103, prefix: "+", suffix: " €", label: "par mois · exemple" } };

export const Root: React.FC = () => (
  <>
    <Composition id="ThumbWide" component={Thumbnail} width={1280} height={720} fps={FPS} durationInFrames={90} defaultProps={thumbDefaults} />
    <Composition id="ThumbTall" component={Thumbnail} width={1080} height={1920} fps={FPS} durationInFrames={90} defaultProps={thumbDefaults} />
  <Composition
    id="MapStory"
    component={MapStory}
    width={W}
    height={H}
    fps={FPS}
    durationInFrames={90}
    defaultProps={demo}
    calculateMetadata={({ props }) => ({ durationInFrames: Math.max(1, (props as StoryProps).scenes.reduce((n, s) => n + s.durationInFrames, 0)) })}
  />
  </>
);
