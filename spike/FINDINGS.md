# Spike findings: VEX V5 Python shim (`vex.py`) for Gears

Branch `spike/vex-shim`. No existing source files were modified. Spike artifacts:
`spike/FINDINGS.md`, `spike/Dockerfile`, `spike/Dockerfile.dockerignore`, `spike/Caddyfile`,
and `spike/probe/vex_probe.py` (a throwaway stub, not the shim).

**Verdict: build it.** Ship it as a bundled module and prototype it as a user tab
(see §5). Building on `simPython` directly, the shim is about 2 weeks of work for one
developer. The main limits are simulator fidelity and robot scale, not Skulpt.

## 0. Repo state (where it differs from the brief)

- **There are no SPIKE Prime leftovers to clean up.** `HEAD`, `origin/master` and `upstream/master` are all `20b8e87`.
  `git diff upstream/master --stat` is empty, and `git status --ignored` is clean. There is nothing to list.
- **`spike/probe/` did not exist** in this checkout or in any branch history. This spike takes the brief's
  probe results as given, without the scripts. `spike/probe/vex_probe.py` is new and was written by this spike.

## 1. Architecture (confirmed from source)

**How modules load (`public/js/skulpt.js`):**
- **Library list:** `externalLibs` maps Skulpt lookup paths (`'./pkg/mod.py'`) to URLs with `?v=<md5-8>` cache-busters.
  `false` means an empty `__init__.py`.
- **Preload:** `preload()` fetches every library at page load into `preloadedLibs`.
- **Lookup order in `builtinRead`:**
  1. User tabs (`filesManager.files`, after stripping `./`).
  2. Skulpt stdlib.
  3. `preloadedLibs`.
  4. An on-demand fetch.
- **Bug in the on-demand fetch (`skulpt.js:124`):** it uses bare `externalLibs`, not `self.externalLibs`.
  So an import that races ahead of preload throws a `ReferenceError`. This is upstream, harmless in practice, and worth a one-line PR.

**How a bundled `vex` would be registered:**
- Add `public/vex.py` (or `public/vex/__init__.py`).
- Add one line to `externalLibs`: `'./vex.py': 'vex.py?v=xxxxxxxx'`.
- `updateVersion.py` already rewrites `?v=` hashes inside `js/*.js`, so it maintains the new entry too.

**How user tabs shadow bundled modules:**
- Tabs are checked first, for any path, so a tab named `vex.py` wins over a bundled `./vex.py`.
- **Verified in the browser:** I registered a "bundled" `./vex.py` at runtime and imported it. I then added a `vex.py` tab
  and imported again. The second run reported `user-tab`.
- This works both ways. It's handy for development, but a stale student tab will silently override a fixed bundled module.

**The bridge:**
- `simPython.js` is a Skulpt JS module exposing ev3dev sysfs-style objects:
  - `Motor(port)` with `speed_sp`, `position_sp`, `time_sp`, `stop_action`, `polarity`, `position`, `speed` and `state`,
    plus `command('run-forever'|'run-timed'|'run-to-rel-pos'|'run-to-abs-pos'|'stop')`.
  - One sensor class per type, each looked up by port string.
- `outA`/`outB` are hard-wired to the drive wheels. Every other port goes through `robot.getComponentByPort`.

**Layering:**
- **ev3dev2** (≈1,700 lines) and **Pybricks** (≈580 lines) are *independent* pure-Python wrappers over `simPython`.
  Neither is built on the other.
- Pybricks blocking moves are a polling loop: send a command, then `sleep(0.01)` until `state` is no longer `running`.
  Every sensor read sleeps 1 ms so tight loops yield.

**Which foundation: `simPython` directly.**
- VEX semantics map 1:1 onto `speed_sp`/`position_sp`/`command`: `wait=`, timeouts, gear cartridges, percent of cartridge RPM.
- Both wrappers carry EV3 assumptions the shim would have to undo:
  - ev3dev2 sets `max_speed = 1050`.
  - Pybricks sets `_MAX_SPEED = 1600`, and its `DriveBase` ramps with encoder dead-reckoning.
- What to copy instead: Pybricks' ~15-line `_wait` pattern and its `SENSOR_DELAY` habit.

**Bonus finding: tight loops will freeze the tab.** Skulpt only yields on `sleep`. Gears resets `Sk.execStart` every 2 s,
so a student's `while True: if bumper.pressing(): ...` would hang the tab. **Every shim getter must `time.sleep(0.001)`**
(Pybricks does exactly this).

## 2. API gap table

**Status key:** **D** direct · **C** needs conversion in the shim · **M** missing (stub, approximate, or raise).
Gears units are cm and degrees. VEX defaults: velocity 50%, drive distance in INCHES, `wait()` in MSEC.

| VEX item | Gears equivalent | Status | Notes |
|---|---|---|---|
| `Ports.PORT1..21` | `'outA'..'outZ'` (motors), `'in1'..` (sensors) | C | VEX has one port namespace; Gears has two, auto-assigned in tree order. The shim needs a port map (see Risks). |
| `brain.three_wire_port.a..h` | `'inN'` | C | Same port map. |
| `brain.screen.print` | `print()` → sim console | C | Use `end=''` and emit a newline on `next_row()`. `set_cursor` and `clear_screen` can only be approximated (no LCD widget). Docs disagree on the default `sep`. |
| `brain.timer.time/clear/value` | `time.time()` | D | Offset on `clear()`. `value()` returns seconds; `time()` returns MSEC by default. |
| `wait(t, units=MSEC)` | `time.sleep` | C | Convert units only. Sleep accuracy is confirmed. |
| `Motor(port, gears, reversed)` | `simPython.Motor(port)` + `polarity('inversed')` | C | Cartridge sets max RPM: 36:1 → 100 (600°/s), 18:1 → 200 (1200°/s), 6:1 → 600 (3600°/s). **Sim drive wheels cap at 800°/s** (`Wheel.js:26`). Arm and swivel actuators are uncapped. |
| `spin(dir, vel, units)` | `speed_sp` + `run-forever` | C | Convert PERCENT/RPM/DPS → °/s. |
| `spin_for(dir, val, DEGREES/TURNS, …, wait=True)` | `position_sp` + `run-to-rel-pos`, then poll `state` | C | **Probed:** 360° at 400°/s took 0.89–0.93 s and blocked correctly. It overshot by 6–9°, because the sim stops after passing the target. Timed `spin_for` maps to `run-timed`. |
| `spin_to_position` | `run-to-abs-pos` | C | Same overshoot. |
| `stop(mode)` / `set_stopping` | `stop_action` + `command('stop')` | D | BRAKE/COAST/HOLD → `'brake'/'coast'/'hold'`. VEX default is BRAKE. HOLD on drive wheels may be ineffective (see Risks). |
| `set_velocity` | shim state | C | Default 50%. |
| `position(units)` / `reset_position` / `set_position` | `position()` / `position(v)` | D | Convert DEGREES or TURNS. |
| `velocity(units)` | `speed()` | C | °/s → RPM or %. |
| `is_done` / `is_spinning` | `state()` | C | `'running'`/`'ramping'` mean busy. Add a shim-side `set_timeout`. |
| `set_max_torque`, `current`, `torque`, `temperature`, `power`, `efficiency`, `installed` | none | M | Return plausible constants. |
| `MotorGroup(*motors)` | list of Motors | C | Readings come from the first motor. `is_done` means all motors are done. `current()` sums. |
| `DriveTrain(l, r, wheelTravel=300, trackWidth=320, wheelBase=320, MM, ratio)` | two Motors | C | Keyword names are camelCase. Distance comes from `wheelTravel`, which the **student** supplies. The sim robot must be configured to match (§3). |
| `drive` / `drive_for` (INCHES default) / `stop` / `set_drive_velocity` / `set_turn_velocity` | encoder targets on outA/outB | C | `drive_for` uses `run-to-rel-pos` on both wheels and returns a bool when `wait=True`. |
| `turn` / `turn_for` (no gyro) | open-loop from `trackWidth` | C | **Probed** on the default robot (5.6 cm wheels, 15.2 cm track): asking 90° gave **104–106°**; asking 180° gave **188–190°** (gyro-measured). This matches real VEX, where gyro-less turns are also inaccurate. |
| `SmartDrive(..., gyro, ...)`: `turn_for`, `turn_to_heading`, `heading`, `rotation`, `set_heading` | `GyroSensor` closed loop | C | Write a P-controller on yaw with `set_turn_threshold` (1°). **Probed:** a right turn reads positive, which matches VEX (clockwise positive). |
| `Bumper(3-wire).pressing()` | `TouchSensor.isPressed()` | D | Only the port map is needed. `pressed`/`released` callbacks are out of scope. |
| `Distance.object_distance(MM)` | `UltrasonicSensor` / `LaserRangeSensor` `.dist()` (cm) | C | Multiply by 10. Clamp to 20–2000 mm and return a large value when nothing is seen. |
| `Distance.is_object_detected` | `dist()` < max | C | Threshold on range. |
| `Distance.object_size` / `object_velocity` | none | M | Velocity could be derived from successive reads. Size: return `NONE` or `MEDIUM`. |
| `Inertial.heading` / `rotation` | `GyroSensor.yawAngleAndRate()[0]` (accumulating °) | C | `heading = yaw % 360`, `rotation = yaw - offset`. |
| `Inertial.calibrate` / `is_calibrating` | none | C | No-op that returns `False` immediately. |
| `Inertial.set_heading`, `reset_*` | offset in shim | C | Same pattern as Pybricks `reset_angle`. |
| `Inertial.orientation(PITCH/ROLL/YAW)` | `pitch`/`roll`/`yawAngleAndRate` | C | |
| `Inertial.gyro_rate` | yaw rate | C | Yaw axis only is cleanest. |
| `Inertial.acceleration` | none | M | |
| `Optical.hue` / `brightness` | `ColorSensor.valueHSV()` (H 0–360, V 0–100) | C | Near-direct. |
| `Optical.color()` | hue bands → `Color.*` | C | Apply VEX's documented hue bands, not Gears' LEGO palette. |
| `Optical.is_near_object` / `set_light` | none | M | `set_light` is a no-op. `is_near_object` could use RGB above zero (the sensor has a max range). |
| `Rotation(port)` | none | M | No passive-encoder component exists. Possible approximation: read a motor's `position()` on a passive axle. Simplest is to omit it. |
| `Gps.x_position/y_position(MM)` | `GPSSensor.position()` → (x, y, alt) in **cm, world frame** | C | Multiply by 10. Origin and extent depend on the world, not a ±1800 mm field centre; worlds would need to be centred. |
| `Gps.heading` | none on `GPSSensor` | C/M | Borrow from a gyro if one is present, otherwise missing. |
| `Gps.quality` | none | M | Return 100. |
| Constants (`FORWARD`…`HOLD`, `Color.*`, `GearSetting`, `Ports`) | none | C | Pure Python enums with identity-checkable instances, e.g. `DirectionType(0,'FORWARD')`. The probes confirm class-attribute enums work. `DPS` is also module-level. |

## 3. Robot approximation

| Parameter | Configurable? | Where | Notes |
|---|---|---|---|
| Wheel diameter | Yes | Configurator slider (1–10 cm); `wheelDiameter` | VEX 4" wheels are 10.16 cm, just past the slider. Set it in JSON; the clamp only applies to the slider (untested). |
| Track width | Indirectly | Derived: `bodyWidth + wheelWidth + 2*wheelToBodyOffset` | Default is 15.2 cm. For a 295 mm track, set `bodyWidth` ≈ 28.3. |
| Body size and mass | Yes | `bodyWidth/Length/Height`, `bodyMass` (UI) | `wheelMass` and `wheelFriction` are JSON-only. |
| Wheel position | Yes | `bodyEdgeToWheelCenterY/Z`, `wheelToBodyOffset` | |
| Caster | Yes | `caster`, `casterDiameter`, `casterOffsetZ` | |
| Motor speed / cartridge | **No** | Hard-coded 800°/s on drive wheels (`Wheel.js:26`) | 36:1 (600°/s) fits under the cap. 18:1 is capped at 67% of 1200°/s. 6:1 cannot be represented. The shim must clamp, or scale percent to the sim cap. |
| Acceleration, hold force | JSON-only (`wheelMaxAcceleration`, `wheelStopActionHoldForce`) | `Robot.js:241-243` | **Bug (upstream, not tested at runtime):** unset values are passed as `undefined` and override the Wheel defaults. Ramping becomes `NaN` (wheels jump straight to target speed) and HOLD force is `undefined`. |
| Extra mechanism motors | Yes | Arm, Swivel, Linear, Wheel, OmniWheel, Magnet, Paintball actuators | Ports are auto-assigned `outC`, `outD`, … in component-tree order. Each takes the same `Motor` command set. Arm/swivel have no speed clamp; Linear uses `degreesPerCm`. |
| Sensor ports | Auto | `in1`, `in2`, … in tree order | Types: Color, Ultrasonic, LaserRange, Lidar, Gyro, GPS, Touch, Camera (and Pen). There is no cap on sensor count; motors stop at 26. |
| Save / load | Yes | Configurator "Save/Load to file" (JSON) | A "VEX clawbot-ish" template can ship as a JSON file with no source change. Example: `public/WRO-2025-Future-Engineer-Obstacle.json`. |

**Scale is a concern.** A V5 robot is roughly 30–45 cm, but Gears worlds (line following, WRO mats) are sized for 15 cm EV3 bots.
A full-size VEX robot will feel cramped. Test on the Grid world or a custom world.

## 4. Hosting

- **Fully static.** `public/` loads only relative, self-hosted assets: no CDN, no analytics, no service worker, and no root-absolute paths.
  - `updateVersion.py` is an optional cache-bust rewrite run before commit, not a build step. The site serves unchanged without it.
  - `public/` is 215 MB, mostly models, textures and Blockly versions.
- **Smoke test:**
  - `python -m http.server` from `public/`: all 83 requests returned 200/304 with no console errors. A bundled-module load and a full simulated run worked.
  - **The Docker image was not built.** Docker Desktop's daemon wasn't running. To verify: `docker build -f spike/Dockerfile -t gears .`.
- **Things to watch behind Caddy on a subdomain:**
  - **Saved programs are per origin.** They live in `localStorage` keyed to the origin, so student code saved on `gears.aposteriori.com.sg` won't appear on your subdomain. Export/import still works.
  - **`.wasm` MIME type.** It must be `application/wasm`; Caddy does this by default and the spike Caddyfile also pins it.
  - **`.htaccess`** files are Apache-only and ignored by Caddy (they stop Apache executing `.py`). The Caddyfile serves `.py` as `text/plain`.
  - **`privacy.html`** names the upstream domain; edit it if you publish under your own.
  - **Caching:** HTML should revalidate and `?v=` assets can cache for a long time. The Caddyfile sets `no-cache` on HTML only.
  - The arena iframes and `genURL.html` use relative URLs and `location.href`, so they're fine on any host or path.
- **Dockerfile:**
  - The image is `caddy:2-alpine` + `public/` + `spike/Caddyfile`, serving plain HTTP on :80. The edge Caddy does TLS and runs `reverse_proxy gears:80`.
  - `spike/Dockerfile.dockerignore` keeps the build context down to `public/` and the Caddyfile.

## 5. Recommendation: bundled module, developed as a user tab

| | User-tab shim | Bundled module |
|---|---|---|
| Source changes | None | One line in `skulpt.js` plus a new file (upstream-friendly) |
| Student setup | Each student adds a `vex.py` tab (localStorage, per browser) | `from vex import *` just works |
| Updates | Every copy goes stale; no way to push fixes | Deploy once; `?v=` busts caches |
| Tamper and confusion | Students see, edit and break it; it clutters the tabs | Invisible. It can still be shadowed deliberately for debugging |
| Dev loop | Edit in the browser, run instantly | Edit the file, reload |
| Hosted-site use | Works on upstream gears.aposteriori.com.sg | Only on your deployment (or if upstream accepts a PR) |

**Recommendation:** develop the shim as a user tab (fast iteration, zero deploy), then ship it as `public/vex.py` with the `externalLibs` line.
- **Fallback:** keep a paste-in `vex.py` for anyone using the upstream site.
- **Robot:** distribute the starter robot as a configurator JSON, not as an edit to `robotTemplates.js`.
- **Upstream PR (optional):** worth offering the bundled module upstream later. The one-line registration and the `skulpt.js:124` fix make an easy PR.

## 6. Risks

1. **Port mapping is a design decision, not a lookup.** VEX `PORT1–21` is one namespace; Gears splits motors and sensors and numbers them by tree order.
   - Proposal: a default map (drive pair → outA/outB, then mechanism motors in order; sensors by type) plus `vex.configure_ports({...})` for overrides.
   - Errors must name both the VEX and the Gears port.
2. **Fidelity: position moves overshoot by 6–9°, and encoder turns by 5–18%.**
   - Mitigation: teach SmartDrive plus Inertial, which is good practice on real V5 anyway.
   - Possible shim-side correction: slow the approach near the target, as Pybricks `DriveBase` does.
3. **Speed cap.** 800°/s is below an 18:1 cartridge at full speed (1200°/s) and far below 6:1. Programs tuned on real robots will run at different speeds.
4. **The upstream wheel-option `undefined` bug.** It probably disables ramping and weakens HOLD on drive wheels; I reasoned this from code and did not test it.
   - Workaround: set `wheelMaxAcceleration: 20`, `wheelStopActionHoldForce: 30000` and `wheelTireDownwardsForce: -4000` in the robot JSON.
5. **Freezing loops.** Every shim read must yield (see §1).
6. **Hidden-tab throttling.** The simulator's physics runs on `requestAnimationFrame`, so it pauses when its tab is hidden. I hit this while testing.
   - Students won't notice, but automated or headless tests will need a manual render pump.
7. **API doc ambiguity.** api.vex.com is behind Cloudflare, so the reference was taken from the official pages via WebFetch summaries and from a VEXcode `vex` stub (DishPy SDK mirror).
   - Points to check against a real VEXcode install: the default `sep` in `screen.print`, the `Gps` `heading_offset` argument, and the exact default program template.
8. **Skulpt edge cases.** Zero-arg `super()` inside nested classes fails, so the shim should use explicit `super(Cls, self)` everywhere. Tracebacks show shim internals, so the shim should raise friendly errors at the API boundary.

## 7. Rough build estimate (one developer)

| Work item | Estimate |
|---|---|
| Enums/constants, `Brain` (screen, timer), `wait`, unit conversions, port map | 1.5 d |
| `Motor`, `MotorGroup` (wait/timeout/is_done, cartridge scaling) | 2 d |
| `DriveTrain` + `SmartDrive` (gyro P-turn, `turn_to_heading`) | 2 d |
| Sensors (Bumper, Distance, Inertial, Optical, GPS; stubs for missing ones) | 1.5 d |
| Robot JSON template(s) and a VEX-scaled test world, if needed | 1 d |
| Test programs (VEXcode samples, autonomous only), fidelity tuning | 2 d |
| Bundling, docs/cheat-sheet for students | 1 d |
| **Total** | **≈ 11 days (2–2.5 weeks)** |

Expected size is 700–1,000 lines of Python.

## 8. VEXcode VR "Standard VR Robot" as a Gears robot (`spike/vr-robot.json`)

A configurator JSON with no source changes. Load it with Robot → Load from file. Supporting files:
- `spike/vr-test-world.json`: a red wall, a green floor patch, and a magnetic disc.
- `spike/vr-tests/01–09_*.py`: one program per component, using `simPython` directly (the layer the shim will build on).

**All nine tests pass** in the sim (2026-10-03, desktop app's built-in browser).

**Sources:**
- VEX KB "Understanding Robot Features in VEXcode VR" (returns 403 to WebFetch, but loads in a real browser).
- VEX KB "Using the Distance Sensor in VEXcode VR with Python".
- `api.vex.com/vr/home/robots/vr_robot.html` fetched fine but lists only the components, with no numbers.

### What VEX actually says, and the "50.8 mm wide" mistake

- **Wheels are 50 mm.**
- **Length is 133 mm.**
- **50.8 mm is the *wheelbase*,** "the distance between the center of the front wheel and the center of the back wheel". It is **not the width**. A 50.8 mm-wide robot with 133 mm length would be implausibly narrow.
- **No width or track width is published.**
- Other published facts:
  - Encoders are 360°/rev.
  - The gyro is built into the drivetrain, with clockwise positive.
  - The Location sensor reads from the "center turning point".
  - The Distance sensor is a laser with a "very narrow field of view" and detects up to 3000 mm.
  - The eyes report object presence and colour (red/green/blue/none). The front eye also reports distance.
  - No eye range is published.

### Answers

1. **Can a ColorSensor face forward? Yes.**
   - Its camera looks along local +Z, so `rotation: [0,0,0]` faces forward and `[π/2,0,0]` faces down.
   - Upstream already does this: the `maze2` template has a forward ColorSensor with `sensorMaxRange: 30, sensorFov: 0.524`, and I copied those values for the front eye.
   - Verified: the front eye reads black (16,16,16) with nothing within 30 cm, and red (h=0, s=100) near the wall.
   - Limitation: `ColorSensor` has no distance reading. The shim's `front_eye` distance/`near_object` should come from the laser instead (same direction, same front face).
2. **LaserRange matches the narrow beam; Ultrasonic does not.**
   - LaserRange casts **1 ray**. Ultrasonic casts **21 rays** in a fan about ±21° wide and capped at 255 cm.
   - Measured with each sensor at the same mount, wall face 38 cm ahead, turning in place:

     | Turn | LaserRange | Ultrasonic |
     |---|---|---|
     | 0° | 29.3 cm | 29.1 cm |
     | 40° | 57.4 cm (misses the wall corner, hits the arena wall) | 33.2 cm (still sees the corner) |
     | 55° | 52.7 cm | 44.4 cm |

   - The JSON sets `rayLength: 300` to match VEX's 3000 mm.
   - Read the laser through `simPython.UltrasonicSensor(port).dist()`. There is no separate LaserRange binding; that class accepts both types.
3. **Dimensions:**
   - Wheel diameter is **5.0 cm**, per VEX; it fits the 1–10 cm slider.
   - Length is **13.3 cm**.
   - **Track width is 12.0 cm.** This is my estimate: `bodyWidth 10 + wheelWidth 1.6 + 2×0.2`. VEX publishes no width, so it is unverified, and the shim's `trackWidth` default should match whatever is chosen here.
   - Gears has one drive axle plus a rear caster, so VEX's 4-wheel 50.8 mm wheelbase cannot be modelled.
   - **The axle sits 1 cm ahead of body centre** (`bodyEdgeToWheelCenterZ 5.65`), so the centre of mass rests on the caster instead of tipping forward.
   - The GPS sits over the axle (the turning centre). Measured: 0.5 cm drift after a 360° spin.
   - One wheel revolution drives 15.7–16.0 cm (expected 15.71).
   - A closed-loop 90° right turn reads +89 to +90°.
4. **Wheel-option workaround applied:** `wheelMaxAcceleration: 20`, `wheelStopActionHoldForce: 30000`, `wheelTireDownwardsForce: -4000`.
   - This **confirms §6 risk 4 at runtime.** Without these keys the wheel gets `maxAcceleration = undefined`, `stopActionHoldForce = undefined` and a tire downforce of **0**.
   - Ramping is disabled. Commanded speed reads 800 on the first 20 ms sample, versus 350 → 718 → 800 with the fix.
   - Flat-ground driving still passes either way. I did not measure how much HOLD resistance is lost.
5. **Ports** (tree order = JSON order; sensors `in1…`, motors `outC…` after the drive pair):

   | Port | Component | Pose (x right, y up, z forward; cm, body-relative) | VEX VR name |
   |---|---|---|---|
   | outA / outB | Left / right drive wheel | axle at z = +1 | `drivetrain` |
   | in1 | GyroSensor | [0, 2.5, −3] | drivetrain heading/rotation |
   | in2 | GPSSensor | [0, 2.5, 1] (over the axle) | `location` |
   | in3 | TouchSensor, 3×2, facing forward | [−3.5, −0.5, 7.65] | `left_bumper` |
   | in4 | TouchSensor, 3×2, facing forward | [3.5, −0.5, 7.65] | `right_bumper` |
   | in5 | LaserRangeSensor, facing forward | [0, 1, 7.4] (directly above the magnet) | `distance` |
   | in6 | ColorSensor, facing forward, 30 cm range | [0, 3, 5.65] | `front_eye` |
   | in7 | ColorSensor, facing down, 1 cm off the floor | [0, −1, 4.5] | `down_eye` |
   | in8 | Pen (trace at the turning centre) | [0, −0.9, 1] | `pen` |
   | outC | MagnetActuator | [0, −1.25, 7.65] | `magnet` |

   - **Pen consumes a sensor port (`in8`).** Any port map has to skip it.
   - Mount checks:
     - The bumper pads protrude to z = 9.45, ahead of the magnet face (8.65), so the bumpers touch first.
     - The laser ray starts flush with the magnet face, so readings measure from the robot's front.

### Test results (`spike/vr-tests/`)

| Test | Result |
|---|---|
| 01 drivetrain | 360° → 15.98 cm, 0.8 cm lateral drift |
| 02 gyro | right 90° reads +90.4 |
| 03 GPS | starts at (0, 1); 0.5 cm drift over a 360° spin |
| 04 bumpers | released at start; square hit presses both; released after backing off; a 25°-angled hit presses left only |
| 05 distance | 29.34 cm (expected 29.3); the beam clears the wall corner at 40° |
| 06 front eye | nothing at start, red near the wall |
| 07 down eye | white floor, then green (h=120) at the patch |
| 08 pen | down/up states correct; one trace mesh drawn |
| 09 magnet | disc carried from x = −30 back to x = −7.6 and lifted to 2 cm |

09 prints no PASS line because Python can't see world objects. I verified it from JS via the `isMagnetic` mesh position.

**How the tests were run.** I served the repo root (`python -m http.server` from the repo root, then `/public/index.html`). The page fetched `spike/` files and ran each through `skulpt.runPython` after `simPanel.resetSim()`, the same path as the Run button. Pasting each file into the Python tab and pressing Run is equivalent.

### Gotchas found along the way

- **Hidden-tab throttling (§6 risk 6) bit for real.** The browser pane went hidden mid-run, physics froze and `sleep` clamped to 1 s. That produced false bumper failures (a phantom press at start, no press on a wall hit).
  - Fix, in the page only and without source edits: a MessageChannel pump that calls `engine._activeRenderLoops` every 16 ms when `document.hidden`, plus routing `setTimeout` < 1 s through the same channel.
  - Any automated shim test suite needs this.
- **Raw GPS order.** `simPython.GPSSensor.position()` returns **(x, altitude, y)**. The §2 table's "(x, y, alt)" is the ev3dev2 wrapper's reordering.
- **World size comes from the floor image.** Custom-world `length`/`width` are ignored, and the default `custom.png` gives a 100 × 100 cm arena with walls at ±50.
- **Number formatting.** Skulpt's `'%d' % float` prints the full float, so the shim should `int()` or `round()` before formatting.
- **Scale suits the existing worlds.** At 13.3 cm long, the VR robot fits EV3-scale worlds, unlike the V5 concern in §3.

## 9. Styled VR robot (`spike/vr-robot-styled.json`)

A look-alike version, still JSON only. It is generated from `vr-robot.json` by `spike/vr-styled/build_styled.py` (needs Pillow), so the two never drift apart. Renders are in `spike/vr-styled/preview-{front,rear,side}.png`.

- **Body texture.** A 3×2 atlas (`imageType: "all"`) gives a grey frame with VEX-style holes and a dark top plate with an orange rim and "VEX VR". The logo reads from the front, as on the VR robot. The PNG is embedded as a `data:` URL (54 KB), so the JSON is one 80 KB file that loads from anywhere.
- **Atlas face mapping** (Babylon box, `Robot.js` faceUV), measured in the sim:
  - Faces 0–2 sit in the image's bottom half and 3–5 in the top half.
  - 0 = front: draw it rotated 180°.
  - 1 = back: as drawn.
  - 2 = right and 3 = left: draw with up = +y, then rotate 90° clockwise.
  - 4 = top: draw with up = robot front, then rotate 90° clockwise.
  - 5 = bottom.
- **Decorative blocks** (no ports, so the port table in §8 is unchanged):
  - Dummy rear wheels, 4.6 cm, 5.08 cm behind the axle (VEX's wheelbase). They sit 0.2 cm off the ground and never touch it.
  - Orange hub covers and fenders on all four wheels.
  - A white sensor tower with a black cap around the front eye.
- **Front eye inside the tower.** The eye's camera sits just inside the tower's front face. Babylon back-face culls that face in the sensor's render, so the eye still sees out. Test 06 still passes.
- **Other changes from the plain robot:**
  - `casterDiameter: 2` keeps the same ground contact but hides the caster under the body.
  - The gyro and GPS boxes moved inside the body. The GPS is still over the axle, so only its altitude reading changes (6.0 → 4.9).
- **Still not changeable without source edits:**
  - The Gears drive-wheel texture (hard-coded in `Wheel.js`).
  - The stock sensor models: the white touch bodies with red pads, the laser box and the magnet.
  - A real GLB body. Robots don't support `modelURL`, unlike world objects.
- **Tests.** All nine tests pass on both robots against the final `vr-test-world.json` (2026-10-03).
- **Screenshots while the pane is hidden.** The pane's screenshots go stale, so use `BABYLON.Tools.CreateScreenshotUsingRenderTargetAsync(engine, cameraArc, …)`. Set `cameraArc.target` directly; `setTarget()` recomputes alpha, beta and radius from the old position.
