"""Build spike/vr-robot-styled.json from spike/vr-robot.json.

Adds a VEX VR-style body texture (embedded as a data: URL so the JSON stays a
single shareable file) and decorative Box/Cylinder blocks (rear dummy wheels,
orange hubs and fenders, a sensor tower). Sensor/actuator ports and poses are
unchanged except GPS/gyro, which are tucked inside the body.

Run from the repo root:  python spike/vr-styled/build_styled.py
Needs Pillow. Writes spike/vr-styled/body.png (for inspection) and the JSON.
"""
import base64, io, json, math, os

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
SPIKE = os.path.dirname(HERE)

PX = 40     # pixels per cm when drawing a face
CELL = 512  # atlas cell size; 3x2 cells for imageType 'all'

ORANGE = '#F7941D'
PLATE = '#3A3C40'
FRAME = '#5A5D61'
DARK = '#2B2C2E'
HOLE = '#1E1F21'

# Body box from vr-robot.json, in cm.
BW, BH, BL = 10.0, 4.0, 13.3


def font(size_px):
    for name in ('arialbd.ttf', 'Arial Bold.ttf', 'DejaVuSans-Bold.ttf'):
        try:
            return ImageFont.truetype(name, size_px)
        except OSError:
            pass
    return ImageFont.load_default()


def holes(d, x0, y0, x1, y1, pitch=1.27, r=0.16):
    """A row/grid of VEX-style holes inside the rectangle (cm)."""
    nx = max(1, int((x1 - x0) / pitch))
    ny = max(1, int((y1 - y0) / pitch))
    for i in range(nx + 1):
        for j in range(ny + 1):
            cx = x0 + i * (x1 - x0) / max(nx, 1)
            cy = y0 + j * (y1 - y0) / max(ny, 1)
            d.ellipse([(cx - r) * PX, (cy - r) * PX, (cx + r) * PX, (cy + r) * PX], fill=HOLE)


def face(w_cm, h_cm, bg):
    img = Image.new('RGB', (round(w_cm * PX), round(h_cm * PX)), bg)
    return img, ImageDraw.Draw(img)


def draw_top():
    """Seen from above; image up = robot front (+z), image right = robot right (+x)."""
    img, d = face(BW, BL, FRAME)
    holes(d, 0.45, 0.6, 0.45, BL - 0.6)              # left rail
    holes(d, BW - 0.45, 0.6, BW - 0.45, BL - 0.6)    # right rail
    holes(d, 1.6, 0.5, BW - 1.6, 0.5)                # front cross-member
    # Dark top plate with an orange rim, rear two-thirds of the body.
    x0, x1 = 1.0, BW - 1.0
    y0, y1 = 3.9, BL - 0.6
    d.rounded_rectangle([x0 * PX, y0 * PX, x1 * PX, y1 * PX], radius=0.8 * PX,
                        fill=ORANGE)
    rim = 0.35
    d.rounded_rectangle([(x0 + rim) * PX, (y0 + rim) * PX, (x1 - rim) * PX, (y1 - rim) * PX],
                        radius=0.6 * PX, fill=PLATE)
    # Logo text reads from the front, like the VR robot (upside down from behind).
    txt = Image.new('RGBA', (round((x1 - x0) * PX), round(2.2 * PX)), (0, 0, 0, 0))
    td = ImageDraw.Draw(txt)
    f = font(round(1.5 * PX))
    tw = td.textlength('VEX VR', font=f)
    td.text(((txt.width - tw) / 2, 0.15 * PX), 'VEX VR', font=f, fill='#E8E8E8')
    txt = txt.rotate(180)
    img.paste(txt, (round(x0 * PX), round(((y0 + y1) / 2 - 1.1) * PX)), txt)
    return img


def draw_side():
    """Seen from outside; up = +y. Symmetric front/back so it suits both sides."""
    img, d = face(BL, BH, DARK)
    d.rectangle([0, 0, BL * PX, 0.35 * PX], fill=ORANGE)
    holes(d, 0.8, 1.4, BL - 0.8, 1.4)
    return img


def draw_front():
    img, d = face(BW, BH, DARK)
    d.rectangle([0, 0, BW * PX, 0.35 * PX], fill=ORANGE)
    d.rectangle([2.0 * PX, 1.0 * PX, (BW - 2.0) * PX, 3.2 * PX], fill=FRAME)
    holes(d, 2.6, 2.1, BW - 2.6, 2.1)
    return img


def draw_back():
    img, d = face(BW, BH, DARK)
    d.rectangle([0, 0, BW * PX, 0.35 * PX], fill=ORANGE)
    holes(d, 1.2, 1.6, BW - 1.2, 1.6)
    d.rectangle([3.5 * PX, 2.4 * PX, (BW - 3.5) * PX, 3.4 * PX], fill=ORANGE)
    return img


def build_atlas():
    # Babylon box faces for imageType 'all' (Robot.js faceUV), measured in the sim:
    # 0 front (+z) needs 180 deg, 1 back as drawn, 2 right / 3 left / 4 top need 90 deg CW.
    faces = {
        0: draw_front().rotate(180),
        1: draw_back(),
        2: draw_side().rotate(-90, expand=True),
        3: draw_side().rotate(-90, expand=True),
        4: draw_top().rotate(-90, expand=True),
        5: face(BW, BL, DARK)[0],
    }
    atlas = Image.new('RGB', (CELL * 3, CELL * 2))
    for i, img in faces.items():
        # faceUV v 0..0.5 is the bottom half of the image (Babylon flips Y).
        x = (i % 3) * CELL
        y = CELL if i < 3 else 0
        atlas.paste(img.resize((CELL, CELL), Image.LANCZOS), (x, y))
    return atlas


def box(pos, w, h, d, color, rot=(0, 0, 0)):
    return {'type': 'Box', 'position': list(pos), 'rotation': list(rot),
            'options': {'width': w, 'height': h, 'depth': d, 'color': color.lstrip('#'),
                        'imageType': 'none', 'imageURL': ''}}


def cyl(pos, diameter, height, color, rot=(0, 0, math.pi / 2)):
    return {'type': 'Cylinder', 'position': list(pos), 'rotation': list(rot),
            'options': {'diameter': diameter, 'height': height, 'color': color.lstrip('#'),
                        'imageType': 'none', 'imageURL': ''}}


def main():
    with open(os.path.join(SPIKE, 'vr-robot.json')) as f:
        robot = json.load(f)

    atlas = build_atlas()
    atlas.save(os.path.join(HERE, 'body.png'), optimize=True)
    buf = io.BytesIO()
    atlas.save(buf, format='PNG', optimize=True)

    robot['name'] = 'vexVRRobotStyled'
    robot['shortDescription'] = 'VEXcode VR Standard Robot (styled approximation)'
    robot['imageType'] = 'all'
    robot['imageURL'] = 'data:image/png;base64,' + base64.b64encode(buf.getvalue()).decode()
    robot['casterDiameter'] = 2  # same contact point, but mostly hidden under the body

    by_type = {}
    for c in robot['components']:
        by_type.setdefault(c['type'], []).append(c)
    by_type['GyroSensor'][0]['position'] = [0, 0, -3]   # inside the body (pose-independent)
    by_type['GPSSensor'][0]['position'] = [0, 1.4, 1]   # still over the axle, now hidden

    # Body-relative cm: x right, y up, z forward. Body spans x +-5, y +-2, z +-6.65;
    # drive wheels are at x +-6, y -1, z +1 (r 2.5); the ground is at y -3.5.
    axle_z = 1.0
    rear_z = axle_z - 5.08          # VEX wheelbase 50.8 mm
    deco = []
    for sx in (-1, 1):
        # Dummy rear wheel, 0.2 cm off the ground so it never touches it.
        deco.append(cyl((sx * 6, -1, rear_z), 4.6, 1.6, '#333333'))
        for z in (axle_z, rear_z):
            deco.append(cyl((sx * 6.95, -1, z), 2.2, 0.3, ORANGE))            # hub cover
            deco.append(box((sx * 6, 1.85, z), 1.8, 0.5, 5.4, ORANGE))        # fender
    # Sensor tower: white body around the front eye, black cap. The eye camera sits just
    # inside the white box's front face, which is back-face culled, so it still sees out.
    deco.append(box((0, 3.2, 5.6), 2.4, 2.4, 3.2, '#E8E8E8'))
    deco.append(box((0, 5.0, 5.6), 2.6, 1.2, 3.4, '#111111'))
    robot['components'].extend(deco)

    out = os.path.join(SPIKE, 'vr-robot-styled.json')
    with open(out, 'w') as f:
        json.dump(robot, f, indent=2)
        f.write('\n')
    print('wrote %s (%d KB), texture %d KB' % (out, os.path.getsize(out) // 1024, len(buf.getvalue()) // 1024))


if __name__ == '__main__':
    main()
