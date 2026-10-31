import { geoMercator, geoPath } from "d3-geo";
import geoData from "../public/geo/europe.json";
import type { Camera, LonLat } from "./types";

export const W = 1080;
export const H = 1920;
const projection = geoMercator().scale(1300).translate([0, 0]);
const path = geoPath(projection);

type Feat = { id: string; name: string; d: string; flagBox: [number, number, number, number] };

/* Plus grand polygone (par boîte englobante) : sert à caler le drapeau sur la métropole,
   sans que des îles lointaines étirent le motif. */
function mainBox(coords: number[][][][]): [number, number, number, number] {
  let best: [number, number, number, number] = [0, 0, 1, 1], area = -1;
  for (const poly of coords) {
    const [[x0, y0], [x1, y1]] = path.bounds({ type: "Polygon", coordinates: poly } as any);
    const a = (x1 - x0) * (y1 - y0);
    if (a > area) { area = a; best = [x0, y0, x1 - x0, y1 - y0]; }
  }
  return best;
}

export const features: Feat[] = (geoData as any).features.map((f: any) => ({
  id: f.properties.id, name: f.properties.name, d: path(f) || "", flagBox: mainBox(f.geometry.coordinates)
}));

export const project = (p: LonLat): [number, number] => projection(p) as [number, number];

export const polygonPath = (pts: LonLat[]) => "M" + pts.map(p => project(p).join(",")).join("L") + "Z";

/* Position écran d'un point géographique pour une caméra donnée. */
export function toScreen(p: LonLat, cam: Camera, w = W, h = H): [number, number] {
  const [cx, cy] = project([cam.lon, cam.lat]);
  const [x, y] = project(p);
  return [(x - cx) * cam.zoom + w / 2, (y - cy) * cam.zoom + h / 2];
}

export function cameraTransform(cam: Camera, w = W, h = H): string {
  const [cx, cy] = project([cam.lon, cam.lat]);
  return `translate(${w / 2} ${h / 2}) scale(${cam.zoom}) translate(${-cx} ${-cy})`;
}

/* Zone « libre » de la France de 1940 (au sud de la ligne de démarcation), tracée à la main :
   approximation visuelle, pas une frontière exacte. */
export const FREE_ZONE: LonLat[] = [
  [6.2, 46.4], [5.6, 47.0], [4.9, 46.8], [3.4, 46.7], [2.1, 47.1], [0.9, 47.3], [0.2, 46.5], [-0.1, 45.7],
  [-0.9, 44.6], [-1.5, 43.5], [-3, 42], [-3, 40], [10, 40], [10, 46.4]
];
