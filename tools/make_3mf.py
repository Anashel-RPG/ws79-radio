#!/usr/bin/env python3
"""Turn every STL in print/stl/ into a 3MF in print/3mf/ (millimetres, shared vertices). Standard library only.

    python3 tools/make_3mf.py
"""
import glob, os, struct, zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "..", "print", "stl")
DST = os.path.join(HERE, "..", "print", "3mf")

CONTENT_TYPES = """<?xml version="1.0" encoding="UTF-8"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/>
</Types>"""
RELS = """<?xml version="1.0" encoding="UTF-8"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Target="/3D/3dmodel.model" Id="rel0" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/>
</Relationships>"""


def read_stl(path):
    b = open(path, "rb").read()
    n = struct.unpack("<I", b[80:84])[0]
    if 84 + n * 50 == len(b):                                  # binary
        tris = []
        for i in range(n):
            o = 84 + i * 50 + 12
            tris.append([struct.unpack("<3f", b[o + k * 12:o + k * 12 + 12]) for k in range(3)])
        return tris
    tris, cur = [], []                                         # ascii
    for line in b.decode("ascii", "replace").splitlines():
        w = line.split()
        if w and w[0] == "vertex":
            cur.append(tuple(float(v) for v in w[1:4]))
            if len(cur) == 3:
                tris.append(cur); cur = []
    return tris


def write_3mf(tris, name, path):
    index, verts, faces = {}, [], []
    for t in tris:
        ids = []
        for v in t:
            key = tuple(round(c, 5) for c in v)
            if key not in index:
                index[key] = len(verts); verts.append(key)
            ids.append(index[key])
        if len(set(ids)) == 3:
            faces.append(ids)
    vx = "\n".join('          <vertex x="%g" y="%g" z="%g"/>' % v for v in verts)
    fx = "\n".join('          <triangle v1="%d" v2="%d" v3="%d"/>' % tuple(f) for f in faces)
    model = f"""<?xml version="1.0" encoding="UTF-8"?>
<model unit="millimeter" xml:lang="en-US" xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02">
  <metadata name="Title">{name}</metadata>
  <metadata name="Designer">The Black Watchmen / Division 79</metadata>
  <resources>
    <object id="1" type="model" name="{name}">
      <mesh>
        <vertices>
{vx}
        </vertices>
        <triangles>
{fx}
        </triangles>
      </mesh>
    </object>
  </resources>
  <build>
    <item objectid="1"/>
  </build>
</model>"""
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", CONTENT_TYPES)
        z.writestr("_rels/.rels", RELS)
        z.writestr("3D/3dmodel.model", model)
    return len(verts), len(faces)


if __name__ == "__main__":
    os.makedirs(DST, exist_ok=True)
    for f in sorted(glob.glob(os.path.join(SRC, "*.stl"))):
        name = os.path.splitext(os.path.basename(f))[0]
        nv, nf = write_3mf(read_stl(f), name, os.path.join(DST, name + ".3mf"))
        print("%-28s %6d vertices %6d triangles" % (name + ".3mf", nv, nf))
