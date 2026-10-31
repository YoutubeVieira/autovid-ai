#!/usr/bin/env node
/* Télécharge les contours des pays (Natural Earth, domaine public) et garde l'Europe + Afrique du Nord.
   Écrit public/geo/europe.json (coordonnées arrondies à 2 décimales).
   Usage : node tools/fetch-assets.mjs */
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const URL_GEO = "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_50m_admin_0_countries.geojson";
const EXTENT = [-25, 27, 45, 72]; // lonMin, latMin, lonMax, latMax

const res = await fetch(URL_GEO);
if (!res.ok) throw new Error("Téléchargement impossible : HTTP " + res.status);
const src = await res.json();

const round = n => Math.round(n * 100) / 100;
const bbox = ring => ring.reduce((b, [x, y]) => [Math.min(b[0], x), Math.min(b[1], y), Math.max(b[2], x), Math.max(b[3], y)], [180, 90, -180, -90]);
const hits = b => b[0] <= EXTENT[2] && b[2] >= EXTENT[0] && b[1] <= EXTENT[3] && b[3] >= EXTENT[1];

const features = [];
for (const f of src.features) {
  const g = f.geometry;
  const polys = g.type === "Polygon" ? [g.coordinates] : g.coordinates;
  const keep = polys.filter(p => hits(bbox(p[0])));
  if (!keep.length) continue;
  features.push({
    type: "Feature",
    properties: { id: f.properties.ADM0_A3, name: f.properties.NAME },
    geometry: { type: "MultiPolygon", coordinates: keep.map(p => p.map(r => r.map(([x, y]) => [round(x), round(y)]))) }
  });
}
fs.mkdirSync(path.join(root, "public/geo"), { recursive: true });
const out = path.join(root, "public/geo/europe.json");
fs.writeFileSync(out, JSON.stringify({ type: "FeatureCollection", features }));
console.log(features.length + " pays écrits dans " + out + " (" + Math.round(fs.statSync(out).size / 1024) + " Ko)");
