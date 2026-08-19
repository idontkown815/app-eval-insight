const fs = require('fs');
const zlib = require('zlib');
const path = require('path');

fs.mkdirSync('build', { recursive: true });
const iconPath = path.join('build', 'icon.png');

if (fs.existsSync(iconPath)) {
  console.log('icon.png found (' + fs.statSync(iconPath).size + ' bytes)');
  process.exit(0);
}

console.log('Creating minimal placeholder icon...');

const crc32 = (buf) => {
  let c = 0xffffffff;
  const table = [];
  for (let n = 0; n < 256; n++) {
    let c2 = n;
    for (let k = 0; k < 8; k++) {
      c2 = c2 & 1 ? 0xedb88320 ^ (c2 >>> 1) : c2 >>> 1;
    }
    table[n] = c2;
  }
  for (const b of buf) c = table[(c ^ b) & 0xff] ^ (c >>> 8);
  return (c ^ 0xffffffff) >>> 0;
};

const makeChunk = (type, data) => {
  const len = Buffer.alloc(4);
  len.writeUInt32BE(data.length);
  const typeData = Buffer.concat([Buffer.from(type), data]);
  const crcBuf = Buffer.alloc(4);
  crcBuf.writeUInt32BE(crc32(typeData));
  return Buffer.concat([len, typeData, crcBuf]);
};

const width = 1, height = 1;
const sig = Buffer.from([137, 80, 78, 71, 13, 10, 26, 10]);
const ihdr = Buffer.alloc(13);
ihdr.writeUInt32BE(width, 0);
ihdr.writeUInt32BE(height, 4);
ihdr[8] = 8;  // bit depth
ihdr[9] = 6;  // color type (RGBA)
const raw = Buffer.from([0, 0, 128, 255]); // filter byte + R + G + B + A
const idat = zlib.deflateSync(raw);
const iend = Buffer.alloc(0);

const png = Buffer.concat([
  sig,
  makeChunk('IHDR', ihdr),
  makeChunk('IDAT', idat),
  makeChunk('IEND', iend)
]);

fs.writeFileSync(iconPath, png);
console.log('Created icon.png (' + png.length + ' bytes)');
