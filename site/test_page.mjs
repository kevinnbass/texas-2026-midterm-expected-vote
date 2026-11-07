// Drive headless Chromium over CDP: click through the page's controls, check state, take screenshots.
// Needs Node 22+ (built-in fetch and WebSocket) and a Chromium started with --remote-debugging-port, e.g.
//   chromium --headless --remote-debugging-port=9333 --user-data-dir=/tmp/prof about:blank &
//   node site/test_page.mjs file://$PWD/build/site/index.html /tmp/shots 9333
// usage: node test_page.mjs <page_url> <out_dir> <cdp_port>   (exit 0 = every check passed)
import { writeFileSync } from 'node:fs';
const [url, out, port] = process.argv.slice(2);
const sleep = ms => new Promise(r => setTimeout(r, ms));
let targets;
for (let i = 0; i < 50; i++) {
  try { targets = await (await fetch(`http://127.0.0.1:${port}/json/list`)).json(); if (targets.length) break; } catch {}
  await sleep(200);
}
const page = targets.find(t => t.type === 'page');
const ws = new WebSocket(page.webSocketDebuggerUrl);
await new Promise(r => ws.addEventListener('open', r, { once: true }));
let id = 0; const pending = new Map(); const errors = [];
ws.addEventListener('message', ev => {
  const m = JSON.parse(ev.data);
  if (m.id && pending.has(m.id)) { pending.get(m.id)(m); pending.delete(m.id); }
  if (m.method === 'Runtime.exceptionThrown') errors.push(m.params.exceptionDetails.text + ' ' + (m.params.exceptionDetails.exception?.description || ''));
  if (m.method === 'Runtime.consoleAPICalled' && m.params.type === 'error') errors.push('console.error ' + JSON.stringify(m.params.args.map(a => a.value)));
  if (m.method === 'Log.entryAdded' && m.params.entry.level === 'error') errors.push('log ' + m.params.entry.text);
});
const send = (method, params = {}) => new Promise(r => { const i = ++id; pending.set(i, r); ws.send(JSON.stringify({ id: i, method, params })); });
const ev = async expr => { const r = await send('Runtime.evaluate', { expression: expr, awaitPromise: true, returnByValue: true }); return r.result.result.value; };
const shot = async (name, clip) => { const r = await send('Page.captureScreenshot', clip ? { format: 'png', clip: { ...clip, scale: 1 } } : { format: 'png' }); writeFileSync(`${out}/${name}.png`, Buffer.from(r.result.data, 'base64')); };
const results = [];
const check = (name, ok, detail = '') => { results.push(`${ok ? 'PASS' : 'FAIL'} ${name}${detail ? ' :: ' + detail : ''}`); };

await send('Runtime.enable'); await send('Log.enable'); await send('Page.enable');
await send('Emulation.setDeviceMetricsOverride', { width: 1440, height: 900, deviceScaleFactor: 1, mobile: false });
await send('Page.navigate', { url });
await sleep(2500);
await ev(`Promise.all([...document.images].map(i => (i.loading='eager', i.complete ? 1 : new Promise(r => { i.onload = i.onerror = r; }))))`);
await sleep(500);

// images load
const imgs = await ev(`[...document.images].map(i => [i.getAttribute('src'), i.naturalWidth])`);
check('all page images load', imgs.every(([s, w]) => !s || w > 0), JSON.stringify(imgs));
// panel images referenced by tabs exist
const tabsrc = await ev(`Promise.all([...document.querySelectorAll('[role=tab]')].map(t => new Promise(r => { const i = new Image(); i.onload = () => r([t.dataset.src, i.naturalWidth, +t.dataset.w]); i.onerror = () => r([t.dataset.src, 0, +t.dataset.w]); i.src = t.dataset.src; })))`);
check('all tab images load at their stated width', tabsrc.every(([s, w, dw]) => w > 0 && w === dw), JSON.stringify(tabsrc));
// numbers: no leftover placeholders, no NaN/undefined
const txt = await ev(`document.body.innerText`);
check('no template placeholders or NaN', !/\{\{|NaN|undefined/.test(txt));
// default table
check('one table visible at load (2026 plain)', await ev(`(() => { const v = [...document.querySelectorAll('table[data-year]')].filter(t => !t.hidden); return v.length === 1 && v[0].dataset.year === '2026' && v[0].dataset.exp === 'plain'; })()`));
check('2026 table has 15 rows', await ev(`document.querySelector('table[data-year="2026"][data-exp="plain"] tbody').rows.length`) === 15);
check('2022 table has 14 rows', await ev(`document.querySelector('table[data-year="2022"][data-exp="plain"] tbody').rows.length`) === 14);
await shot('01_top_1440');

// figure 1 tabs
await ev(`document.querySelectorAll('#figure-1 [role=tab]')[2].click()`);
await sleep(600);
const st = await ev(`(() => { const v = document.querySelector('#figure-1 [data-viewer]'); return [v.querySelector('.stage img').getAttribute('src'), v.querySelector('[data-dl]').getAttribute('href'), [...v.querySelectorAll('[role=tab]')].map(t => t.getAttribute('aria-selected')).join(',')]; })()`);
check('tab switches image, download link and selection', st[0].endsWith('panels/texas_statewide_expected_2018_2026.png') && st[1] === st[0] && st[2] === 'false,false,true', JSON.stringify(st));
await ev(`document.querySelector('#figure-1').scrollIntoView()`); await sleep(400);
await shot('02_fig1_right_tab');
// lightbox
await ev(`document.querySelector('#figure-1 .stage').click()`); await sleep(700);
check('lightbox opens with the selected image', await ev(`document.getElementById('lightbox').open && document.querySelector('#lightbox img').getAttribute('src').endsWith('panels/texas_statewide_expected_2018_2026.png')`));
check('lightbox close button has focus on open', (await ev(`document.activeElement && document.activeElement.dataset.act`)) === 'close');
check('lightbox caption', (await ev(`document.querySelector('#lightbox .cap').textContent`)) === 'Figure 1, right: actual vs. expected votes');
await shot('03_lightbox_fit');
await ev(`(() => { const i = document.querySelector('#lightbox img'), r = i.getBoundingClientRect(); i.dispatchEvent(new MouseEvent('click', { bubbles: true, clientX: r.left + r.width * 0.15, clientY: r.top + r.height * 0.2 })); })()`);
await sleep(700);
const act = await ev(`(() => { const s = document.querySelector('#lightbox .scroller'), i = document.querySelector('#lightbox img'); return [document.getElementById('lightbox').classList.contains('actual'), i.offsetWidth, s.scrollLeft, s.scrollTop]; })()`);
check('click zooms to full resolution near the clicked point', act[0] && act[1] === 3060 && act[2] >= 0 && act[3] > 0, JSON.stringify(act));
await shot('04_lightbox_actual');
await ev(`document.querySelector('#lightbox [data-act=close]').click()`); await sleep(300);
check('lightbox closes', !(await ev(`document.getElementById('lightbox').open`)));
// whole-figure tab back
await ev(`document.querySelectorAll('#figure-1 [role=tab]')[0].click()`); await sleep(300);
check('back to whole figure', (await ev(`document.querySelector('#figure-1 .stage img').getAttribute('src')`)).endsWith('figures/texas_history_and_expected.png'));

// table controls
await ev(`document.querySelector('[data-ctl=year] [data-v="2018"]').click()`);
await ev(`document.querySelector('[data-ctl=exp] [data-v="inc"]').click()`);
await sleep(300);
const vis = await ev(`[...document.querySelectorAll('table[data-year]')].filter(t => !t.hidden).map(t => t.dataset.year + '/' + t.dataset.exp)`);
check('year + expectation switch shows exactly that table', JSON.stringify(vis) === '["2018/inc"]', JSON.stringify(vis));
await ev(`document.documentElement.style.scrollBehavior='auto'; document.querySelector('#numbers').scrollIntoView()`); await sleep(500);
await shot('05_table_2018_inc');
await ev(`document.querySelector('[data-ctl=year] [data-v="2026"]').click()`);
await ev(`document.querySelector('[data-ctl=exp] [data-v="plain"]').click()`);
await sleep(200);

// keyboard: arrow keys on tabs
await ev(`document.querySelectorAll('#figure-2 [role=tab]')[0].focus()`);
await send('Input.dispatchKeyEvent', { type: 'keyDown', key: 'ArrowRight', code: 'ArrowRight', windowsVirtualKeyCode: 39 });
await send('Input.dispatchKeyEvent', { type: 'keyUp', key: 'ArrowRight', code: 'ArrowRight', windowsVirtualKeyCode: 39 });
await sleep(300);
check('arrow key moves to next tab', (await ev(`document.activeElement.textContent`)) === 'Left: 1994–2026' && (await ev(`document.querySelector('#figure-2 .stage img').getAttribute('src')`)).includes('history_incumbency'));

// overflow check at desktop and phone widths
const ovf = async () => ev(`document.documentElement.scrollWidth - document.documentElement.clientWidth`);
check('no horizontal page overflow at 1440', (await ovf()) <= 0);
await send('Emulation.setDeviceMetricsOverride', { width: 390, height: 844, deviceScaleFactor: 2, mobile: true });
await sleep(800);
await ev(`window.scrollTo(0, 0)`); await sleep(200);
check('no horizontal page overflow at 390 (table scrolls inside its card)', (await ovf()) <= 0, String(await ovf()));
await shot('06_phone_top');
await ev(`document.querySelector('#figure-1').scrollIntoView()`); await sleep(400);
await shot('07_phone_fig1');

check('no script errors', errors.length === 0, errors.join(' | '));
writeFileSync(`${out}/results.txt`, results.join('\n') + '\n');
console.log(results.join('\n'));
ws.close();
process.exit(results.some(r => r.startsWith('FAIL')) ? 1 : 0);
