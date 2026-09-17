import { deflateSync } from 'node:zlib'
import { mkdirSync, writeFileSync } from 'node:fs'

const size = 512
const pixels = Buffer.alloc(size * size * 4)

function setPixel(x, y, [red, green, blue, alpha = 255]) {
  if (x < 0 || y < 0 || x >= size || y >= size) return
  const offset = (y * size + x) * 4
  pixels[offset] = red
  pixels[offset + 1] = green
  pixels[offset + 2] = blue
  pixels[offset + 3] = alpha
}

function insideRoundedRect(x, y, left, top, right, bottom, radius) {
  const closestX = Math.max(left + radius, Math.min(x, right - radius))
  const closestY = Math.max(top + radius, Math.min(y, bottom - radius))
  const dx = x - closestX
  const dy = y - closestY
  return dx * dx + dy * dy <= radius * radius
}

function drawLine(x0, y0, x1, y1, width, color) {
  const steps = Math.max(Math.abs(x1 - x0), Math.abs(y1 - y0))
  for (let step = 0; step <= steps; step += 1) {
    const x = Math.round(x0 + ((x1 - x0) * step) / steps)
    const y = Math.round(y0 + ((y1 - y0) * step) / steps)
    for (let dy = -width; dy <= width; dy += 1) {
      for (let dx = -width; dx <= width; dx += 1) {
        if (dx * dx + dy * dy <= width * width) setPixel(x + dx, y + dy, color)
      }
    }
  }
}

for (let y = 0; y < size; y += 1) {
  for (let x = 0; x < size; x += 1) {
    if (insideRoundedRect(x, y, 0, 0, size - 1, size - 1, 104)) {
      setPixel(x, y, [29, 78, 216, 255])
    }
    if (insideRoundedRect(x, y, 104, 128, 408, 384, 28)) {
      setPixel(x, y, [239, 246, 255, 255])
    }
  }
}

drawLine(148, 314, 218, 242, 14, [37, 99, 235, 255])
drawLine(218, 242, 273, 284, 14, [37, 99, 235, 255])
drawLine(273, 284, 364, 180, 14, [37, 99, 235, 255])

const crcTable = Array.from({ length: 256 }, (_, value) => {
  let current = value
  for (let bit = 0; bit < 8; bit += 1) {
    current = (current & 1) !== 0 ? 0xedb88320 ^ (current >>> 1) : current >>> 1
  }
  return current >>> 0
})

function crc32(buffer) {
  let crc = 0xffffffff
  for (const byte of buffer) crc = crcTable[(crc ^ byte) & 0xff] ^ (crc >>> 8)
  return (crc ^ 0xffffffff) >>> 0
}

function chunk(type, data) {
  const name = Buffer.from(type)
  const output = Buffer.alloc(12 + data.length)
  output.writeUInt32BE(data.length, 0)
  name.copy(output, 4)
  data.copy(output, 8)
  output.writeUInt32BE(crc32(Buffer.concat([name, data])), 8 + data.length)
  return output
}

const header = Buffer.alloc(13)
header.writeUInt32BE(size, 0)
header.writeUInt32BE(size, 4)
header[8] = 8
header[9] = 6

const rows = Buffer.alloc((size * 4 + 1) * size)
for (let y = 0; y < size; y += 1) {
  const rowOffset = y * (size * 4 + 1)
  rows[rowOffset] = 0
  pixels.copy(rows, rowOffset + 1, y * size * 4, (y + 1) * size * 4)
}

mkdirSync(new URL('../build/', import.meta.url), { recursive: true })
writeFileSync(
  new URL('../build/icon.png', import.meta.url),
  Buffer.concat([
    Buffer.from([137, 80, 78, 71, 13, 10, 26, 10]),
    chunk('IHDR', header),
    chunk('IDAT', deflateSync(rows, { level: 9 })),
    chunk('IEND', Buffer.alloc(0)),
  ]),
)
