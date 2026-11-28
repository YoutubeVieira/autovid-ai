"""Genere un personnage 3D stylise (prof de gym senior) en OBJ + MTL.
Usage: python3 make_coach.py <dossier_sortie>"""
import math, sys, os

out = sys.argv[1]
os.makedirs(out, exist_ok=True)

MATERIALS = {
    "skin":     (0.93, 0.74, 0.62),
    "hair":     (0.78, 0.78, 0.82),
    "top":      (0.00, 0.72, 0.72),
    "leggings": (0.08, 0.08, 0.10),
    "shoes":    (0.95, 0.95, 0.95),
    "soles":    (0.15, 0.15, 0.15),
    "headband": (0.95, 0.35, 0.40),
    "whistle":  (0.95, 0.80, 0.10),
    "cord":     (0.10, 0.10, 0.10),
    "eyes":     (0.05, 0.05, 0.05),
    "mouth":    (0.75, 0.20, 0.25),
}

objects = []  # (name, material, verts, faces)

def sub(a, b): return (a[0]-b[0], a[1]-b[1], a[2]-b[2])
def cross(a, b): return (a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0])
def norm(a):
    l = math.sqrt(sum(c*c for c in a)) or 1.0
    return (a[0]/l, a[1]/l, a[2]/l)

def ellipsoid(c, r, seg=24, rings=16):
    v, f = [], []
    v.append((c[0], c[1]+r[1], c[2]))
    for i in range(1, rings):
        t = math.pi*i/rings
        for j in range(seg):
            p = 2*math.pi*j/seg
            v.append((c[0]+r[0]*math.sin(t)*math.cos(p),
                      c[1]+r[1]*math.cos(t),
                      c[2]+r[2]*math.sin(t)*math.sin(p)))
    v.append((c[0], c[1]-r[1], c[2]))
    for j in range(seg):
        f.append((0, 1+(j+1)%seg, 1+j))
    for i in range(rings-2):
        for j in range(seg):
            a = 1+i*seg+j; b = 1+i*seg+(j+1)%seg
            c2 = 1+(i+1)*seg+(j+1)%seg; d = 1+(i+1)*seg+j
            f.append((a, b, c2, d))
    last = len(v)-1
    base = 1+(rings-2)*seg
    for j in range(seg):
        f.append((last, base+j, base+(j+1)%seg))
    return v, f

def limb(p0, p1, r0, r1, seg=16, caps=True):
    """Cylindre conique de p0 a p1 avec calottes spheriques lisses."""
    axis = norm(sub(p1, p0))
    ref = (1, 0, 0) if abs(axis[0]) < 0.9 else (0, 0, 1)
    u = norm(cross(axis, ref)); w = cross(axis, u)
    v, f = [], []
    for k, (p, r) in enumerate(((p0, r0), (p1, r1))):
        for j in range(seg):
            a = 2*math.pi*j/seg
            v.append((p[0]+r*(math.cos(a)*u[0]+math.sin(a)*w[0]),
                      p[1]+r*(math.cos(a)*u[1]+math.sin(a)*w[1]),
                      p[2]+r*(math.cos(a)*u[2]+math.sin(a)*w[2])))
    for j in range(seg):
        f.append((j, (j+1)%seg, seg+(j+1)%seg, seg+j))
    if caps:
        for p, r in ((p0, r0), (p1, r1)):
            sv, sf = ellipsoid(p, (r, r, r), seg=seg, rings=max(6, seg//2))
            off = len(v); v += sv; f += [tuple(i+off for i in face) for face in sf]
    return v, f

def box(c, s):
    x, y, z = c; hx, hy, hz = s[0]/2, s[1]/2, s[2]/2
    v = [(x+dx*hx, y+dy*hy, z+dz*hz) for dx in (-1, 1) for dy in (-1, 1) for dz in (-1, 1)]
    f = [(0,1,3,2),(4,6,7,5),(0,4,5,1),(2,3,7,6),(0,2,6,4),(1,5,7,3)]
    return v, f

def add(name, mat, geom): objects.append((name, mat, geom[0], geom[1]))
def merge(*geoms):
    v, f = [], []
    for gv, gf in geoms:
        off = len(v); v += gv; f += [tuple(i+off for i in face) for face in gf]
    return v, f

# ---- Dimensions (metres, Y haut, face vers +Z, ~1.65 m) ----
HEAD_Y = 1.45
# Tete
add("Head", "skin", ellipsoid((0, HEAD_Y, 0), (0.115, 0.135, 0.12)))
add("Neck", "skin", limb((0, 1.33, 0), (0, 1.26, 0), 0.045, 0.05, caps=False))
# Cheveux courts argentes
add("Hair", "hair", ellipsoid((0, HEAD_Y+0.035, -0.012), (0.125, 0.12, 0.13)))
# Bandeau
add("Headband", "headband", limb((0, HEAD_Y+0.062, 0), (0, HEAD_Y+0.092, 0), 0.127, 0.127, seg=32, caps=False))
# Yeux, nez, bouche
add("Eyes", "eyes", merge(ellipsoid((-0.042, HEAD_Y+0.015, 0.108), (0.014, 0.018, 0.01), 12, 8),
                          ellipsoid((0.042, HEAD_Y+0.015, 0.108), (0.014, 0.018, 0.01), 12, 8)))
add("Nose", "skin", ellipsoid((0, HEAD_Y-0.015, 0.12), (0.016, 0.02, 0.02), 12, 8))
add("Mouth", "mouth", ellipsoid((0, HEAD_Y-0.065, 0.1), (0.04, 0.014, 0.014), 16, 8))
add("Ears", "skin", merge(ellipsoid((-0.118, HEAD_Y, 0), (0.014, 0.03, 0.02), 12, 8),
                          ellipsoid((0.118, HEAD_Y, 0), (0.014, 0.03, 0.02), 12, 8)))

# Torse (haut turquoise)
add("Top", "top", merge(
    limb((0, 1.22, 0), (0, 1.0, 0), 0.15, 0.125, seg=24),
    limb((0, 1.0, 0), (0, 0.92, 0), 0.125, 0.145, seg=24)))
# Bras (peau) : gauche (x-) le long du corps, droit (x+) leve poing en l'air
add("Arm_L_upper", "skin", limb((-0.17, 1.2, 0), (-0.22, 1.0, 0.0), 0.045, 0.04))
add("Arm_L_lower", "skin", limb((-0.22, 1.0, 0.0), (-0.20, 0.82, 0.05), 0.04, 0.034))
add("Hand_L", "skin", ellipsoid((-0.2, 0.78, 0.06), (0.035, 0.045, 0.03), 12, 8))
add("Arm_R_upper", "skin", limb((0.17, 1.2, 0), (0.30, 1.15, 0.03), 0.045, 0.04))
add("Arm_R_lower", "skin", limb((0.30, 1.15, 0.03), (0.28, 1.36, 0.06), 0.04, 0.034))
add("Hand_R", "skin", ellipsoid((0.28, 1.4, 0.06), (0.04, 0.04, 0.04), 12, 8))
# Bretelles du haut sur les epaules
add("Shoulders", "top", merge(ellipsoid((-0.15, 1.21, 0), (0.05, 0.04, 0.05), 12, 8),
                              ellipsoid((0.15, 1.21, 0), (0.05, 0.04, 0.05), 12, 8)))
# Bassin + jambes (legging)
add("Hips", "leggings", ellipsoid((0, 0.88, 0), (0.15, 0.1, 0.11)))
add("Leg_L_upper", "leggings", limb((-0.075, 0.86, 0), (-0.08, 0.5, 0.02), 0.075, 0.055))
add("Leg_L_lower", "leggings", limb((-0.08, 0.5, 0.02), (-0.08, 0.1, 0), 0.055, 0.04))
add("Leg_R_upper", "leggings", limb((0.075, 0.86, 0), (0.08, 0.5, 0.02), 0.075, 0.055))
add("Leg_R_lower", "leggings", limb((0.08, 0.5, 0.02), (0.08, 0.1, 0), 0.055, 0.04))
# Baskets
add("Shoe_L", "shoes", ellipsoid((-0.08, 0.055, 0.05), (0.05, 0.05, 0.11), 16, 10))
add("Shoe_R", "shoes", ellipsoid((0.08, 0.055, 0.05), (0.05, 0.05, 0.11), 16, 10))
add("Soles", "soles", merge(box((-0.08, 0.01, 0.05), (0.1, 0.02, 0.22)),
                            box((0.08, 0.01, 0.05), (0.1, 0.02, 0.22))))
# Cordon + sifflet
add("Cord", "cord", merge(limb((-0.07, 1.26, 0.03), (0, 1.14, 0.135), 0.004, 0.004, 6, False),
                          limb((0.07, 1.26, 0.03), (0, 1.14, 0.135), 0.004, 0.004, 6, False)))
add("Whistle", "whistle", merge(box((0, 1.12, 0.14), (0.04, 0.02, 0.025)),
                                ellipsoid((0, 1.12, 0.14), (0.014, 0.014, 0.014), 8, 6)))

# ---- Ecriture OBJ/MTL ----
name = "coach_senior"
with open(os.path.join(out, name + ".mtl"), "w") as m:
    for k, (r, g, b) in MATERIALS.items():
        m.write(f"newmtl {k}\nKd {r:.3f} {g:.3f} {b:.3f}\nKa 0 0 0\nKs 0.1 0.1 0.1\nNs 20\nd 1\nillum 2\n\n")
nv = 0
with open(os.path.join(out, name + ".obj"), "w") as o:
    o.write(f"# Prof de gym senior - personnage stylise low-poly\n# unites: metres, Y haut, face vers +Z\nmtllib {name}.mtl\n")
    for oname, mat, v, f in objects:
        o.write(f"o {oname}\nusemtl {mat}\ns 1\n")
        for x, y, z in v: o.write(f"v {x:.5f} {y:.5f} {z:.5f}\n")
        for face in f: o.write("f " + " ".join(str(i+1+nv) for i in face) + "\n")
        nv += len(v)
print(f"{len(objects)} objets, {nv} sommets -> {out}/{name}.obj")
