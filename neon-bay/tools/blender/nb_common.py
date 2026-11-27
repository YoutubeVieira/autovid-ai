"""Shared helpers for the Neon Bay procedural asset pipeline (Blender 5.x, bpy module).

Every generator imports this module:  scene reset, materials, mesh building,
auto-smooth, modifier application, glTF export (+ base64 .glb.js fallback).

Conventions (Blender side, Z-up):  the glTF exporter is always called with
export_yup=True, so Blender +X -> glTF +X, Blender +Z -> glTF +Y,
Blender -Y -> glTF +Z.
"""
import base64
import math
import os

import bpy  # noqa: F401  (must come before bmesh / mathutils)
import bmesh
from mathutils import Vector

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
MODELS = os.path.join(ROOT, "models")


# --------------------------------------------------------------------------- scene
def reset_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    for coll in (bpy.data.meshes, bpy.data.materials, bpy.data.actions, bpy.data.armatures):
        for block in list(coll):
            coll.remove(block)


def link(obj):
    bpy.context.scene.collection.objects.link(obj)
    return obj


# --------------------------------------------------------------------------- materials
def material(name, color, metallic=0.0, roughness=0.5, emission=None, strength=0.0,
             alpha=1.0, transmission=0.0):
    """Principled material; name is the contract the game relies on."""
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    c = tuple(color) + (1.0,) if len(color) == 3 else tuple(color)
    bsdf.inputs["Base Color"].default_value = c
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = roughness
    if emission is not None:
        bsdf.inputs["Emission Color"].default_value = tuple(emission) + (1.0,)
        bsdf.inputs["Emission Strength"].default_value = strength
    if alpha < 1.0:
        bsdf.inputs["Alpha"].default_value = alpha
        try:
            mat.surface_render_method = "BLENDED"
        except Exception:
            pass
    mat.diffuse_color = c
    return mat


# --------------------------------------------------------------------------- mesh building
def mesh_object(name, verts, faces, mats=(), face_mats=None):
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(v) for v in verts], [], [tuple(f) for f in faces])
    me.validate(clean_customdata=False)
    me.update()
    obj = link(bpy.data.objects.new(name, me))
    for m in mats:
        me.materials.append(m)
    if face_mats is not None:
        for p, mi in zip(me.polygons, face_mats):
            p.material_index = mi
    return obj


def bm_to_object(name, bm, mats=()):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    obj = link(bpy.data.objects.new(name, me))
    for m in mats:
        me.materials.append(m)
    return obj


def lathe(profile, segments, axis="Y", cap_start=False, cap_end=False):
    """Revolve a list of (radius, axial) points around an axis. Returns verts, faces."""
    verts, faces = [], []
    n = len(profile)
    for s in range(segments):
        a = 2 * math.pi * s / segments
        ca, sa = math.cos(a), math.sin(a)
        for r, h in profile:
            if axis == "Y":
                verts.append((r * ca, h, r * sa))
            elif axis == "Z":
                verts.append((r * ca, r * sa, h))
            else:
                verts.append((h, r * ca, r * sa))
    for s in range(segments):
        s2 = (s + 1) % segments
        for i in range(n - 1):
            a, b = s * n + i, s * n + i + 1
            c, d = s2 * n + i + 1, s2 * n + i
            faces.append((a, b, c, d))
    if cap_start:
        faces.append(tuple(s * n for s in reversed(range(segments))))
    if cap_end:
        faces.append(tuple(s * n + n - 1 for s in range(segments)))
    return verts, faces


def box(name, size, loc=(0, 0, 0), mat=None, bevel=0.0, segments=1):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co = Vector((v.co.x * size[0], v.co.y * size[1], v.co.z * size[2])) + Vector(loc)
    obj = bm_to_object(name, bm, [mat] if mat else [])
    if bevel > 0:
        add_bevel(obj, bevel, segments)
        apply_modifiers(obj)
    return obj


def cylinder(name, radius, depth, loc=(0, 0, 0), verts=12, mat=None, axis="Z", r2=None):
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=verts, radius1=radius,
                          radius2=radius if r2 is None else r2, depth=depth)
    if axis == "X":
        bmesh.ops.rotate(bm, verts=bm.verts, cent=(0, 0, 0),
                         matrix=__import__("mathutils").Matrix.Rotation(math.pi / 2, 3, "Y"))
    elif axis == "Y":
        bmesh.ops.rotate(bm, verts=bm.verts, cent=(0, 0, 0),
                         matrix=__import__("mathutils").Matrix.Rotation(math.pi / 2, 3, "X"))
    bmesh.ops.translate(bm, verts=bm.verts, vec=Vector(loc))
    return bm_to_object(name, bm, [mat] if mat else [])


def uv_sphere(name, radius, loc=(0, 0, 0), seg=10, rings=6, mat=None, scale=(1, 1, 1)):
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=seg, v_segments=rings, radius=radius)
    for v in bm.verts:
        v.co = Vector((v.co.x * scale[0], v.co.y * scale[1], v.co.z * scale[2])) + Vector(loc)
    return bm_to_object(name, bm, [mat] if mat else [])


# --------------------------------------------------------------------------- modifiers
def add_bevel(obj, width, segments=2, angle=35):
    m = obj.modifiers.new("Bevel", "BEVEL")
    m.width = width
    m.segments = segments
    m.limit_method = "ANGLE"
    m.angle_limit = math.radians(angle)
    m.harden_normals = False
    return m


def add_subsurf(obj, levels=1):
    m = obj.modifiers.new("Subsurf", "SUBSURF")
    m.levels = levels
    m.render_levels = levels
    return m


def apply_modifiers(obj):
    """Apply the modifier stack without bpy.ops (works headless)."""
    dg = bpy.context.evaluated_depsgraph_get()
    ev = obj.evaluated_get(dg)
    me = bpy.data.meshes.new_from_object(ev, preserve_all_data_layers=True, depsgraph=dg)
    old = obj.data
    obj.modifiers.clear()
    obj.data = me
    if old.users == 0:
        bpy.data.meshes.remove(old)
    return obj


def auto_smooth(obj, angle=40.0):
    """Shade smooth + mark edges sharper than `angle` as sharp (Blender 4.1+ auto smooth)."""
    me = obj.data
    bm = bmesh.new()
    bm.from_mesh(me)
    lim = math.radians(angle)
    for f in bm.faces:
        f.smooth = True
    for e in bm.edges:
        if len(e.link_faces) == 2:
            same_mat = e.link_faces[0].material_index == e.link_faces[1].material_index
            e.smooth = same_mat and e.calc_face_angle(0.0) <= lim
        else:
            e.smooth = False
    bm.to_mesh(me)
    bm.free()
    me.update()


def flat(obj):
    for p in obj.data.polygons:
        p.use_smooth = False


def join(objs, name=None):
    """Join mesh objects into objs[0] (no bpy.ops) keeping materials."""
    target = objs[0]
    bpy.context.view_layer.update()
    bm = bmesh.new()
    mats = []
    for o in objs:
        me = o.data.copy()
        me.transform(o.matrix_world)
        remap = []
        for m in me.materials:
            if m not in mats:
                mats.append(m)
            remap.append(mats.index(m))
        for p in me.polygons:
            p.material_index = remap[p.material_index] if remap else 0
        bm.from_mesh(me)
        bpy.data.meshes.remove(me)
    me = bpy.data.meshes.new(name or target.name)
    bm.to_mesh(me)
    bm.free()
    for m in mats:
        me.materials.append(m)
    keep_name = name or target.name
    for o in objs:
        old = o.data
        bpy.data.objects.remove(o)
        if old.users == 0:
            bpy.data.meshes.remove(old)
    obj = link(bpy.data.objects.new(keep_name, me))
    return obj


def tri_count(obj):
    return sum(len(p.vertices) - 2 for p in obj.data.polygons)


def scene_tris():
    return sum(tri_count(o) for o in bpy.context.scene.objects if o.type == "MESH")


# --------------------------------------------------------------------------- export
def write_js_fallback(glb_path):
    key = os.path.splitext(os.path.basename(glb_path))[0]
    with open(glb_path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("ascii")
    with open(glb_path + ".js", "w") as f:
        f.write("window.NB_MODEL_DATA=window.NB_MODEL_DATA||{};window.NB_MODEL_DATA.%s='%s';" % (key, b64))


def export_glb(name, animations=False, objects=None, texcoords=False, morph=False):
    os.makedirs(MODELS, exist_ok=True)
    path = os.path.join(MODELS, name + ".glb")
    for o in bpy.context.scene.objects:
        o.select_set(objects is None or o in objects)
    kw = dict(
        filepath=path,
        export_format="GLB",
        export_yup=True,
        export_apply=True,
        export_texcoords=texcoords,          # UVs only for textured assets (humans)
        export_image_format="AUTO",
        export_normals=True,
        export_materials="EXPORT",
        export_cameras=False,
        export_lights=False,
        use_selection=objects is not None,
        export_animations=animations,
    )
    if animations:
        kw.update(export_animation_mode="ACTIONS", export_force_sampling=True,
                  export_frame_step=1, export_optimize_animation_size=True,
                  export_anim_slide_to_zero=True, export_skins=True,
                  export_def_bones=True, export_all_influences=False)
    if morph:   # shape keys -> named morph targets (+ normals), sparse accessors (only the moved vertices)
        kw.update(export_morph=True, export_morph_normal=True, export_morph_tangent=False,
                  export_try_sparse_sk=True, export_try_omit_sparse_sk=False, export_morph_animation=False,
                  export_apply=False)   # the armature is the only modifier (applying would drop the keys)
    bpy.ops.export_scene.gltf(**kw)
    if morph:
        compact_morph_targets(path)
    write_js_fallback(path)
    print("[nb] wrote %s (%.1f KB, %d tris)" % (path, os.path.getsize(path) / 1024, scene_tris()))
    return path


# --------------------------------------------------------------------------- morph targets
def _glb_read(path):
    import json
    import struct
    with open(path, "rb") as f:
        b = f.read()
    jn = struct.unpack_from("<I", b, 12)[0]
    js = json.loads(b[20:20 + jn])
    off = 20 + jn
    bn = struct.unpack_from("<I", b, off)[0]
    return js, b[off + 8:off + 8 + bn]


def _glb_write(path, js, bin_):
    import json
    import struct
    jb = json.dumps(js, separators=(",", ":")).encode()
    jb += b" " * (-len(jb) % 4)
    bin_ += b"\0" * (-len(bin_) % 4)
    total = 12 + 8 + len(jb) + 8 + len(bin_)
    with open(path, "wb") as f:
        f.write(struct.pack("<4sII", b"glTF", 2, total))
        f.write(struct.pack("<I4s", len(jb), b"JSON") + jb)
        f.write(struct.pack("<I4s", len(bin_), b"BIN\0") + bin_)


def compact_morph_targets(path, pos_eps=5e-5, nrm_eps=0.015):
    """Rewrite the morph targets of a .glb so that they stay small:
    - deltas below pos_eps (m) / nrm_eps are zeroed (the exporter leaves float noise on every normal
      of every primitive), then every target is a sparse accessor holding only the moved vertices;
    - POSITION deltas stay float32 (three.js r128 Box3 / bounding spheres read them raw);
    - NORMAL deltas become normalized int8 (KHR_mesh_quantization, ~0.5 deg; only the shader
      reads them, as floats in -1..1);
    - targets of a primitive that do not move (shirt, trousers...) share one empty accessor, and all
      sparse indices / values live in two buffer views (less JSON)."""
    import numpy as np
    js, bin_ = _glb_read(path)
    views, accs = js["bufferViews"], js["accessors"]
    ctype = {5126: np.float32, 5125: np.uint32, 5123: np.uint16, 5122: np.int16, 5121: np.uint8, 5120: np.int8}
    norm_div = {5120: 127.0, 5121: 255.0, 5122: 32767.0, 5123: 65535.0}

    def view_bytes(i):
        v = views[i]
        o = v.get("byteOffset", 0)
        return bin_[o:o + v["byteLength"]]

    def decode(a):
        n = a["count"]
        out = np.zeros((n, 3), np.float32)
        div = norm_div.get(a["componentType"], 1.0) if a.get("normalized") else 1.0
        if "bufferView" in a:
            raw = np.frombuffer(view_bytes(a["bufferView"]), ctype[a["componentType"]], n * 3, a.get("byteOffset", 0))
            out = raw.reshape(n, 3).astype(np.float32) / div
        if "sparse" in a:
            sp = a["sparse"]
            idx = np.frombuffer(view_bytes(sp["indices"]["bufferView"]), ctype[sp["indices"]["componentType"]],
                                sp["count"], sp["indices"].get("byteOffset", 0))
            val = np.frombuffer(view_bytes(sp["values"]["bufferView"]), ctype[a["componentType"]], sp["count"] * 3,
                                sp["values"].get("byteOffset", 0)).reshape(-1, 3)
            out[idx.astype(np.int64)] = val.astype(np.float32) / div
        return out
    old_acc = set()
    new_accs = list(accs)            # morph accessors are re-created at the end of the list
    idx_blob, val_blob = bytearray(), bytearray()
    plan = []
    for m in js["meshes"]:
        for pr in m["primitives"]:
            empty = None
            for t in pr.get("targets", []):
                for key in list(t):
                    ai = t[key]
                    old_acc.add(ai)
                    a = accs[ai]
                    d = decode(a)
                    eps = pos_eps if key == "POSITION" else nrm_eps
                    keep = np.where(np.linalg.norm(d, axis=1) >= eps)[0]
                    if not len(keep):
                        if empty is None:
                            idx_blob.extend(b"\0" * (-len(idx_blob) % 4))
                            val_blob.extend(b"\0" * (-len(val_blob) % 4))
                            empty = len(new_accs)
                            new_accs.append({"componentType": 5126, "count": a["count"], "type": "VEC3",
                                             "min": [0.0, 0.0, 0.0], "max": [0.0, 0.0, 0.0],
                                             "sparse": {"count": 1, "indices": {"bufferView": "I", "byteOffset": len(idx_blob),
                                                                                 "componentType": 5121},
                                                        "values": {"bufferView": "V", "byteOffset": len(val_blob)}}})
                            idx_blob.extend(b"\0")
                            val_blob.extend(b"\0" * 12)
                        t[key] = empty
                        continue
                    it, idt = (5121, np.uint8) if keep[-1] < 256 else ((5123, np.uint16) if keep[-1] < 65536
                                                                       else (5125, np.uint32))
                    vals = d[keep]
                    na = {"count": a["count"], "type": "VEC3"}
                    if key == "POSITION":
                        full = np.zeros((a["count"], 3), np.float32)
                        full[keep] = vals
                        na.update(componentType=5126, min=full.min(0).tolist(), max=full.max(0).tolist())
                        vb = vals.astype(np.float32).tobytes()
                    else:
                        na.update(componentType=5120, normalized=True)
                        vb = np.clip(np.round(vals * 127.0), -127, 127).astype(np.int8).tobytes()
                    idx_blob.extend(b"\0" * (-len(idx_blob) % 4))
                    val_blob.extend(b"\0" * (-len(val_blob) % 4))
                    na["sparse"] = {"count": int(len(keep)),
                                    "indices": {"bufferView": "I", "byteOffset": len(idx_blob), "componentType": it},
                                    "values": {"bufferView": "V", "byteOffset": len(val_blob)}}
                    idx_blob.extend(keep.astype(idt).tobytes())
                    val_blob.extend(vb)
                    t[key] = len(new_accs)
                    new_accs.append(na)
                    plan.append(key)
    # drop the old morph accessors, renumber every accessor reference
    keep_ids = [i for i in range(len(new_accs)) if i not in old_acc]
    amap = {o: n for n, o in enumerate(keep_ids)}
    js["accessors"] = accs = [new_accs[i] for i in keep_ids]
    for m in js["meshes"]:
        for pr in m["primitives"]:
            pr["attributes"] = {k: amap[v] for k, v in pr["attributes"].items()}
            if "indices" in pr:
                pr["indices"] = amap[pr["indices"]]
            for t in pr.get("targets", []):
                for k in t:
                    t[k] = amap[t[k]]
    for an in js.get("animations", []):
        for smp in an["samplers"]:
            smp["input"], smp["output"] = amap[smp["input"]], amap[smp["output"]]
    for sk in js.get("skins", []):
        if "inverseBindMatrices" in sk:
            sk["inverseBindMatrices"] = amap[sk["inverseBindMatrices"]]
    # rebuild the binary chunk: the views still referenced, then the two sparse views
    used = {a["bufferView"] for a in accs if isinstance(a.get("bufferView"), int)}
    for a in accs:
        sp = a.get("sparse")
        if sp and isinstance(sp["indices"]["bufferView"], int):
            used |= {sp["indices"]["bufferView"], sp["values"]["bufferView"]}
    used |= {im["bufferView"] for im in js.get("images", []) if "bufferView" in im}
    out, nviews, remap = bytearray(), [], {}

    def add_view(data, src=None):
        out.extend(b"\0" * (-len(out) % 4))
        v = {"buffer": 0, "byteOffset": len(out), "byteLength": len(data)}
        for k in ("target", "byteStride"):
            if src and k in src:
                v[k] = src[k]
        out.extend(data)
        nviews.append(v)
        return len(nviews) - 1
    for i, v in enumerate(views):
        if i in used:
            remap[i] = add_view(view_bytes(i), v)
    vi, vv = add_view(bytes(idx_blob)), add_view(bytes(val_blob))
    for a in accs:
        if isinstance(a.get("bufferView"), int):
            a["bufferView"] = remap[a["bufferView"]]
        sp = a.get("sparse")
        if sp:
            for part, new in (("indices", vi), ("values", vv)):
                b = sp[part]["bufferView"]
                sp[part]["bufferView"] = new if b in ("I", "V") else remap[b]
    for im in js.get("images", []):
        if "bufferView" in im:
            im["bufferView"] = remap[im["bufferView"]]
    js["bufferViews"] = nviews
    out.extend(b"\0" * (-len(out) % 4))
    js["buffers"] = [{"byteLength": len(out)}]
    for k in ("extensionsUsed", "extensionsRequired"):
        js[k] = sorted(set(js.get(k, [])) | {"KHR_mesh_quantization"})
    _glb_write(path, js, bytes(out))
    print("[nb] morph targets: %d sparse accessors, %.1f KB" % (len(plan), (len(idx_blob) + len(val_blob)) / 1024))
