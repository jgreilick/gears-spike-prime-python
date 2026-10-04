// Castle Crasher topple check. Paste into the browser console (sim page) after a run.
// Python can't see world objects, so this reads the meshes directly.
// A roof is down when it has dropped >= 3 cm or tilted > 30 degrees from where the
// world file placed it. A castle is "broken" when any roof is down, "flattened" when all are.
(function checkCastles() {
  const CASTLES = { center: [0, 0], 'top-left': [-76.5, 75], 'top-right': [75.5, 73],
                    'bottom-left': [-76.5, -73], 'bottom-right': [73, -74.5] };
  const objs = babylon.world.processedOptions.objects;
  const report = {};
  objs.forEach(function(o, i) {
    const id = 'worldBaseObject_' + (o.type == 'model' ? 'model' : o.type) + i;
    const mesh = babylon.scene.getMeshByID(id);
    if (!mesh) return;
    let name = null, best = Infinity;
    for (const k in CASTLES) {
      const d = Math.hypot(o.position[0] - CASTLES[k][0], o.position[1] - CASTLES[k][1]);
      if (d < best) { best = d; name = k; }
    }
    const up = BABYLON.Vector3.TransformNormal(BABYLON.Axis.Y, mesh.getWorldMatrix()).normalize();
    const tilt = Math.acos(Math.min(1, up.y)) * 180 / Math.PI;
    const drop = o.position[2] - mesh.absolutePosition.y;
    const moved = Math.hypot(mesh.absolutePosition.x - o.position[0], mesh.absolutePosition.z - o.position[1]);
    const r = report[name] = report[name] || { pieces: 0, moved: 0, roofs: 0, roofsDown: 0 };
    r.pieces++;
    if (moved > 2 || tilt > 10 || Math.abs(drop) > 2) r.moved++;
    if (o.type == 'model') {
      r.roofs++;
      if (drop >= 3 || tilt > 30) r.roofsDown++;
    }
  });
  for (const k in report) {
    report[k].broken = report[k].roofsDown > 0;
    report[k].flattened = report[k].roofsDown == report[k].roofs;
  }
  return report;
})();
