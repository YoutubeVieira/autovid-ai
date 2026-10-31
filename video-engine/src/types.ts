export type LonLat = [number, number];
export type Camera = { lon: number; lat: number; zoom: number };

/* Remplissage d'un pays : own = drapeau du pays, land = terre neutre, gray/red/yellow = teintes d'histoire,
   split = zone occupée (rouge) + zone libre (jaune), comme la France en 1940. */
export type FillKey = "land" | "flag" | "gray" | "red" | "yellow" | "split";

type Base = { delay?: number; until?: number; at?: LonLat; screen?: [number, number]; dx?: number; dy?: number };
export type Item =
  | (Base & { kind: "icon"; emoji: string })                                   // hexagone avec pictogramme
  | (Base & { kind: "person"; label: string; img?: string; ring?: string })    // médaillon + étiquette
  | (Base & { kind: "flagBadge"; flag: "gbr" | "fra" | "deu"; emoji?: string }) // hexagone drapeau
  | (Base & { kind: "bubble"; text?: string; emoji?: string; tail?: "left" | "right" })
  | (Base & { kind: "tag"; text: string })                                     // pastille grise (nom de pays)
  | (Base & { kind: "title"; text: string; sub?: string });                    // titre en haut

export type Subtitle = { text: string; from: number; to: number };
export type Scene = {
  id: string;
  text: string;
  camera: Camera;
  fills?: Record<string, FillKey>;
  items?: Item[];
  audio?: string;
  durationInFrames: number;
  subtitles: Subtitle[];
};
export type StoryProps = { title?: string; brand?: string; scenes: Scene[]; bg?: string };
