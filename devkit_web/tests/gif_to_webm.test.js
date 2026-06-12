// GIF→WebM tool — pure parts + queue UI (the actual ffmpeg conversion needs
// network and a real browser, so it is exercised manually on the hosted page).
import { test, beforeEach } from 'node:test';
import assert from 'node:assert/strict';
import { Window } from 'happy-dom';

let w;
beforeEach(() => {
  w = new Window();
  globalThis.window = w;
  globalThis.document = w.document;
  globalThis.HTMLElement = w.HTMLElement;
  globalThis.Event = w.Event;
  globalThis.alert = () => {};
});

test('FFMPEG_ARGS matches the v6 encoder settings', async () => {
  const { FFMPEG_ARGS } = await import('../src/tools/gif_to_webm.js');
  assert.deepEqual(FFMPEG_ARGS('in.gif', 'out.webm'), [
    '-i', 'in.gif', '-c:v', 'libvpx-vp9', '-pix_fmt', 'yuva420p',
    '-auto-alt-ref', '0', '-crf', '30', '-b:v', '0', '-an', 'out.webm',
  ]);
});

test('webmNameFor swaps the extension case-insensitively', async () => {
  const { webmNameFor } = await import('../src/tools/gif_to_webm.js');
  assert.equal(webmNameFor('dance.gif'), 'dance.webm');
  assert.equal(webmNameFor('Dance.GIF'), 'Dance.webm');
});

test('tool scans a folder recursively and lists the queue', async () => {
  const { runGifToWebmTool } = await import('../src/tools/gif_to_webm.js');
  const fakeDir = (entries) => ({
    kind: 'directory',
    async* entries() { for (const [n, e] of Object.entries(entries)) yield [n, e]; },
  });
  const folder = fakeDir({
    'dance.gif': { kind: 'file' },
    'profile.png': { kind: 'file' },
    sub: fakeDir({ 'spin.GIF': { kind: 'file' } }),
  });
  w.showDirectoryPicker = async () => folder;

  const container = document.createElement('div');
  runGifToWebmTool(container, { onDone: () => {} });
  container.querySelector('[data-action="pick-gif-folder"]').dispatchEvent(new Event('click'));
  await new Promise((r) => setTimeout(r, 0));
  await new Promise((r) => setTimeout(r, 0));

  assert.match(container.textContent, /2 GIF\(s\) found/);
  assert.match(container.textContent, /dance\.gif/);
  assert.match(container.textContent, /sub\/spin\.GIF/);
  assert.ok(container.querySelector('[data-action="convert"]'));
});
