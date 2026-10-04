"""Generate spike/castle-crasher-world.json, a Gears custom world that mimics
VEXcode VR's Castle Crasher playground. Needs Pillow.

    python spike/castle-crasher/build_world.py

Everything is embedded as data: URLs (floor PNG, pyramid glTF), so the JSON
loads from anywhere. Gears units are cm; VEX coordinates are mm = GPS x 10.
JSON object positions are [x, y, z] with y = forward (+Y VEX) and z = up.
"""
import base64, io, json, math, os, struct
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, '..', 'castle-crasher-world.json')

FIELD = 200.0          # playable white area, cm (VEX: 2000 x 2000 mm)
BORDER = 15.0          # red band outside the field, cm (screenshot 1)
PX_PER_CM = 2          # floor image resolution
BLOCK_COLOR = '#4D4D4D'
ROOF_COLOR = (1.0, 0.8, 0.0)
# Tuned in the sim: blocks are light next to the robot (body 1000, wheels 200 each) and
# slippery, so a push shoves the base out from under the towers instead of sliding the
# whole castle as one piece. Ammo multiplies frictions: block-block 0.09, block-floor 0.3.
DENSITY = 0.002        # mass per cm^3
FRICTION = 0.3


def floor_png():
    total = FIELD + 2 * BORDER
    n = int(total * PX_PER_CM)
    b = int(BORDER * PX_PER_CM)
    im = Image.new('RGB', (n, n), (224, 32, 32))
    im.paste((255, 255, 255), (b, b, n - b, n - b))
    buf = io.BytesIO()
    im.save(buf, 'PNG', optimize=True)
    return 'data:image/png;base64,' + base64.b64encode(buf.getvalue()).decode(), 10.0 / PX_PER_CM


def pyramid_gltf(base, height, rgb):
    """Square pyramid, base centred on the origin at y=0, flat-shaded."""
    h = base / 2
    c = [(-h, 0, -h), (h, 0, -h), (h, 0, h), (-h, 0, h)]
    apex = (0, height, 0)
    tris = [(c[i], c[(i + 1) % 4], apex) for i in range(4)] + [(c[0], c[1], c[2]), (c[0], c[2], c[3])]

    def sub(a, b): return [a[i] - b[i] for i in range(3)]
    def cross(a, b): return [a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0]]

    pos, nor = [], []
    for k, (a, b, cc) in enumerate(tris):
        n = cross(sub(b, a), sub(cc, a))
        centroid = [(a[i] + b[i] + cc[i]) / 3 for i in range(3)]
        outward = [0, -1, 0] if k >= 4 else [centroid[0], 0, centroid[2]]
        if sum(n[i] * outward[i] for i in range(3)) < 0:   # make winding CCW from outside
            b, cc = cc, b
            n = [-v for v in n]
        L = math.sqrt(sum(v * v for v in n))
        for v in (a, b, cc):
            pos.extend(v)
            nor.extend(x / L for x in n)
    blob = struct.pack('<%df' % len(pos), *pos) + struct.pack('<%df' % len(nor), *nor)
    count = len(pos) // 3
    gltf = {
        'asset': {'version': '2.0', 'generator': 'gears castle-crasher build_world.py'},
        'scene': 0,
        'scenes': [{'nodes': [0]}],
        'nodes': [{'mesh': 0, 'name': 'roof'}],
        'meshes': [{'primitives': [{'attributes': {'POSITION': 0, 'NORMAL': 1}, 'material': 0}]}],
        'materials': [{'pbrMetallicRoughness': {'baseColorFactor': list(rgb) + [1],
                                                'metallicFactor': 0, 'roughnessFactor': 0.9},
                       'doubleSided': True}],
        'buffers': [{'byteLength': len(blob),
                     'uri': 'data:application/octet-stream;base64,' + base64.b64encode(blob).decode()}],
        'bufferViews': [{'buffer': 0, 'byteOffset': 0, 'byteLength': count * 12},
                        {'buffer': 0, 'byteOffset': count * 12, 'byteLength': count * 12}],
        'accessors': [
            {'bufferView': 0, 'componentType': 5126, 'count': count, 'type': 'VEC3',
             'min': [-h, 0, -h], 'max': [h, height, h]},
            {'bufferView': 1, 'componentType': 5126, 'count': count, 'type': 'VEC3'},
        ],
    }
    return 'data:' + json.dumps(gltf, separators=(',', ':'))


def physics(volume):
    return {'mass': round(volume * DENSITY, 2), 'friction': FRICTION, 'restitution': 0.05,
            'dampLinear': 0, 'dampAngular': 0, 'group': 1, 'mask': -1}


def block(x, y, z0, sx, sy, sz):
    """Box resting with its bottom at height z0. Returns (object, top height)."""
    return {'type': 'box', 'position': [x, y, z0 + sz / 2], 'size': [sx, sy, sz],
            'color': BLOCK_COLOR, 'physicsOptions': physics(sx * sy * sz)}, z0 + sz


def roof(x, y, z0, base, height):
    # Gears models get a box impostor of their bounding box, so physically this is a box.
    return {'type': 'model', 'modelURL': pyramid_gltf(base, height, ROOF_COLOR), 'modelScale': 1,
            'position': [x, y, z0 + height / 2],
            'physicsOptions': physics(base * base * height / 3)}


def castle_center(cx, cy):
    """Two base halves (the seam in the 3D view), four towers with roofs."""
    objs = []
    for sx in (-1, 1):
        o, top = block(cx + sx * 7.5, cy, 0, 15, 30, 20)
        objs.append(o)
    for sx in (-1, 1):
        for sy in (-1, 1):
            o, t = block(cx + sx * 7.5, cy + sy * 7.5, top, 10, 10, 10)
            objs += [o, roof(cx + sx * 7.5, cy + sy * 7.5, t, 13, 9)]
    return objs


def castle_quad(cx, cy):
    """One low base slab with four roofs; the base shows as a cross from above."""
    o, top = block(cx, cy, 0, 30, 30, 8)
    objs = [o]
    for sx in (-1, 1):
        for sy in (-1, 1):
            objs.append(roof(cx + sx * 8.25, cy + sy * 8.25, top, 13.5, 8))
    return objs


def castle_single(cx, cy, size, height, roof_h):
    o, top = block(cx, cy, 0, size, size, height)
    return [o, roof(cx, cy, top, size, roof_h)]


def main():
    floor, scale = floor_png()
    # Castle centres in cm, measured from the top-down screenshots (+-2 cm).
    castles = [
        ('center', castle_center(0, 0)),
        ('top-left', castle_quad(-76.5, 75)),
        ('top-right', castle_single(75.5, 73, 13, 11, 8)),
        ('bottom-left', castle_single(-76.5, -73, 13, 11, 8)),
        ('bottom-right', castle_single(73, -74.5, 24, 12, 15)),
    ]
    objects = []
    for _, objs in castles:
        objects += objs
    world = {
        'worldName': 'custom',
        'options': {
            'imageURL': floor,
            'groundType': 'box',
            'uScale': 1, 'vScale': 1,
            'imageScale': scale,
            'timer': 'none',
            'wall': False,
            'startPos': 'center',
            # Body centre 1 cm behind the axle, so the GPS (over the axle) reads (0, -80) cm.
            'startPosXYZStr': '0, -81, 0',
            'startRotStr': '0',
            'objects': objects,
        },
    }
    with open(OUT, 'w') as f:
        json.dump(world, f, indent=1)
    counts = ', '.join('%s %d' % (n, len(o)) for n, o in castles)
    print('wrote %s (%d objects: %s), %d bytes' % (os.path.normpath(OUT), len(objects), counts, os.path.getsize(OUT)))


if __name__ == '__main__':
    main()
