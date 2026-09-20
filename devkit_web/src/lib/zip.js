import { LIMITS, safePath } from './contract.js';

const TABLE = Array.from({length:256}, (_, n) => {
  for (let k = 0; k < 8; k++) n = (n & 1) ? 0xedb88320 ^ (n >>> 1) : n >>> 1;
  return n >>> 0;
});
function crc32(data) {
  let crc = 0xffffffff;
  for (const byte of data) crc = TABLE[(crc ^ byte) & 255] ^ (crc >>> 8);
  return (crc ^ 0xffffffff) >>> 0;
}

// Stored ZIP entries avoid runtime dependencies/CDNs. Images are already
// compressed; regular ZIP readers, including Python's importer, support this.
export function buildZip(entries) {
  if (!entries.length || entries.length > LIMITS.files) throw new Error('Invalid number of files.');
  const encoder = new TextEncoder();
  const chunks = [], directory = [], paths = new Set();
  let offset = 0, total = 0;
  for (const entry of entries) {
    const path = safePath(entry.path);
    const name = encoder.encode(path);
    if (name.length > 65535 || paths.has(path.toLowerCase())) throw new Error('Duplicate or overlong ZIP path: ' + path);
    paths.add(path.toLowerCase());
    const bytes = typeof entry.data === 'string' ? encoder.encode(entry.data) : entry.data;
    if (!(bytes instanceof Uint8Array) || bytes.length > LIMITS.file) throw new Error('Invalid or oversized file: ' + path);
    total += bytes.length;
    if (total > LIMITS.total) throw new Error('This devkit supports packs up to 128 MB. Split this project into smaller packs.');
    const crc = crc32(bytes);
    const header = new Uint8Array(30 + name.length), view = new DataView(header.buffer);
    view.setUint32(0, 0x04034b50, true); view.setUint16(4, 20, true);
    view.setUint16(6, 0x800, true); view.setUint16(12, 33, true);
    view.setUint32(14, crc, true); view.setUint32(18, bytes.length, true); view.setUint32(22, bytes.length, true);
    view.setUint16(26, name.length, true); header.set(name, 30);
    const central = new Uint8Array(46 + name.length), cv = new DataView(central.buffer);
    cv.setUint32(0, 0x02014b50, true); cv.setUint16(4, 20, true); cv.setUint16(6, 20, true);
    cv.setUint16(8, 0x800, true); cv.setUint16(14, 33, true); cv.setUint32(16, crc, true);
    cv.setUint32(20, bytes.length, true); cv.setUint32(24, bytes.length, true);
    cv.setUint16(28, name.length, true); cv.setUint32(42, offset, true); central.set(name, 46);
    chunks.push(header, bytes); directory.push(central); offset += header.length + bytes.length;
  }
  const directorySize = directory.reduce((n, c) => n + c.length, 0);
  const end = new Uint8Array(22), ev = new DataView(end.buffer);
  ev.setUint32(0, 0x06054b50, true); ev.setUint16(8, entries.length, true); ev.setUint16(10, entries.length, true);
  ev.setUint32(12, directorySize, true); ev.setUint32(16, offset, true);
  const out = new Uint8Array(offset + directorySize + end.length);
  let position = 0;
  for (const chunk of [...chunks, ...directory, end]) { out.set(chunk, position); position += chunk.length; }
  return out;
}
