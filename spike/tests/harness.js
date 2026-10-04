// Browser harness for the vex shim tests. Paste into the console of a Gears page, or eval it.
// It drives the page the way a student does: Worlds -> Load from file, File -> Import zip,
// paste a test into main.py, press Reset, press Run, read the console.
// Automation-only pieces (not needed by students):
//   - pump(): calls Babylon's render loop when requestAnimationFrame stalls (a hidden or
//     throttled automation pane freezes physics otherwise).
//   - stubFileDialog()/feed(): the site opens pickers by clicking a detached <input type=file>;
//     we skip only that native dialog, then hand the input a File and fire 'change' so the
//     site's own loader runs.
window.VT = (function() {
  const sleep = ms => new Promise(r => setTimeout(r, ms));
  const pending = [];

  function pump() {
    if (window._vtPump) return;
    window._vtPump = true;
    window._vtLastRaf = performance.now();
    window._vtPumped = 0;
    (function raf() { window._vtLastRaf = performance.now(); requestAnimationFrame(raf); })();
    const ch = new MessageChannel();
    let last = performance.now();
    ch.port1.onmessage = () => {
      const now = performance.now();
      if (now - window._vtLastRaf > 50 && now - last >= 16) {
        last = now;
        const engine = babylon.engine;
        engine.beginFrame();   // measures deltaTime; wheel ramping is delta x acceleration
        for (const f of engine._activeRenderLoops) f();
        engine.endFrame();
        window._vtPumped++;
      }
      ch.port2.postMessage(0);
    };
    ch.port2.postMessage(0);
  }

  function stubFileDialog() {
    if (window._vtStub) return;
    window._vtStub = true;
    const orig = HTMLInputElement.prototype.dispatchEvent;
    HTMLInputElement.prototype.dispatchEvent = function(ev) {
      if (this.type === 'file' && ev.type === 'click') { pending.push(this); return true; }
      return orig.call(this, ev);
    };
  }

  async function feed(name, data, mime) {
    for (let i = 0; i < 50 && !pending.length; i++) await sleep(20);
    const el = pending.pop();
    if (!el) throw new Error('no file input is waiting');
    const dt = new DataTransfer();
    dt.items.add(new File([data], name, {type: mime}));
    el.files = dt.files;
    el.dispatchEvent(new Event('change'));
  }

  async function sha256(data) {
    const buf = typeof data === 'string' ? new TextEncoder().encode(data) : data;
    const h = await crypto.subtle.digest('SHA-256', buf);
    return [...new Uint8Array(h)].map(b => b.toString(16).padStart(2, '0')).join('');
  }

  function menuItem(text) {
    return [...document.querySelectorAll('.menuDropDown li')].find(li => li.innerText.trim() === text);
  }

  // Same handlers as clicking the menu; `menu` is the top-bar label.
  async function openMenu(menu, item) {
    const top = [...document.querySelectorAll('.menuBar .menuItem')].find(e => e.innerText.trim() === menu);
    top.click();
    await sleep(200);
    const li = menuItem(item);
    if (!li) throw new Error('menu item not found: ' + menu + ' -> ' + item);
    li.click();
  }

  async function loadWorld(text) {
    await openMenu('Worlds', 'Load from file');
    await feed('world.json', text, 'application/json');
    await sleep(3000);
  }

  async function importZip(bytes) {
    await openMenu('File', 'Import zip package from your computer');
    await feed('project.zip', bytes, 'application/zip');
    await sleep(3000);
  }

  function setMain(code) {
    filesManager.select('main.py');
    pythonPanel.editor.setValue(code, 1);
    filesManager.updateCurrentFile();
  }

  async function runMain(code, timeoutMs) {
    $('#navSim').click();
    $('.reset').click();
    await sleep(1500);
    setMain(code);
    simPanel.clearConsole();
    const t0 = Date.now();
    $('.runSim').click();
    await sleep(300);
    while (skulpt.running && Date.now() - t0 < (timeoutMs || 120000)) await sleep(200);
    const timedOut = skulpt.running;
    if (timedOut) $('.runSim').click();
    await sleep(300);
    return {secs: (Date.now() - t0) / 1000, timedOut, console: simPanel.$consoleContent.text()};
  }

  function parse(text) {
    const lines = text.split('\n');
    return {
      pass: lines.filter(l => l.startsWith('PASS ')).length,
      fail: lines.filter(l => l.startsWith('FAIL ')),
      summary: lines.find(l => l.startsWith('SUMMARY ')) || null,
      errors: lines.filter(l => /Error|Exception/.test(l) && !l.startsWith('PASS') && !l.startsWith('FAIL')),
    };
  }

  return {sleep, pump, stubFileDialog, feed, sha256, openMenu, loadWorld, importZip, setMain, runMain, parse};
})();
