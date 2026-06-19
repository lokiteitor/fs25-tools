// png_encoder.js
// Exports utility to save heightmaps in 16-bit Grayscale PNG format.

export function create16BitGrayscalePNG(width, height, heightsInMeters) {
    // heightsInMeters is a Float32Array of size width * height.
    // Heights are stored in meters. We convert to centimeters (height * 100) and clamp to [0, 65535].
    
    // PNG signature: 89 50 4E 47 0D 0A 1A 0A
    const signature = new Uint8Array([0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A]);
    
    // IHDR chunk data (13 bytes)
    // Width (4 bytes, Big Endian)
    // Height (4 bytes, Big Endian)
    // Bit depth: 16 (0x10)
    // Color type: 0 (grayscale)
    // Compression: 0 (deflate)
    // Filter: 0 (none)
    // Interlace: 0 (none)
    const ihdrData = new Uint8Array(13);
    const view = new DataView(ihdrData.buffer);
    view.setUint32(0, width, false);
    view.setUint32(4, height, false);
    ihdrData[8] = 16; // 16-bit
    ihdrData[9] = 0;  // Grayscale
    ihdrData[10] = 0; // Deflate
    ihdrData[11] = 0; // Filter
    ihdrData[12] = 0; // Interlace
    
    const ihdrChunk = createChunk("IHDR", ihdrData);
    
    // IDAT chunk data (uncompressed zlib stream)
    // Raw pixel data size: height * (1 + width * 2) bytes
    // 1 filter byte per row (0 = no filter) + 2 bytes per pixel (Big Endian uint16)
    const rawDataSize = height * (1 + width * 2);
    const rawData = new Uint8Array(rawDataSize);
    
    let rawIdx = 0;
    for (let y = 0; y < height; y++) {
        rawData[rawIdx++] = 0; // Filter byte: None
        for (let x = 0; x < width; x++) {
            const hIdx = y * width + x;
            const hCm = Math.max(0, Math.min(65535, Math.round(heightsInMeters[hIdx] * 100)));
            rawData[rawIdx++] = (hCm >> 8) & 0xFF; // MSB (Big Endian)
            rawData[rawIdx++] = hCm & 0xFF;        // LSB
        }
    }
    
    // Create uncompressed zlib stream
    // 2 bytes zlib header: 0x78 0x01
    // Deflate blocks of max 65535 bytes
    const zlibHeader = new Uint8Array([0x78, 0x01]);
    
    const blockSize = 65535;
    const blocksCount = Math.ceil(rawDataSize / blockSize);
    const blocks = [];
    
    for (let i = 0; i < blocksCount; i++) {
        const start = i * blockSize;
        const end = Math.min(rawDataSize, start + blockSize);
        const len = end - start;
        const isLast = (i === blocksCount - 1) ? 1 : 0;
        
        // Block header: 5 bytes
        // 1 byte BFINAL + BTYPE (0x01 if last block, 0x00 if not)
        // 2 bytes LEN (Little Endian)
        // 2 bytes NLEN (Little Endian complement)
        const blockHeader = new Uint8Array(5);
        blockHeader[0] = isLast;
        blockHeader[1] = len & 0xFF;
        blockHeader[2] = (len >> 8) & 0xFF;
        const nlen = ~len;
        blockHeader[3] = nlen & 0xFF;
        blockHeader[4] = (nlen >> 8) & 0xFF;
        
        const blockData = rawData.subarray(start, end);
        
        const mergedBlock = new Uint8Array(blockHeader.length + blockData.length);
        mergedBlock.set(blockHeader, 0);
        mergedBlock.set(blockData, blockHeader.length);
        blocks.push(mergedBlock);
    }
    
    // Adler-32 checksum (4 bytes, Big Endian) over rawData
    const adlerVal = adler32(rawData);
    const adlerBytes = new Uint8Array([
        (adlerVal >> 24) & 0xFF,
        (adlerVal >> 16) & 0xFF,
        (adlerVal >> 8) & 0xFF,
        adlerVal & 0xFF
    ]);
    
    // Sum zlib parts
    let zlibSize = zlibHeader.length + adlerBytes.length;
    for (const b of blocks) zlibSize += b.length;
    
    const idatData = new Uint8Array(zlibSize);
    let idatIdx = 0;
    idatData.set(zlibHeader, idatIdx);
    idatIdx += zlibHeader.length;
    for (const b of blocks) {
        idatData.set(b, idatIdx);
        idatIdx += b.length;
    }
    idatData.set(adlerBytes, idatIdx);
    
    const idatChunk = createChunk("IDAT", idatData);
    
    // IEND chunk (empty, just marker)
    const iendChunk = createChunk("IEND", new Uint8Array(0));
    
    // Assemble final PNG file
    const pngSize = signature.length + ihdrChunk.length + idatChunk.length + iendChunk.length;
    const png = new Uint8Array(pngSize);
    let pngIdx = 0;
    
    png.set(signature, pngIdx); pngIdx += signature.length;
    png.set(ihdrChunk, pngIdx); pngIdx += ihdrChunk.length;
    png.set(idatChunk, pngIdx); pngIdx += idatChunk.length;
    png.set(iendChunk, pngIdx); pngIdx += iendChunk.length;
    
    return png;
}

function createChunk(type, data) {
    const len = data.length;
    const chunk = new Uint8Array(4 + 4 + len + 4); // Length (4), Type (4), Data (len), CRC (4)
    const view = new DataView(chunk.buffer);
    
    view.setUint32(0, len, false);
    
    // Type (4 bytes)
    for (let i = 0; i < 4; i++) {
        chunk[4 + i] = type.charCodeAt(i);
    }
    
    // Data (len bytes)
    chunk.set(data, 8);
    
    // CRC (4 bytes) - calculated over Type and Data
    const crcBytes = chunk.subarray(4, 8 + len);
    const crcVal = crc32(crcBytes);
    view.setUint32(8 + len, crcVal, false);
    
    return chunk;
}

// Adler-32 implementation
function adler32(data) {
    let s1 = 1;
    let s2 = 0;
    const len = data.length;
    
    // Process in chunks of 5552 bytes to prevent overflow in s2
    let pos = 0;
    while (pos < len) {
        const chunkLen = Math.min(5552, len - pos);
        for (let i = 0; i < chunkLen; i++) {
            s1 = s1 + data[pos++];
            s2 = s2 + s1;
        }
        s1 = s1 % 65521;
        s2 = s2 % 65521;
    }
    return ((s2 << 16) | s1) >>> 0;
}

// CRC-32 table initialization
const crcTable = [];
for (let n = 0; n < 256; n++) {
    let c = n;
    for (let k = 0; k < 8; k++) {
        if (c & 1) {
            c = 0xedb88320 ^ (c >>> 1);
        } else {
            c = c >>> 1;
        }
    }
    crcTable[n] = c;
}

function crc32(bytes) {
    let crc = 0xffffffff;
    for (let i = 0; i < bytes.length; i++) {
        crc = crcTable[(crc ^ bytes[i]) & 0xff] ^ (crc >>> 8);
    }
    return (crc ^ 0xffffffff) >>> 0;
}
