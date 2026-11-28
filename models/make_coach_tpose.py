"""Genere un personnage 3D stylise en T-pose (prof de gym senior) en OBJ + MTL, pret pour Blender.
Usage: python3 make_coach_tpose.py <dossier_sortie>
Unites: metres, Y haut, visage vers +Z, hauteur ~1.65 m."""
import math, sys, os

out = sys.argv[1]
os.makedirs(out, exist_ok=True)

MATERIALS = {
    "skin":      (0.86, 0.66, 0.55),
    "lips":      (0.72, 0.42, 0.42),
    "hair":      (0.72, 0.72, 0.75),
    "brows":     (0.55, 0.55, 0.58),
    "eye_white": (0.95, 0.95, 0.95),
    "iris":      (0.38, 0.50, 0.58),
    "pupil":     (0.03, 0.03, 0.03),
    "bra":       (0.50, 0.42, 0.76),
    "leggings":  (0.26, 0.26, 0.28),
    "waistband": (0.19, 0.19, 0.21),
    "shoes":     (0.88, 0.88, 0.92),
    "soles":     (0.80, 0.80, 0.82),
}

objects = []

def sub(a, b): return (a[0]-b[0], a[1]-b[1], a[2]-b[2])
def add3(a, b): return (a[0]+b[0], a[1]+b[1], a[2]+b[2])
def dot(a, b): return a[0]*b[0]+a[1]*b[1]+a[2]*b[2]
def cross(a, b): return (a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0])
def norm(a):
    l = math.sqrt(dot(a, a)) or 1.0
    return (a[0]/l, a[1]/l, a[2]/l)

def ellipsoid(c, r, seg=24, rings=16):
    v, f = [(c[0], c[1]+r[1], c[2])], []
    for i in range(1, rings):
        t = math.pi*i/rings
        for j in range(seg):
            p = 2*math.pi*j/seg
            v.append((c[0]+r[0]*math.sin(t)*math.cos(p), c[1]+r[1]*math.cos(t), c[2]+r[2]*math.sin(t)*math.sin(p)))
    v.append((c[0], c[1]-r[1], c[2]))
    for j in range(seg): f.append((0, 1+(j+1)%seg, 1+j))
    for i in range(rings-2):
        for j in range(seg):
            a = 1+i*seg+j; b = 1+i*seg+(j+1)%seg; c2 = 1+(i+1)*seg+(j+1)%seg; d = 1+(i+1)*seg+j
            f.append((a, b, c2, d))
    last = len(v)-1; base = 1+(rings-2)*seg
    for j in range(seg): f.append((last, base+j, base+(j+1)%seg))
    return v, f

def loft(secs, u, w, seg=28, cap_start=True, cap_end=True):
    """secs = [(centre, rayon_u, rayon_w), ...]; sections elliptiques dans le plan (u, w)."""
    v, f = [], []
    for c, ru, rw in secs:
        for j in range(seg):
            a = 2*math.pi*j/seg
            v.append((c[0]+ru*math.cos(a)*u[0]+rw*math.sin(a)*w[0],
                      c[1]+ru*math.cos(a)*u[1]+rw*math.sin(a)*w[1],
                      c[2]+ru*math.cos(a)*u[2]+rw*math.sin(a)*w[2]))
    def orient(idx, ref_c, ref_dir=None):
        pts = [v[i] for i in idx]
        n = cross(sub(pts[1], pts[0]), sub(pts[2], pts[0]))
        cen = (sum(p[0] for p in pts)/len(pts), sum(p[1] for p in pts)/len(pts), sum(p[2] for p in pts)/len(pts))
        want = ref_dir if ref_dir is not None else sub(cen, ref_c)
        return tuple(idx) if dot(n, want) >= 0 else tuple(reversed(idx))
    for i in range(len(secs)-1):
        rc = tuple((secs[i][0][k]+secs[i+1][0][k])/2 for k in range(3))
        for j in range(seg):
            f.append(orient((i*seg+j, i*seg+(j+1)%seg, (i+1)*seg+(j+1)%seg, (i+1)*seg+j), rc))
    for cap, (si, nb) in ((cap_start, (0, 1)), (cap_end, (len(secs)-1, len(secs)-2))):
        if not cap: continue
        ci = len(v); v.append(secs[si][0])
        away = sub(secs[si][0], secs[nb][0])
        for j in range(seg):
            f.append(orient((ci, si*seg+(j+1)%seg, si*seg+j), None, away))
    return v, f

def limb(p0, p1, r0, r1, seg=10):
    axis = norm(sub(p1, p0)); ref = (1, 0, 0) if abs(axis[0]) < 0.9 else (0, 0, 1)
    u = norm(cross(axis, ref)); w = cross(axis, u)
    return loft([(p0, r0, r0), (p1, r1, r1)], u, w, seg=seg)

def box(c, s):
    x, y, z = c; hx, hy, hz = s[0]/2, s[1]/2, s[2]/2
    v = [(x+dx*hx, y+dy*hy, z+dz*hz) for dx in (-1, 1) for dy in (-1, 1) for dz in (-1, 1)]
    f = [(0,1,3,2),(4,6,7,5),(0,4,5,1),(2,3,7,6),(0,2,6,4),(1,5,7,3)]
    return v, f

def merge(*geoms):
    v, f = [], []
    for gv, gf in geoms:
        off = len(v); v += gv; f += [tuple(i+off for i in face) for face in gf]
    return v, f

def add(name, mat, geom): objects.append((name, mat, geom[0], geom[1]))
def mirror(g): return ([(-x, y, z) for x, y, z in g[0]], [tuple(reversed(face)) for face in g[1]])
X, Y, Z = (1, 0, 0), (0, 1, 0), (0, 0, 1)

# ================= TETE =================
HY = 1.50
add("Head", "skin", ellipsoid((0, HY, 0), (0.088, 0.112, 0.098), 32, 20))
add("Jaw", "skin", ellipsoid((0, HY-0.045, 0.012), (0.074, 0.07, 0.08), 28, 14))
add("Neck", "skin", loft([((0, 1.34, 0), 0.05, 0.048), ((0, 1.40, 0.005), 0.042, 0.042), ((0, 1.45, 0.01), 0.04, 0.04)], X, Z))
add("Ears", "skin", merge(ellipsoid((-0.088, HY-0.005, -0.005), (0.012, 0.028, 0.018), 12, 8),
                          ellipsoid((0.088, HY-0.005, -0.005), (0.012, 0.028, 0.018), 12, 8)))
add("Nose", "skin", ellipsoid((0, HY-0.028, 0.098), (0.012, 0.022, 0.018), 12, 8))
add("Lips", "lips", ellipsoid((0, HY-0.062, 0.083), (0.028, 0.008, 0.01), 16, 8))
add("Eye_whites", "eye_white", merge(ellipsoid((-0.034, HY+0.012, 0.085), (0.015, 0.009, 0.01), 14, 8),
                                     ellipsoid((0.034, HY+0.012, 0.085), (0.015, 0.009, 0.01), 14, 8)))
add("Irises", "iris", merge(ellipsoid((-0.034, HY+0.012, 0.092), (0.0075, 0.0075, 0.004), 12, 8),
                            ellipsoid((0.034, HY+0.012, 0.092), (0.0075, 0.0075, 0.004), 12, 8)))
add("Pupils", "pupil", merge(ellipsoid((-0.034, HY+0.012, 0.0955), (0.003, 0.003, 0.002), 8, 6),
                             ellipsoid((0.034, HY+0.012, 0.0955), (0.003, 0.003, 0.002), 8, 6)))
add("Brows", "brows", merge(ellipsoid((-0.034, HY+0.037, 0.083), (0.02, 0.003, 0.006), 12, 6),
                            ellipsoid((0.034, HY+0.037, 0.083), (0.02, 0.003, 0.006), 12, 6)))
# Cheveux gris ondules (carre mi-long)
add("Hair", "hair", merge(
    ellipsoid((0, HY+0.03, -0.03), (0.098, 0.092, 0.108), 28, 16),            # calotte
    ellipsoid((0, HY-0.03, -0.06), (0.1, 0.125, 0.07), 24, 14),               # volume arriere (carre)
    ellipsoid((-0.088, HY-0.05, -0.02), (0.02, 0.075, 0.06), 16, 12),         # meches gauche
    ellipsoid((0.088, HY-0.05, -0.02), (0.02, 0.075, 0.06), 16, 12),          # meches droite
    ellipsoid((0, HY+0.07, 0.045), (0.08, 0.04, 0.05), 16, 10)))              # frange

# ================= TORSE (peau) + HAUT =================
torso = [((0, 1.00, 0), 0.12, 0.088), ((0, 1.04, 0), 0.118, 0.086), ((0, 1.12, 0), 0.126, 0.092),
         ((0, 1.20, 0), 0.142, 0.1), ((0, 1.27, 0), 0.155, 0.092), ((0, 1.32, 0), 0.13, 0.08),
         ((0, 1.36, 0), 0.06, 0.055)]
add("Torso", "skin", loft(torso, X, Z))
add("Shoulders", "skin", merge(ellipsoid((-0.185, 1.285, 0), (0.05, 0.048, 0.048), 16, 10),
                               ellipsoid((0.185, 1.285, 0), (0.05, 0.048, 0.048), 16, 10)))
bra = [((0, 1.135, 0), 0.134, 0.1), ((0, 1.20, 0), 0.152, 0.112), ((0, 1.26, 0), 0.159, 0.103), ((0, 1.285, 0), 0.153, 0.096)]
chest = merge(ellipsoid((-0.06, 1.19, 0.07), (0.066, 0.052, 0.05), 16, 10),
              ellipsoid((0.06, 1.19, 0.07), (0.066, 0.052, 0.05), 16, 10))
straps = merge(*[limb(a, b, 0.011, 0.011) for s in (-1, 1) for a, b in (
    ((s*0.065, 1.24, 0.095), (s*0.06, 1.335, 0.045)), ((s*0.06, 1.335, 0.045), (s*0.075, 1.33, -0.06)))])
add("Sports_bra", "bra", merge(loft(bra, X, Z), chest, straps))

# ================= BRAS EN T-POSE =================
def arm(s):
    secs = [((s*0.19, 1.285, 0), 0.049, 0.046), ((s*0.32, 1.285, 0), 0.043, 0.041), ((s*0.45, 1.285, 0), 0.037, 0.035),
            ((s*0.58, 1.285, 0), 0.032, 0.03), ((s*0.685, 1.285, 0), 0.023, 0.02)]
    return loft(secs, Y, Z, seg=16)
add("Arm_L", "skin", arm(-1)); add("Arm_R", "skin", arm(1))
def hand(s):
    parts = [ellipsoid((s*0.725, 1.285, 0), (0.042, 0.011, 0.034), 14, 8)]
    for k, zoff in enumerate((-0.021, -0.007, 0.007, 0.021)):
        ln = (0.052, 0.058, 0.054, 0.044)[k]
        parts.append(limb((s*0.755, 1.285, zoff), (s*(0.755+ln), 1.283, zoff*1.5), 0.0075, 0.0055, 8))
    parts.append(limb((s*0.705, 1.285, 0.028), (s*0.74, 1.285, 0.055), 0.009, 0.007, 8))
    return merge(*parts)
add("Hand_L", "skin", hand(-1)); add("Hand_R", "skin", hand(1))

# ================= BASSIN / LEGGING =================
pelvis = [((0, 0.78, 0), 0.15, 0.096), ((0, 0.86, 0), 0.16, 0.102), ((0, 0.93, 0), 0.148, 0.098), ((0, 0.98, 0), 0.13, 0.092), ((0, 1.02, 0), 0.122, 0.089)]
add("Leggings_hips", "leggings", loft(pelvis, X, Z))
add("Waistband", "waistband", loft([((0, 1.0, 0), 0.127, 0.093), ((0, 1.05, 0), 0.123, 0.09)], X, Z))
def leg(s):
    secs = [((s*0.078, 0.92, 0), 0.082, 0.094), ((s*0.078, 0.78, 0.002), 0.08, 0.088), ((s*0.08, 0.62, 0.004), 0.072, 0.076),
            ((s*0.078, 0.46, 0.004), 0.056, 0.058), ((s*0.076, 0.30, 0), 0.05, 0.054), ((s*0.074, 0.14, 0), 0.036, 0.038),
            ((s*0.074, 0.085, 0), 0.034, 0.036)]
    return loft(secs, X, Z)
add("Leg_L", "leggings", leg(-1)); add("Leg_R", "leggings", leg(1))
# Baskets blanches
def shoe(s):
    return merge(ellipsoid((s*0.076, 0.065, 0.035), (0.045, 0.05, 0.105), 20, 12),
                 ellipsoid((s*0.076, 0.095, -0.01), (0.04, 0.04, 0.05), 14, 8))
add("Shoe_L", "shoes", shoe(-1)); add("Shoe_R", "shoes", shoe(1))
add("Soles", "soles", merge(box((-0.076, 0.012, 0.035), (0.092, 0.024, 0.225)), box((0.076, 0.012, 0.035), (0.092, 0.024, 0.225))))

# ================= ECRITURE OBJ / MTL =================
name = "coach_senior_tpose"
with open(os.path.join(out, name + ".mtl"), "w") as m:
    for k, (r, g, b) in MATERIALS.items():
        m.write(f"newmtl {k}\nKd {r:.3f} {g:.3f} {b:.3f}\nKa 0 0 0\nKs 0.1 0.1 0.1\nNs 20\nd 1\nillum 2\n\n")
nv = 0
with open(os.path.join(out, name + ".obj"), "w") as o:
    o.write(f"# Prof de gym senior - T-pose stylisee\n# unites: metres, Y haut, face vers +Z\nmtllib {name}.mtl\n")
    for oname, mat, v, f in objects:
        o.write(f"o {oname}\nusemtl {mat}\ns 1\n")
        for x, y, z in v: o.write(f"v {x:.5f} {y:.5f} {z:.5f}\n")
        for face in f: o.write("f " + " ".join(str(i+1+nv) for i in face) + "\n")
        nv += len(v)
print(f"{len(objects)} objets, {nv} sommets -> {out}/{name}.obj")
