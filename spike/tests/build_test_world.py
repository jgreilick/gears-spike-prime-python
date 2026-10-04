"""Generate spike/tests/vex-test-world.json: an open 5 x 5 m floor for the shim tests. Needs Pillow.

    python spike/tests/build_test_world.py

No arena walls, so the laser sees nothing when it faces away from the one wall (V5 range is
2000 mm; the floor edge is 2500 mm from the start and the sim ray is 3000 mm long).
Coordinates are cm; VEX mm = GPS cm x 10. The robot starts with the GPS at (0, -1500) mm
facing +Y; the red wall's near face is at Y = +400 mm, 1900 mm ahead.
"""
import base64, io, json, os
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'vex-test-world.json')

SIZE = 500             # floor, cm
PX_PER_CM = 1
GRID = 50              # grid spacing, cm
WALL_FACE_Y = 40.0     # cm
WALL_DEPTH = 4.0
WALL_WIDTH = 80.0
WALL_HEIGHT = 15.0


def floor_png():
    n = SIZE * PX_PER_CM
    im = Image.new('RGB', (n, n), (240, 240, 240))
    d = ImageDraw.Draw(im)
    for i in range(0, n + 1, GRID * PX_PER_CM):
        d.line([(i, 0), (i, n)], fill=(200, 200, 200))
        d.line([(0, i), (n, i)], fill=(200, 200, 200))
    buf = io.BytesIO()
    im.save(buf, 'PNG', optimize=True)
    return 'data:image/png;base64,' + base64.b64encode(buf.getvalue()).decode(), 10.0 / PX_PER_CM


def main():
    floor, scale = floor_png()
    wall = {'type': 'box', 'position': [0, WALL_FACE_Y + WALL_DEPTH / 2, WALL_HEIGHT / 2],
            'size': [WALL_WIDTH, WALL_DEPTH, WALL_HEIGHT], 'color': '#E60000', 'physicsOptions': 'fixed'}
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
            # Body centre is 1 cm behind the axle; the GPS sits over the axle.
            'startPosXYZStr': '0, -151, 0',
            'startRotStr': '0',
            'objects': [wall],
        },
    }
    with open(OUT, 'w') as f:
        json.dump(world, f, indent=1)
    print('wrote %s, %d bytes' % (os.path.normpath(OUT), os.path.getsize(OUT)))


if __name__ == '__main__':
    main()
