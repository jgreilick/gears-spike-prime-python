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
4. **Wheel-option workaround applied:** `wheelMaxAcceleration: 20` (lowered to 2 in §12), `wheelStopActionHoldForce: 30000`, `wheelTireDownwardsForce: -4000`.
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

## 10. Castle Crasher playground (`spike/castle-crasher-world.json`)

A Gears custom world laid out like VEXcode VR's Castle Crasher. It uses no source changes and no VEX assets.
`spike/castle-crasher/build_world.py` (needs Pillow) generates it. The floor PNG and the pyramid roof glTF are
both drawn by the script and embedded as `data:` URLs, so the 25 KB JSON loads from anywhere.
Load it with World → Load from file, and load `spike/vr-robot.json` as the robot.

| File | Purpose |
|---|---|
| `castle-crasher/build_world.py` | Generates the world. Layout, sizes and physics constants are at the top. |
| `castle-crasher/01_center_castle.py` | Checks the start pose, then `drive_for` 800 mm into the centre castle and backs off. |
| `castle-crasher/02_corner_castles.py` | Gyro+GPS navigation that reaches and rams all four corner castles in one run, staying clear of the centre. |
| `castle-crasher/03_border.py` | The down eye sees the red band at the field edge; driving on falls off the table. |
| `castle-crasher/check_castles.js` | Console snippet that reports, per castle, pieces moved and roofs knocked down. |
| `castle-crasher/preview-*.png` | Renders: start view, top-down, and after the centre crash. |

### Coordinates

- **Ground:** 230 × 230 cm, centred on the origin. That's a 460 px image at `imageScale: 5`, since ground size comes from the image (§8).
  The white field is ±100 cm (2000 mm), with a 15 cm red band outside it.
- **GPS matches VEX:** GPS × 10 = VEX mm, with +Y away from the start and +X to the robot's right.
- **Start:** `startPosXYZStr: "0, -81, 0"`. The body centre sits 1 cm behind the axle, and the GPS is over the axle (the VR "centre turning point"), so it reads **(0, −800) mm**. Facing +Y.
- **Scale check:** the start is 800 mm from the centre castle and the robot's front is about 85 mm ahead of the GPS, so contact comes after about 565 mm. A `drive_for(800)` hits the castle and shoves about 235 mm into it, as VEX's first challenge expects.

### Castles: 21 loose pieces, each its own physics body

| Castle | Centre (mm) | Pieces | Build (cm) |
|---|---|---|---|
| Centre | (0, 0) | 10 | 2 base halves 15×30×20 (the seam visible in the 3D view), 4 towers 10×10×10, 4 roofs 13 wide × 9 tall |
| Top-left | (−765, 750) | 5 | one base slab 30×30×8, 4 roofs 13.5 × 8 (the dark "cross" seen from above) |
| Top-right | (755, 730) | 2 | block 13×13×11, roof 13 × 8 |
| Bottom-left | (−765, −730) | 2 | block 13×13×11, roof 13 × 8 |
| Bottom-right | (730, −745) | 2 | block 24×24×12, roof 24 × 15 |

- Centres and footprints come from the two top-down screenshots, which agree to about ±20 mm. Heights come from the 3D view, so they are estimates.
- Physics: `mass = 0.002 × volume`, so a base half is 18 against the robot's 1400. Friction is 0.3 and restitution 0.05.
  - I tuned these in the sim. At density 0.02 and friction 0.6, the robot pushed the whole centre castle 22 cm as one piece and knocked nothing off.
  - Ammo multiplies the two bodies' frictions, so block-on-block is 0.09 and block-on-floor is 0.3. The pushed base shoots out from under the towers.
- All stacks are stable at rest: less than 0.5 mm of settling over 3 s.

### Border

- **No walls, on purpose (`wall: false`).** In the VEX 3D view (screenshot 3, zoomed) the red edge is a flat stripe flush with the floor, with empty grey void beyond and no wall face.
- 03 confirms the down eye reads red right at y = −1000 mm, and the robot falls off at the outer edge (altitude −51 mm at y = −1243).

### Test results (2026-10-03, `vr-robot.json`, built-in browser)

| Test | Result |
|---|---|
| Start pose | GPS (0, −800) mm, heading 0. Passed on every run. |
| 01 `drive_for` 800 | Bumpers hit and the robot travels 789–797 mm. **The centre castle broke on 3/3 runs:** 1–2 of 4 roofs knocked off and 5–10 of 10 pieces displaced. No other castle moved. |
| 02 corners | **All four reached on 2/2 runs.** Top-right, bottom-left and bottom-right are flattened (roof off); top-left loses 2/4 roofs. The centre is untouched. Takes about 32 s. |
| 03 border | Floor is white at the start, red is seen at the edge, and the robot falls off. |

### What doesn't match

1. **There is no pyramid primitive.** Custom-world objects are only box, cylinder, sphere and model.
   - Roofs are `model` objects pointing at a generated glTF (`data:{json}`), which Babylon 4.2's glTF loader direct-loads.
   - **Physically each roof is a box.** Gears gives models a box impostor the size of their bounding box, so roofs tumble like cubes, and the laser/ultrasonic hit an invisible box around the pyramid.
2. **Compound objects exist but can't topple apart.** `type: "compound"` parents its children to the first object, which makes one rigid body. Loose stacked objects are the only way to get blocks that fall separately.
3. **The centre castle breaks but doesn't flatten.** Gears' VR robot is low (bumpers about 3 cm up), so it can only push the base, which slides; it can't tip a 20 cm block.
   - Towers fall when the base is shoved out from under them. Usually 1–2 roofs come off and the far half stays standing.
   - That resembles VEX's own post-crash view (screenshot 1, where half the centre castle is still up), but it is weaker than "everything falls".
   - The impact also deflects the robot 30–110 mm to the left.
   - Ammo is not deterministic across runs: one setting gave 2, 1 and 1 roofs.
4. **Python can't see world objects.** Robot.js's `ObjectTracker` looks meshes up by `objectTrackerLabel`, which a custom world can't set; only the football world sets it.
   - So the tests check reach with bumpers and GPS, and topples with `check_castles.js`.
   - A VEX-style "castles crashed" counter would need a source change, either labels from world JSON or a world-side scorer.
5. **Look:**
   - Blocks are dark grey, as in the top-down and thumbnail screenshots. VEX's current 3D view shows them light grey.
   - That 3D view also shows a green cone at the bottom-right where the top-down views show a yellow pyramid. I followed the top-down views.
   - The red band's width differs between screenshots: wide in screenshot 1, a hairline in screenshot 4. I used 150 mm, outside the 2000 mm field.
6. **Automation gotcha:**
   - The render loop only runs while the Simulator tab is active (`babylon.js:205`). Driving the page from JS needs `$('#navSim').click()` before anything moves.
   - The hidden-pane render pump (§8) is also needed. `engine` isn't global; use `babylon.engine`.

## 11. MVP shim and starter ZIP (`spike/vex.py`, `spike/vexsim.py`, `dist/vex-starter.zip`)

### Files

| File | Purpose |
|---|---|
| `spike/vex.py` | V5 Python subset over `simPython`. Prints `vex shim v0.1`. `__all__` keeps internals and `SimNotAvailable` out of `import *` (Skulpt 0.11 honours `__all__`); tests import `SimNotAvailable` explicitly. |
| `spike/vexsim.py` | VR-style `Pen` (`move`, `set_pen_color`, `set_pen_width`, `set_pen_color_rgb`; `fill` raises). Prints `vexsim v0.1`. |
| `spike/starter/main.py` | VEXcode-style config block, then `set_drive_velocity`/`set_turn_velocity(50, PERCENT)` and `drive_for(FORWARD, 800, MM, 50, PERCENT)`. Every velocity names its units. |
| `spike/build_starter.py` | Builds `dist/vex-starter.zip` with fixed timestamps: `python spike/build_starter.py`. |

### Port map and geometry (as shipped)

| V5 | Device | Gears |
|---|---|---|
| `Ports.PORT1` | left drive motor | outA |
| `Ports.PORT10` | right drive motor (mounted mirrored, so VEXcode's `reverse=True` drives forward) | outB |
| `Ports.PORT3` | Inertial | in1 (GyroSensor) |
| `Ports.PORT4` | Distance | in5 (LaserRangeSensor) |
| `three_wire_port.a` / `.b` | left / right Bumper | in3 / in4 |
| (vexsim) | Pen | in8 |

- Starter geometry: `SmartDrive(..., 157.08, 120, 50.8, MM, 1)`. That is wheelTravel = π × 50 mm, track 120 mm (§8 estimate) and VEX VR's published 50.8 mm wheelbase. Gears has no rear axle, so the shim stores `wheelBase` but doesn't use it.
- Constructing a device on an empty port raises `SimNotAvailable("Nothing is plugged into PORT7 on the sim robot.")`. A wrong device type gives "PORT3 on the sim robot is an Inertial, not a Motor."

### Project ZIP: answer

- **Layout:** Gears' Export writes `gearsBlocks.xml`, every tab (`*.py`), `gearsRobot.json` (`robot.options`) and `meta.json` (`{name, pythonModified}`).
- **Import** (`main.js` `loadZipFromComputer`):
  - It first deletes all tabs.
  - It reads `meta.json`, then `gearsBlocks.xml` if present, then `gearsRobot.json` (via `loadRobot`), then every name ending in `.py`. `gearsPython.py` is renamed to `main.py`.
  - Any other file is ignored.
- **`pythonModified: true` is required.** Otherwise Blockly keeps ownership of `main.py`.
- **The world never rides in the ZIP.** We ship `castle-crasher.json` at the ZIP root for students to extract. Import ignores it, as verified below.
- **Setup is two steps:** (1) Worlds → Load from file with the extracted `castle-crasher.json`; (2) File → Import zip package. Loading the robot during step 2 doesn't reset the world.

`dist/vex-starter.zip` contents (no `gearsBlocks.xml`):

| Entry | Source |
|---|---|
| `meta.json` | `{"name": "vex-starter", "pythonModified": true}` |
| `main.py` | `spike/starter/main.py` |
| `vex.py`, `vexsim.py` | `spike/` |
| `gearsRobot.json` | `spike/vr-robot.json` |
| `castle-crasher.json` | `spike/castle-crasher-world.json` |

### Public-site round trip (2026-10-04, gears.aposteriori.com.sg, built-in browser; v0.1 ZIP, repeated for the current ZIP in §12)

| Step | Result |
|---|---|
| ZIP bytes in the page | SHA-256 `5eb9c55364edfdb0…`, the same as the built file |
| 1. Worlds → Load from file (`castle-crasher.json` extracted from the ZIP with JSZip) | World `custom`, 21 objects, no error modal or JS error |
| 2. File → Import zip package | Tabs `main.py`, `vex.py`, `vexsim.py`; robot `vexVRRobot` with all 9 components; project name `vex-starter`; world unchanged; no error from the extra JSON |
| 3. Run button | Console `vex shim v0.1 / Calibrating`, no errors, 5.4 s. **Centre castle: 10/10 pieces moved, 2/4 roofs down. Other castles untouched.** The robot travelled 792 mm. |

The local copy gave the same centre-castle result (10/10 moved, 2/4 roofs down).

**Harness notes (automation only, not student-facing):**
- **Pane blocks public→localhost requests.** The built-in browser blocks fetches from the public site to localhost (`ERR_BLOCKED_BY_CLIENT`), even with CORS headers.
  - The ZIP went in as base64 instead, checked per 1 KB chunk with SHA-256. Hand-pasting was wrong once and was caught by the hash.
- **File pickers.** The site opens them by dispatching `click` on a detached `<input type=file>`.
  - The harness stubbed only that click, then set `input.files` with a `DataTransfer` and fired `change`.
  - Everything after that is the site's own handler, reached from the real menu items.
- **Frozen physics.** The pane can stop running `requestAnimationFrame` while `document.hidden` is still `false`. Physics freezes, and the first Run "finished" with the robot never moving.
  - The pump from §8 has to trigger on stalled rAF frames, not on `document.hidden`.

### Behaviour decisions

- **PERCENT is a share of the sim cap.** 100% = 800°/s. RPM and `VelocityUnits.DPS` are absolute and clamp at 800°/s, with a one-time console note. `GearSetting` is accepted and stored but changes nothing.
- **Position moves end in HOLD.** `spin_for`, `drive_for`, open-loop `turn_for` and SmartDrive turns hold until wheel speed is under 5°/s (300 ms max), then apply the user's stopping mode.
  - Stopping straight into BRAKE let the wheel coast: 360° became 434°. HOLD stops at about 369°. SmartDrive turns at first ended in BRAKE and overshot (180° → 191°); since §12 they hold too.
- **Position moves slow down near the target** (added in §12). While `wait=True` polls, each wheel's speed is capped at `sqrt(2 × 2000°/s² × remaining)`, with a 60°/s floor. Without this, a 100% move hit HOLD at 800°/s and the robot pitched forward: the laser read the floor (264 mm against 605 mm expected).
- **Velocity in position moves is a magnitude.** In `spin_for`, `drive_for` and `turn_for`, direction comes from `direction × sign(value)`, and a negative velocity doesn't flip it. PROS calls this argument the "maximum allowable velocity" for relative and absolute moves. In `spin`, `drive` and `turn`, a negative velocity reverses, as PROS `move_velocity` does. The V5 docs say neither.
- **`is_done()` grace period.** The wheel's `state` only updates on the next physics frame, so `is_done()` counts a motor as busy for 60 ms after a position command.
- **SmartDrive turns with `wait=False` raise `SimNotAvailable`.** The closed loop needs the caller's thread.
- **`brain.screen.print` writes immediately with `end=''`,** and `next_row()` writes the newline. Gears' console appends raw text, so nothing is lost if a program never calls `next_row()`.
- **Distance with no object.** Anything beyond the documented 2000 mm range, including the sim's 3000 mm "no hit", returns **9999 mm** (or 9999/25.4 = 393.66 in INCHES). `is_object_detected()` is then False.
  - Source: PROS distance docs, "Will return 9999 if the sensor can not detect an object". That reads the same firmware value VEXcode does. api.vex.com gives only the 20–2000 mm range.
  - Below 20 mm, the sim value passes through.
- **Skulpt 0.11 quirks hit while building:**
  - A nested function with `*args, **kwargs` can't see its enclosing scope ("Undefined variable"); unsupported methods use a callable object instead.
  - Lambdas in a module-level tuple hit the same error.
  - `dir()` without arguments isn't supported.

### V5 doc discrepancies (api.vex.com, read 2026-10-04)

- **Gear ratio names.** The Motor constructor page lists `GearSetting.RATIO_1_1` (default), `RATIO_2_1` and `RATIO_3_1`, but the Drivetrain page's examples use `GearSetting.RATIO_18_1`. The shim follows the Drivetrain page and real VEXcode: `RATIO_36_1`, `RATIO_18_1` (default) and `RATIO_6_1`.
- **Velocity units default to RPM, not PERCENT.** In `spin`, `spin_for`, `set_velocity`, `drive*`, `turn*` and `set_*_velocity`, a bare `set_velocity(50)` means 50 rpm, which is 300°/s in the sim. The starting velocity is still 50%.
- **Rotation unit names.** The docs write `RotationUnits.TURNS`; the VEXcode stub has `RotationUnits.REV`. The shim provides both, as the same object.
- **`brain.screen.print` separators differ.** Its `sep` defaults to `""`, while `print_at` and Controller `print` default to `" "`.
- **`drive_for` and `spin_for` return values aren't documented.** The shim returns `True` when the move completed and `False` on timeout or `wait=False`.
- **No-object Distance value isn't documented** on api.vex.com (Python, C++ or Blocks pages). The shim uses PROS's 9999 mm (see Behaviour decisions).
- **Negative velocity in position moves isn't documented.** The shim follows PROS (see Behaviour decisions).
- **Power-on defaults match the docs.** Motors and drivetrains start at 50% drive and turn velocity, and stopping defaults to BRAKE. The shim already did this.

## 12. Test suite, demo measurements and demos (2026-10-04, public site)

Everything below ran on **gears.aposteriori.com.sg**, loaded the way a student loads it:
- **World:** Worlds → Load from file.
- **Tabs:** File → Import zip package.
- **Each test:** pasted into `main.py`, then Reset, then Run.

**Source files.** The page fetched them from GitHub raw at commit `4c9363e`, and each matched the committed blob's SHA-256.

**Harness (`spike/tests/harness.js`), automation-only.** It runs the same handlers as the UI. Three extra pieces are needed only because the automation pane throttles itself:
- **Frame pump.** Runs Babylon's frame (`beginFrame`/render loops/`endFrame`) when `requestAnimationFrame` stalls.
  - Without `beginFrame`, `deltaTime` stays at 0. Wheels ramp speed by `delta × acceleration`, so they never move. That's how `t_motorgroup` "hung" at first.
- **Short timers.** `setTimeout` under 1 s, which drives Python `sleep`, fires from the same message loop while rAF is stalled.
- **Time limit.** It resets `Sk.execStart` the way Gears' own 2 s `setInterval` does, because a throttled `setInterval` let Skulpt raise `TimeLimitError` after 5 s.

**Worlds.**
- **Test world** (`spike/tests/vex-test-world.json`, generated by `build_test_world.py`): an open 5 × 5 m floor with no arena walls. One red wall's near face is at Y = +400 mm. The robot starts at (0, −1500) mm facing it.
- **Castle Crasher** is §10's world.
- **The VR robot now uses `wheelMaxAcceleration: 2`** (2000°/s², 0 → 800°/s in 0.4 s). At 20, a 100% `drive_for(300 mm)` turned the wheels exactly 688° but GPS showed 253–273 mm, because the wheels spun on launch. At 2, it measures 297–305 mm. `vr-robot-styled.json` was regenerated to match.

### Test results

Tests are in `spike/tests/t_*.py`, with helpers in `vextest.py`. Each prints `PASS|FAIL name measured expected tol` and a `SUMMARY` line. Ground truth comes from `simPython` (GPS `in2`, gyro `in1`, raw wheel `outA`), never from the shim.

| Test | Public site | Checks |
|---|---|---|
| t_constants | 28/28 | Enum identity and aliases, PORT1–21, GearSetting, `__all__` (no private names, no `SimNotAvailable`), version 0.1 |
| t_wait_timer | 7/7 | `wait` MSEC/SECONDS/default, `brain.timer` time/clear, `Timer()` |
| t_screen | 8/8 | `sep` (default ""), `precision` (default 2), `next_row`, `new_line`, `clear_screen`, captured from the shim's own writes |
| t_motor_spin_for | 14/14 | DEGREES/TURNS, `spin_to_position`, set/reset position, `wait=False` + `is_done`/`is_spinning`, return values, `set_timeout` stops early |
| t_motor_signs | 56/56 | `spin_for`: FORWARD/REVERSE × ±value × ±velocity × reversed (16 cases; checks the shim position and the raw wheel). `spin`: direction × ±velocity × reversed (8 cases) |
| t_motor_velocity_units | 14/15, then 15/15 | One check failed on the first run: `RPM_200_clamped_dps` measured 697 against 800 ± 80. It passed on the rerun (812). The sibling 800°/s checks passed in all three runs (791/784, then 813/805). Counted as harness timing jitter. The clamp note printed exactly once. |
| t_motorgroup | 10/10 | `count`, `spin_for` drives forward 155 mm, both motors move, `wait=False` |
| t_drive_for | 13/13 | 500 mm, REVERSE, INCHES, negative distance, 100%, `wait=False`, `drive` velocity readback (GPS-checked) |
| t_turn_for_open | 7/7 | Direction and approximate size (±20°): RIGHT/LEFT/TURNS/negative angle, `turn` |
| t_smartdrive_turn | 8/8 | ±3°: RIGHT/LEFT 90, 180 at 30%, 0.5 TURNS, threshold 5; `wait=False` raises |
| t_turn_to_heading | 11/11 | Shortest direction, negative heading, `turn_to_rotation` 450/360/1.5 TURNS, `set_heading` |
| t_bumper | 8/8 | Released at start; a square hit presses both; released after backing off; a 25° hit presses left only |
| t_distance | 11/11 | Far wall (1823 mm), mid, near (~165 mm, ±15), INCHES, default units; nothing in range → 9999 / 393.66 in, `is_object_detected` False |
| t_inertial | 16/16 | Clockwise positive, wrap to 330, negative rotation, `set_heading`/`set_rotation`/resets, TURNS |
| t_unsupported | 72/72 | Every stubbed method and class raises `SimNotAvailable` with its exact message |
| t_unmapped_port | 29/29 | Motor on each unused PORT, Distance/Inertial on an empty port, 3-wire c–h, wrong device type, non-port argument |
| t_pen | 17/17 | UP/DOWN, all colours and widths, RGB at opacity 100, bad arguments raise ValueError |

All 17 tests also passed on the local copy.

**Quirk found:** `simPython.Pen.isDown()` returns a raw JS boolean. Comparing it (`==`, `is`, `type()`) silently ends the program with no error. `not raw.isDown()` gives a real `bool`.

### Demo measurements (5 independent runs each, Reset between runs, 50% velocity)

| Measurement | Runs | Mean | Worst |
|---|---|---|---|
| `drive_for(FORWARD, 800, MM)`: distance error | +6.4, +0.1, +4.2, +9.4, +2.6 mm | +4.5 mm | +9.4 mm |
| …lateral drift | 11.2, −18.4, 8.1, −7.1, −6.5 mm | 10.3 mm (abs) | 18.4 mm |
| Open-loop `DriveTrain.turn_for(RIGHT, 90)`: heading error | −8.2, −4.2, −5.7, −7.1, −9.3° | −6.9° | −9.3° |
| `SmartDrive.turn_for(RIGHT, 90)`: heading error | −0.25, −0.41, −0.48, −0.36, −0.64° | −0.43° | −0.64° |
| 4 × (300 mm, right 90) open-loop: final heading error | −38.0, −28.1, −34.7, −26.5, −30.1° | −31.5° | −38.0° |
| …final distance from start | 120, 94, 138, 103, 118 mm | 115 mm | 138 mm |
| 4 × (300 mm, right 90) SmartDrive: final heading error | −0.7, −1.4, −4.4, +5.1, −0.9° | 2.5° (abs) | 5.1° |
| …final distance from start | 33, 23, 29, 35, 10 mm | 26 mm | 35 mm |
| Castle Crasher starter (`dist/vex-starter.zip`, Run × 5) | centre pieces moved: 10, 10, 10, 10, 10; roofs down: 2, 2, 2, 2, 2 | 10/10, 2/4 roofs | same every run |
| …other castles | 0 pieces moved on every run | untouched | untouched |

- **Open-loop turns.** They come in about 7° short with 120 mm track width and turn-in-place scrub. The square's heading error (−31°) is more than 4 × 7°, because the drives add heading drift too.
- **SmartDrive squares.** Each turn lands within its 1° threshold, but SmartDrive `drive_for` doesn't hold heading, so drift from the drives remains.

### Starter ZIP round trip, current build

`dist/vex-starter.zip` SHA-256 `6df720e0d918d69b…`. It's built by `build_starter.py` and is byte-identical across rebuilds.
- Pasted base64 matched all 15 chunk hashes.
- World extracted from the ZIP: 21 objects.
- Import gave tabs `main.py`, `vex.py`, `vexsim.py`, robot `vexVRRobot` (`wheelMaxAcceleration` 2), and project `vex-starter`. The extra JSON caused no error.
- Run × 5: as in the table above, no console errors, 5.7–5.8 s each.

### Demos (`spike/demo/`, public site)

Each demo is the starter's config block plus an explicit-units body.

| Demo | World | Result |
|---|---|---|
| d1_crash | Castle Crasher | "Crashed!"; centre castle 10/10 moved, 2/4 roofs down |
| d2_distance | Castle Crasher | Start 573 mm, stopped at 140 mm (30% and 20 ms polling overshoot the 150 mm line by 10 mm) |
| d3_bumper | `spike/vr-test-world.json` (walled) | 3 bumps in 20 s: back up 200 mm and turn right each time |
| d4_open_vs_smart | Castle Crasher | Open-loop −25.7°, SmartDrive +3.0° (local copy: −18.7° / +3.6°) |
| d5_pen_square | Castle Crasher | One continuous blue trace, a visible square (the corner doesn't quite close) |

**The d4 gap is easy to see.** About 26° against 3° in one run, and about 31° against 2.5° on average in the 5-run measurement, so it needs no variant.
