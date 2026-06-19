// editor.js
import { create16BitGrayscalePNG } from './png_encoder.js';

// --- Application State ---
let gridWidth = 512;
let gridHeight = 512;
let heights = new Float32Array(gridWidth * gridHeight);

// Brush parameters
let activeTool = 'raise'; // 'raise', 'lower', 'flatten', 'smooth', 'ramp-start', 'ramp-end', 'osm-select', 'osm-draw'
let brushRadiusMeters = 150;
let brushStrength = 0.4;
let targetHeight = 100;
let isPainting = false;
let paintRequestId = null;
let lastPaintTime = 0;
let currentMouseMeters = { x: 0, y: 0 };
let lastPaintMeters = { x: 0, y: 0 };

// Ramp parameters
let rampStart = null; // { x, y } in meters
let rampEnd = null;   // { x, y } in meters

// 2D Render Options
let viewMode2D = 'shading'; // 'shading', 'elevation', 'grayscale'

// OSM Vector Data
// Bounding box matching the Python scripts:
const MIN_LON = -109.7277558150625;
const MAX_LON = -109.6863841849375;
const MIN_LAT = 27.061491919529106;
const MAX_LAT = 27.098328080470894;
const PLAYABLE_SIZE = 4096;
const MAP_SIZE = 8192;

let osmNodes = {}; // id -> { id, lat, lon, x, z } in meters
let osmWays = [];   // array of { id, tags: {}, nodeRefs: [] }
let nextNodeId = -1;
let nextWayId = -1;

let selectedWay = null;
let activeDrawPath = []; // array of node ids in progress
let activeHoverNode = null;
let activeSelectedNode = null;
let isDraggingNode = false;

// UI elements caching
let elHeightCanvas, elVectorCanvas, ctxHeight, ctxVector;
let elStatusCoords, elStatusElevation, elStatusZone;
let elActiveToolDisplay, elTagsPanel, elNoSelectionMsg, elTagsList;
let elRampStatus;

// Three.js State
let renderer3D, scene3D, camera3D, controls3D;
let terrainMesh3D, terrainGeom3D, terrainMaterial3D;
let playableBox3D;
let osmLines3DGroup = null;
let exaggeration3D = 1.5;
let renderMode3D = 'texture'; // 'texture', 'elevation', 'wireframe'
let isSamplingHeight = false;

// --- Seeded Perlin Noise Class ---
class PerlinNoise {
    constructor(seed = 12345) {
        let state = seed;
        function random() {
            state = (state * 1664525 + 1013904223) % 4294967296;
            return state / 4294967296;
        }
        
        this.p = new Uint8Array(256);
        for (let i = 0; i < 256; i++) this.p[i] = i;
        
        for (let i = 255; i > 0; i--) {
            const j = Math.floor(random() * (i + 1));
            const tmp = this.p[i];
            this.p[i] = this.p[j];
            this.p[j] = tmp;
        }
        
        this.gx = new Float32Array(256);
        this.gy = new Float32Array(256);
        for (let i = 0; i < 256; i++) {
            const angle = random() * Math.PI * 2;
            this.gx[i] = Math.cos(angle);
            this.gy[i] = Math.sin(angle);
        }
    }
    
    noise2d(x, y) {
        const X = Math.floor(x) & 255;
        const Y = Math.floor(y) & 255;
        const xf = x - Math.floor(x);
        const yf = y - Math.floor(y);
        
        const u = xf * xf * xf * (xf * (xf * 6 - 15) + 10);
        const v = yf * yf * yf * (yf * (yf * 6 - 15) + 10);
        
        const n00 = this.getGrad(X, Y, xf, yf);
        const n10 = this.getGrad(X + 1, Y, xf - 1, yf);
        const n01 = this.getGrad(X, Y + 1, xf, yf - 1);
        const n11 = this.getGrad(X + 1, Y + 1, xf - 1, yf - 1);
        
        const x1 = n00 * (1 - u) + n10 * u;
        const x2 = n01 * (1 - u) + n11 * u;
        return x1 * (1 - v) + x2 * v;
    }
    
    getGrad(ix, iy, dx, dy) {
        const hash = this.p[(this.p[ix & 255] + iy) & 255];
        return this.gx[hash] * dx + this.gy[hash] * dy;
    }
}

function fractalNoise(perlin, x, y, octaves, persistence = 0.5, scale = 1.0) {
    let total = 0;
    let frequency = scale;
    let amplitude = 1;
    let maxValue = 0;
    for (let i = 0; i < octaves; i++) {
        total += perlin.noise2d(x * frequency, y * frequency) * amplitude;
        maxValue += amplitude;
        amplitude *= persistence;
        frequency *= 2;
    }
    return total / maxValue;
}

// --- Spline interpolation for roads ---
function interpolateCatmullRom(p0, p1, p2, p3, t) {
    const t2 = t * t;
    const t3 = t2 * t;
    return 0.5 * (
        (2 * p1) +
        (-p0 + p2) * t +
        (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2 +
        (-p0 + 3 * p1 - 3 * p2 + p3) * t3
    );
}

function evaluateSpline(controlPoints, resolution = 2000) {
    if (controlPoints.length < 2) return [];
    const padded = [
        controlPoints[0],
        ...controlPoints,
        controlPoints[controlPoints.length - 1]
    ];
    const evaluated = [];
    const segments = controlPoints.length - 1;
    
    for (let i = 0; i < segments; i++) {
        const p0 = padded[i];
        const p1 = padded[i + 1];
        const p2 = padded[i + 2];
        const p3 = padded[i + 3];
        
        const segmentSteps = Math.ceil(resolution / segments);
        for (let step = 0; step < segmentSteps; step++) {
            const t = step / segmentSteps;
            const x = interpolateCatmullRom(p0[0], p1[0], p2[0], p3[0], t);
            const y = interpolateCatmullRom(p0[1], p1[1], p2[1], p3[1], t);
            evaluated.push({ x, y });
        }
    }
    const lastPt = controlPoints[controlPoints.length - 1];
    evaluated.push({ x: lastPt[0], y: lastPt[1] });
    return evaluated;
}

// --- Procedural Base Terrain Generator (Scenario A) ---
window.generateBaseDEM = function() {
    showLoading("Generando Terreno Procedimental...");
    
    setTimeout(() => {
        const seed = parseInt(document.getElementById('param-seed').value) || 12345;
        const flatHeight = parseFloat(document.getElementById('param-flat-height').value) || 100;
        const microRoughnessAmp = parseFloat(document.getElementById('param-roughness').value);
        const borderNoiseScale = parseFloat(document.getElementById('param-border-noise').value);
        
        const S = gridWidth;
        const scaleMeters = MAP_SIZE / S;
        
        // Setup noise sources
        const perlinSlope = new PerlinNoise(seed + 102);
        const perlinSelector = new PerlinNoise(seed);
        const perlinValley = new PerlinNoise(seed + 10);
        const perlinHill = new PerlinNoise(seed + 20);
        const perlinMountain = new PerlinNoise(seed + 30);
        
        // Generate values
        for (let i = 0; i < S; i++) {
            for (let j = 0; j < S; j++) {
                const x = j * scaleMeters;
                const y = i * scaleMeters;
                
                let baseline = flatHeight;
                
                // Micro roughness
                if (microRoughnessAmp > 0) {
                    const micro = fractalNoise(perlinSlope, x / 50, y / 50, 3) * microRoughnessAmp;
                    baseline += micro;
                }
                
                // Non-playable border
                const offsetMin = 2048;
                const offsetMax = 6144;
                const dxBorder = Math.max(0, Math.max(offsetMin - x, x - offsetMax));
                const dyBorder = Math.max(0, Math.max(offsetMin - y, y - offsetMax));
                const distBorder = Math.sqrt(dxBorder*dxBorder + dyBorder*dyBorder);
                
                let wNoise = 0;
                const blendMargin = 256;
                if (distBorder > 0 && distBorder <= blendMargin) {
                    wNoise = 0.5 * (1 - Math.cos(Math.PI * distBorder / blendMargin));
                } else if (distBorder > blendMargin) {
                    wNoise = 1.0;
                }
                
                if (wNoise > 0) {
                    const selectorVal = (perlinSelector.noise2d(x / 1000, y / 1000) * 0.7 + perlinSelector.noise2d(x / 500, y / 500) * 0.3) / 0.7;
                    const selectorClamped = Math.max(-1, Math.min(1, selectorVal));
                    
                    function smoothstep(edge0, edge1, xVal) {
                        const tVal = Math.max(0, Math.min(1, (xVal - edge0) / (edge1 - edge0)));
                        return tVal * tVal * (3.0 - 2.0 * tVal);
                    }
                    const wMountain = smoothstep(-0.2, 0.4, selectorClamped);
                    const wValley = smoothstep(0.2, -0.4, selectorClamped);
                    const wHill = 1.0 - wMountain - wValley;
                    
                    const nValley = fractalNoise(perlinValley, x / 300, y / 300, 3) * 10;
                    const nHill = fractalNoise(perlinHill, x / 200, y / 200, 4) * 40;
                    
                    const m1 = (1.0 - Math.abs(perlinMountain.noise2d(x / 1024, y / 1024))) * 180;
                    const m2 = (1.0 - Math.abs(perlinMountain.noise2d(x / 512, y / 512))) * 80;
                    const m3 = (1.0 - Math.abs(perlinMountain.noise2d(x / 256, y / 256))) * 30;
                    const nMountain = m1 + m2 + m3;
                    
                    const borderNoise = (wValley * nValley + wHill * nHill + wMountain * nMountain) * borderNoiseScale;
                    
                    baseline += borderNoise * wNoise;
                }
                
                heights[i * S + j] = Math.max(0, Math.min(655.35, baseline));
            }
        }
        
        redrawCanvas2D();
        buildTerrain3DMesh();
        hideLoading();
    }, 50);
};

// --- View Modes (2D Renderings) ---
window.set2DViewMode = function(mode) {
    viewMode2D = mode;
    document.querySelectorAll('.toolbar-group .toggle-btn').forEach(btn => btn.classList.remove('active'));
    if (mode === 'shading') document.getElementById('btn-view-shading').classList.add('active');
    if (mode === 'elevation') document.getElementById('btn-view-elevation').classList.add('active');
    if (mode === 'grayscale') document.getElementById('btn-view-grayscale').classList.add('active');
    redrawCanvas2D();
};

function redrawCanvas2D() {
    if (!ctxHeight) return;
    
    const w = gridWidth;
    const h = gridHeight;
    const imgData = ctxHeight.createImageData(w, h);
    const data = imgData.data;
    
    // Shaded Relief Light vector (top-left)
    const lx = 0.7, ly = -0.7, lz = 0.5;
    const lenL = Math.sqrt(lx*lx + ly*ly + lz*lz);
    const nlx = lx / lenL, nly = ly / lenL, nlz = lz / lenL;
    
    const cellScale = MAP_SIZE / w;
    
    for (let y = 0; y < h; y++) {
        for (let x = 0; x < w; x++) {
            const idx = y * w + x;
            const height = heights[idx];
            
            let r = 0, g = 0, b = 0;
            
            if (viewMode2D === 'grayscale') {
                const val = Math.max(0, Math.min(255, Math.round((height / 250) * 255)));
                r = g = b = val;
            } else if (viewMode2D === 'elevation') {
                // Elevation color ramp
                // 0m: Dark Green, 50m: Grass, 150m: Yellow/Brown, 250m+: White
                if (height < 25) {
                    const t = height / 25;
                    r = Math.round(20 + t * 40);
                    g = Math.round(60 + t * 60);
                    b = Math.round(20 + t * 20);
                } else if (height < 150) {
                    const t = (height - 25) / 125;
                    r = Math.round(60 + t * 110);
                    g = Math.round(120 + t * 40);
                    b = Math.round(40 + t * 10);
                } else {
                    const t = Math.min(1.0, (height - 150) / 100);
                    r = Math.round(170 + t * 85);
                    g = Math.round(160 + t * 95);
                    b = Math.round(50 + t * 205);
                }
            } else if (viewMode2D === 'shading') {
                // Shaded Relief (Slope lighting)
                // Base colors: Lake (blue), Valley (green), Meseta (dry green/clay), Mountains (brown/gray)
                let baseR = 110, baseG = 130, baseB = 90; // default grassy clay
                
                // Lake
                if (height <= 226 && x > w * 0.65 && y > h * 0.65) {
                    const dxL = x - w * 5800 / 8192;
                    const dyL = y - h * 5800 / 8192;
                    const distL = Math.max(Math.abs(dxL), Math.abs(dyL));
                    if (distL <= h * 90 / 8192) {
                        baseR = 37; baseG = 99; baseB = 235; // Water
                    }
                }
                
                if (baseR !== 37) { // if not lake
                    if (height < 15) {
                        baseR = 80; baseG = 120; baseB = 75; // Lowland Grass
                    } else if (height < 220) {
                        // Slope transition
                        const t = (height - 15) / 205;
                        baseR = Math.round(80 + t * 50);
                        baseG = Math.round(120 + t * 5);
                        baseB = Math.round(75 + t * 5);
                    } else {
                        // Plateau / High border hills
                        const t = Math.min(1.0, (height - 220) / 100);
                        baseR = Math.round(130 + t * 50);
                        baseG = Math.round(125 + t * 40);
                        baseB = Math.round(80 + t * 85);
                    }
                }
                
                // Compute slopes
                const xp = Math.min(w - 1, x + 1);
                const yp = Math.min(h - 1, y + 1);
                const hz = heights[y * w + x];
                const hdx = (heights[y * w + xp] - hz) / cellScale;
                const hdy = (heights[yp * w + x] - hz) / cellScale;
                
                // Normal
                const nx = -hdx;
                const ny = -hdy;
                const nz = 1.0;
                const lenN = Math.sqrt(nx*nx + ny*ny + nz*nz);
                const nnx = nx / lenN, nny = ny / lenN, nnz = nz / lenN;
                
                // Light dot
                const dot = nnx * nlx + nny * nly + nnz * nlz;
                const diffuse = Math.max(0.0, dot);
                const lighting = 0.35 + 0.65 * diffuse;
                
                r = Math.max(0, Math.min(255, Math.round(baseR * lighting)));
                g = Math.max(0, Math.min(255, Math.round(baseG * lighting)));
                b = Math.max(0, Math.min(255, Math.round(baseB * lighting)));
            }
            
            const pxIdx = idx * 4;
            data[pxIdx] = r;
            data[pxIdx + 1] = g;
            data[pxIdx + 2] = b;
            data[pxIdx + 3] = 255;
        }
    }
    
    ctxHeight.putImageData(imgData, 0, 0);
}

// --- OSM Vector Layer Rendering ---
function redrawOSM2D() {
    if (!ctxVector) return;
    
    ctxVector.clearRect(0, 0, elVectorCanvas.width, elVectorCanvas.height);
    
    const w = elVectorCanvas.width;
    const h = elVectorCanvas.height;
    
    // Grid coordinate conversions
    function toCanvasCoords(xMeters, zMeters) {
        // xMeters, zMeters range from 0 to 8192.
        const u = xMeters / MAP_SIZE;
        const v = zMeters / MAP_SIZE;
        return {
            x: u * w,
            y: v * h
        };
    }
    
    // Draw Playable Area Box (4096m centered)
    const playOffset = (MAP_SIZE - PLAYABLE_SIZE) / 2; // 2048
    const playMin = toCanvasCoords(playOffset, playOffset);
    const playMax = toCanvasCoords(playOffset + PLAYABLE_SIZE, playOffset + PLAYABLE_SIZE);
    
    ctxVector.strokeStyle = 'rgba(79, 70, 229, 0.4)';
    ctxVector.lineWidth = 1.5;
    ctxVector.setLineDash([4, 4]);
    ctxVector.strokeRect(playMin.x, playMin.y, playMax.x - playMin.x, playMax.y - playMin.y);
    ctxVector.setLineDash([]);
    
    // Draw Lake Bounds indicator
    const lakeMin = toCanvasCoords(5800 - 90, 5800 - 90);
    const lakeMax = toCanvasCoords(5800 + 90, 5800 + 90);
    ctxVector.strokeStyle = 'rgba(37, 99, 235, 0.4)';
    ctxVector.lineWidth = 1;
    ctxVector.strokeRect(lakeMin.x, lakeMin.y, lakeMax.x - lakeMin.x, lakeMax.y - lakeMin.y);
    
    // Draw existing OSM Ways
    osmWays.forEach(way => {
        if (way.nodeRefs.length < 2) return;
        
        ctxVector.beginPath();
        const startNode = osmNodes[way.nodeRefs[0]];
        if (!startNode) return;
        
        const startPt = toCanvasCoords(startNode.x, startNode.z);
        ctxVector.moveTo(startPt.x, startPt.y);
        
        for (let i = 1; i < way.nodeRefs.length; i++) {
            const node = osmNodes[way.nodeRefs[i]];
            if (!node) continue;
            const pt = toCanvasCoords(node.x, node.z);
            ctxVector.lineTo(pt.x, pt.y);
        }
        
        // Style based on preset type
        let color = '#ffffff';
        let isClosed = way.tags.natural === 'wood' || way.tags.landuse === 'forest' || way.tags.natural === 'water' || way.tags.water || way.tags.landuse === 'farmyard';
        
        if (way.tags.natural === 'wood' || way.tags.landuse === 'forest') color = '#22c55e'; // Green
        else if (way.tags.landuse === 'farmyard') color = '#eab308'; // Yellow/Orange
        else if (way.tags.natural === 'water' || way.tags.water) color = '#2563eb'; // Blue
        else if (way.tags.highway) color = '#9ca3af'; // Road Gray
        
        ctxVector.lineWidth = (selectedWay === way) ? 4.0 : 2.0;
        ctxVector.strokeStyle = color;
        
        if (isClosed) {
            ctxVector.closePath();
            ctxVector.fillStyle = (selectedWay === way) ? hexToRgba(color, 0.25) : hexToRgba(color, 0.1);
            ctxVector.fill();
        }
        
        ctxVector.stroke();
    });
    
    // Draw Active Drawing Path
    if (activeDrawPath.length > 0) {
        ctxVector.beginPath();
        const startNode = osmNodes[activeDrawPath[0]];
        if (startNode) {
            const startPt = toCanvasCoords(startNode.x, startNode.z);
            ctxVector.moveTo(startPt.x, startPt.y);
            
            for (let i = 1; i < activeDrawPath.length; i++) {
                const node = osmNodes[activeDrawPath[i]];
                if (node) {
                    const pt = toCanvasCoords(node.x, node.z);
                    ctxVector.lineTo(pt.x, pt.y);
                }
            }
            
            ctxVector.strokeStyle = '#a78bfa'; // violet drawing line
            ctxVector.lineWidth = 2;
            ctxVector.stroke();
            
            // Draw node circles
            activeDrawPath.forEach(nid => {
                const node = osmNodes[nid];
                if (node) {
                    const pt = toCanvasCoords(node.x, node.z);
                    ctxVector.fillStyle = '#c084fc';
                    ctxVector.beginPath();
                    ctxVector.arc(pt.x, pt.y, 4, 0, Math.PI * 2);
                    ctxVector.fill();
                }
            });
        }
    }
    
    // Draw all individual nodes if editing vectors
    if (activeTool === 'osm-select' || activeTool === 'osm-draw') {
        Object.values(osmNodes).forEach(node => {
            const pt = toCanvasCoords(node.x, node.z);
            const isHover = activeHoverNode === node;
            const isSel = activeSelectedNode === node;
            
            ctxVector.fillStyle = isSel ? '#ef4444' : (isHover ? '#f43f5e' : 'rgba(255, 255, 255, 0.6)');
            ctxVector.beginPath();
            ctxVector.arc(pt.x, pt.y, isSel ? 6 : (isHover ? 5 : 3), 0, Math.PI * 2);
            ctxVector.fill();
            if (isHover || isSel) {
                ctxVector.strokeStyle = '#ffffff';
                ctxVector.lineWidth = 1;
                ctxVector.stroke();
            }
        });
    }
    
    // Draw Ramp Markers
    if (rampStart) {
        const pt = toCanvasCoords(rampStart.x, rampStart.y);
        ctxVector.fillStyle = '#10b981'; // green for start
        ctxVector.beginPath();
        ctxVector.arc(pt.x, pt.y, 8, 0, Math.PI * 2);
        ctxVector.fill();
        ctxVector.strokeStyle = '#fff';
        ctxVector.lineWidth = 2;
        ctxVector.stroke();
        
        ctxVector.font = '10px monospace';
        ctxVector.fillStyle = '#fff';
        ctxVector.fillText('RAMP INI', pt.x + 10, pt.y + 4);
    }
    
    if (rampEnd) {
        const pt = toCanvasCoords(rampEnd.x, rampEnd.y);
        ctxVector.fillStyle = '#ef4444'; // red for end
        ctxVector.beginPath();
        ctxVector.arc(pt.x, pt.y, 8, 0, Math.PI * 2);
        ctxVector.fill();
        ctxVector.strokeStyle = '#fff';
        ctxVector.lineWidth = 2;
        ctxVector.stroke();
        
        ctxVector.font = '10px monospace';
        ctxVector.fillStyle = '#fff';
        ctxVector.fillText('RAMP FIN', pt.x + 10, pt.y + 4);
    }
    
    // Draw Brush Preview Circle (when mouse hovers, done dynamically in mouse event handlers)
}

function hexToRgba(hex, alpha) {
    const h = hex.replace('#', '');
    const r = parseInt(h.substring(0, 2), 16);
    const g = parseInt(h.substring(2, 4), 16);
    const b = parseInt(h.substring(4, 6), 16);
    return `rgba(${r}, ${g}, ${b}, ${alpha})`;
}

// --- Map Resolution Resizing ---
window.resizeInternalCanvas = function(res) {
    showLoading("Redimensionando malla...");
    setTimeout(() => {
        const targetRes = parseInt(res);
        const oldHeights = heights;
        const oldW = gridWidth;
        const oldH = gridHeight;
        
        gridWidth = targetRes;
        gridHeight = targetRes;
        heights = new Float32Array(gridWidth * gridHeight);
        
        // Bilinear interpolate old values to new grid size
        for (let y = 0; y < gridHeight; y++) {
            for (let x = 0; x < gridWidth; x++) {
                const u = x / (gridWidth - 1);
                const v = y / (gridHeight - 1);
                
                const px = u * (oldW - 1);
                const py = v * (oldH - 1);
                
                const x0 = Math.floor(px);
                const y0 = Math.floor(py);
                const x1 = Math.min(x0 + 1, oldW - 1);
                const y1 = Math.min(y0 + 1, oldH - 1);
                
                const tx = px - x0;
                const ty = py - y0;
                
                const h00 = oldHeights[y0 * oldW + x0];
                const h10 = oldHeights[y0 * oldW + x1];
                const h01 = oldHeights[y1 * oldW + x0];
                const h11 = oldHeights[y1 * oldW + x1];
                
                const h0 = h00 * (1 - tx) + h10 * tx;
                const h1 = h01 * (1 - tx) + h11 * tx;
                
                heights[y * gridWidth + x] = h0 * (1 - ty) + h1 * ty;
            }
        }
        
        // Update elements sizes
        elHeightCanvas.width = targetRes;
        elHeightCanvas.height = targetRes;
        
        redrawCanvas2D();
        buildTerrain3DMesh();
        hideLoading();
    }, 50);
};

// --- Height Manual Brushes implementation ---
function startPaintingLoop(startX, startY) {
    isPainting = true;
    lastPaintMeters.x = startX;
    lastPaintMeters.y = startY;
    currentMouseMeters.x = startX;
    currentMouseMeters.y = startY;
    lastPaintTime = performance.now();
    
    if (paintRequestId) cancelAnimationFrame(paintRequestId);
    paintRequestId = requestAnimationFrame(paintLoop);
}

function paintLoop(now) {
    if (!isPainting) return;
    
    const deltaTime = Math.min(0.1, (now - lastPaintTime) / 1000.0);
    lastPaintTime = now;
    
    let changed = false;
    
    const x0 = lastPaintMeters.x;
    const y0 = lastPaintMeters.y;
    const x1 = currentMouseMeters.x;
    const y1 = currentMouseMeters.y;
    
    const dx = x1 - x0;
    const dy = y1 - y0;
    const distance = Math.sqrt(dx * dx + dy * dy);
    
    // Step size: 1/4 of brush radius (ensure smooth overlap)
    const stepSize = Math.max(2.0, brushRadiusMeters / 4.0);
    const numSteps = Math.max(1, Math.ceil(distance / stepSize));
    
    for (let step = 0; step < numSteps; step++) {
        const t = numSteps === 1 ? 1 : step / (numSteps - 1);
        const px = x0 + dx * t;
        const py = y0 + dy * t;
        
        if (applyBrush(px, py, deltaTime / numSteps)) {
            changed = true;
        }
    }
    
    lastPaintMeters.x = x1;
    lastPaintMeters.y = y1;
    
    if (changed) {
        redrawCanvas2D();
        updateTerrainGeometryVertices();
    }
    
    paintRequestId = requestAnimationFrame(paintLoop);
}

function applyBrush(mx, my, deltaTime) {
    // mx, my in meters (0 to 8192)
    const S = gridWidth;
    const scale = MAP_SIZE / S;
    const rPix = brushRadiusMeters / scale;
    
    const centerX = mx / scale;
    const centerY = my / scale;
    
    const xMin = Math.max(0, Math.floor(centerX - rPix));
    const xMax = Math.min(S - 1, Math.ceil(centerX + rPix));
    const yMin = Math.max(0, Math.floor(centerY - rPix));
    const yMax = Math.min(S - 1, Math.ceil(centerY + rPix));
    
    let heightsChanged = false;
    
    let heightsBackup = null;
    if (activeTool === 'smooth') {
        heightsBackup = new Float32Array(heights);
    }
    
    for (let y = yMin; y <= yMax; y++) {
        for (let x = xMin; x <= xMax; x++) {
            const dx = x - centerX;
            const dy = y - centerY;
            const dist = Math.sqrt(dx*dx + dy*dy);
            
            if (dist < rPix) {
                // Cosine falloff weight
                const t = dist / rPix;
                const w = 0.5 * (1 + Math.cos(Math.PI * t)); // 1 at center, 0 at boundary
                
                const idx = y * S + x;
                
                if (activeTool === 'raise') {
                    // Raise height (up to 30m/s at center at full strength)
                    const prev = heights[idx];
                    heights[idx] = Math.min(650, heights[idx] + brushStrength * w * deltaTime * 30);
                    if (heights[idx] !== prev) heightsChanged = true;
                } else if (activeTool === 'lower') {
                    // Lower height
                    const prev = heights[idx];
                    heights[idx] = Math.max(0, heights[idx] - brushStrength * w * deltaTime * 30);
                    if (heights[idx] !== prev) heightsChanged = true;
                } else if (activeTool === 'flatten') {
                    // Flatten towards target
                    const diff = targetHeight - heights[idx];
                    if (Math.abs(diff) > 0.001) {
                        const lerpFactor = Math.min(1.0, brushStrength * w * deltaTime * 5);
                        heights[idx] += diff * lerpFactor;
                        heightsChanged = true;
                    }
                } else if (activeTool === 'smooth') {
                    // Smooth (Gaussian blur approximation)
                    const x0 = Math.max(0, x - 1);
                    const x1 = Math.min(S - 1, x + 1);
                    const y0 = Math.max(0, y - 1);
                    const y1 = Math.min(S - 1, y + 1);
                    
                    const avg = (
                        heightsBackup[y0 * S + x0] + heightsBackup[y0 * S + x] + heightsBackup[y0 * S + x1] +
                        heightsBackup[y * S + x0]                           + heightsBackup[y * S + x1] +
                        heightsBackup[y1 * S + x0] + heightsBackup[y1 * S + x] + heightsBackup[y1 * S + x1]
                    ) / 8;
                    
                    const smoothDiff = avg - heightsBackup[idx];
                    if (Math.abs(smoothDiff) > 0.001) {
                        const lerpFactor = Math.min(1.0, brushStrength * w * deltaTime * 5);
                        heights[idx] += smoothDiff * lerpFactor;
                        heightsChanged = true;
                    }
                }
            }
        }
    }
    
    return heightsChanged;
}

// --- Ramp Application Tool ---
window.applyRampTool = function() {
    if (!rampStart || !rampEnd) {
        alert("Por favor, fija los puntos de inicio y fin de la rampa primero.");
        return;
    }
    
    showLoading("Aplicando rampa...");
    
    setTimeout(() => {
        const hStart = parseFloat(document.getElementById('ramp-height-start').value) || 0;
        const hEnd = parseFloat(document.getElementById('ramp-height-end').value) || 0;
        const rWidth = parseFloat(document.getElementById('ramp-width-m').value) || 20;
        const rMargin = parseFloat(document.getElementById('ramp-margin-m').value) || 40;
        
        const S = gridWidth;
        const scale = MAP_SIZE / S;
        
        // Line calculations (meters)
        const x1 = rampStart.x, y1 = rampStart.y;
        const x2 = rampEnd.x, y2 = rampEnd.y;
        
        const dx = x2 - x1;
        const dy = y2 - y1;
        const len = Math.sqrt(dx*dx + dy*dy);
        
        if (len < 5) {
            alert("Los puntos de inicio y fin de la rampa están demasiado juntos.");
            hideLoading();
            return;
        }
        
        // Walk grid and project onto line segment
        for (let i = 0; i < S; i++) {
            for (let j = 0; j < S; j++) {
                const px = j * scale;
                const py = i * scale;
                
                // Vector P1 -> P
                const vx = px - x1;
                const vy = py - y1;
                
                // Project onto P1 -> P2
                let t = (vx * dx + vy * dy) / (len * len);
                t = Math.max(0, Math.min(1, t)); // Clamped to segment
                
                // Closest point on line
                const cx = x1 + t * dx;
                const cy = y1 + t * dy;
                
                // Distance to line
                const d = Math.sqrt((px - cx)**2 + (py - cy)**2);
                
                const rampLimit = rWidth / 2;
                const marginLimit = rampLimit + rMargin;
                
                if (d <= marginLimit) {
                    const targetRoadH = hStart + (hEnd - hStart) * t;
                    const idx = i * S + j;
                    
                    if (d <= rampLimit) {
                        heights[idx] = targetRoadH; // Flat road bed
                    } else {
                        // Smooth blend shoulder
                        const u = (d - rampLimit) / rMargin;
                        const w = 0.5 * (1 + Math.cos(Math.PI * u)); // 1 to 0
                        heights[idx] = targetRoadH * w + heights[idx] * (1 - w);
                    }
                }
            }
        }
        
        redrawCanvas2D();
        buildTerrain3DMesh();
        
        // Clear ramp points
        rampStart = null;
        rampEnd = null;
        elRampStatus.innerText = "Rampa aplicada. Puntos restablecidos.";
        redrawOSM2D();
        hideLoading();
    }, 50);
};

// --- OSM Vector Editor Event Handling ---
function handleOSMClick(xMeters, zMeters) {
    const clickRadius = 50; // meters to click a node
    
    // Mode Select Node/Way
    if (activeTool === 'osm-select') {
        // Find nearest node
        let closestNode = null;
        let minDist = clickRadius;
        
        Object.values(osmNodes).forEach(node => {
            const d = Math.sqrt((node.x - xMeters)**2 + (node.z - zMeters)**2);
            if (d < minDist) {
                minDist = d;
                closestNode = node;
            }
        });
        
        if (closestNode) {
            activeSelectedNode = closestNode;
            // Highlight parent way
            const parentWay = oswaysContainingNode(closestNode.id)[0];
            selectWay(parentWay);
            redrawOSM2D();
            return;
        }
        
        // If no node clicked, check if we clicked a way segment
        let closestWay = null;
        let minWayDist = 80; // meters tolerance
        
        osmWays.forEach(way => {
            if (way.nodeRefs.length < 2) return;
            for (let i = 0; i < way.nodeRefs.length - 1; i++) {
                const n1 = osmNodes[way.nodeRefs[i]];
                const n2 = osmNodes[way.nodeRefs[i+1]];
                if (!n1 || !n2) continue;
                
                const d = distToSegment(xMeters, zMeters, n1.x, n1.z, n2.x, n2.z);
                if (d < minWayDist) {
                    minWayDist = d;
                    closestWay = way;
                }
            }
        });
        
        if (closestWay) {
            selectWay(closestWay);
            activeSelectedNode = null;
        } else {
            selectWay(null);
            activeSelectedNode = null;
        }
        redrawOSM2D();
    }
    
    // Mode Drawing Node/Way
    if (activeTool === 'osm-draw') {
        // Create new node
        const nid = nextNodeId--;
        const lat = MAX_LAT - (zMeters / PLAYABLE_SIZE) * (MAX_LAT - MIN_LAT); // approximated map coordinates
        const lon = MIN_LON + (xMeters / PLAYABLE_SIZE) * (MAX_LON - MIN_LON);
        
        const node = {
            id: nid.toString(),
            lat: lat,
            lon: lon,
            x: xMeters,
            z: zMeters
        };
        
        osmNodes[node.id] = node;
        activeDrawPath.push(node.id);
        
        updateStatusToolHUD(`Añadiendo way (${activeDrawPath.length} pts)... ENTER para finalizar.`);
        redrawOSM2D();
    }
}

function oswaysContainingNode(nodeId) {
    return osmWays.filter(w => w.nodeRefs.includes(nodeId));
}

function distToSegment(px, py, x1, y1, x2, y2) {
    const dx = x2 - x1;
    const dy = y2 - y1;
    const l2 = dx*dx + dy*dy;
    if (l2 === 0) return Math.sqrt((px - x1)**2 + (py - y1)**2);
    
    let t = ((px - x1) * dx + (py - y1) * dy) / l2;
    t = Math.max(0, Math.min(1, t));
    
    return Math.sqrt((px - (x1 + t * dx))**2 + (py - (y1 + t * dy))**2);
}

function finishOSMWayDrawing() {
    if (activeDrawPath.length < 2) {
        // Cancel if too few nodes
        activeDrawPath.forEach(nid => delete osmNodes[nid]);
        activeDrawPath = [];
        redrawOSM2D();
        updateStatusToolHUD("");
        return;
    }
    
    const wid = nextWayId--;
    const closed = document.getElementById('draw-closed').checked;
    const presetType = document.getElementById('way-preset-type').value;
    
    const tags = {};
    if (presetType === 'wood') tags.natural = 'wood';
    else if (presetType === 'water') tags.natural = 'water';
    else if (presetType === 'farmyard') tags.landuse = 'farmyard';
    else if (presetType === 'highway') tags.highway = 'road';
    
    // Close polygon if requested
    if (closed && activeDrawPath[0] !== activeDrawPath[activeDrawPath.length - 1]) {
        activeDrawPath.push(activeDrawPath[0]);
    }
    
    const newWay = {
        id: wid.toString(),
        tags: tags,
        nodeRefs: [...activeDrawPath]
    };
    
    osmWays.push(newWay);
    activeDrawPath = [];
    selectWay(newWay);
    
    updateStatusToolHUD("");
    redrawOSM2D();
    rebuildOsmOverlays3D();
}

function selectWay(way) {
    selectedWay = way;
    if (way) {
        elTagsPanel.style.display = 'block';
        elNoSelectionMsg.style.display = 'none';
        document.getElementById('selected-way-id').innerText = way.id;
        document.getElementById('selected-way-nodes-count').innerText = way.nodeRefs.length;
        
        // Populate Tags UI
        elTagsList.innerHTML = '';
        Object.entries(way.tags).forEach(([k, v]) => {
            const item = document.createElement('div');
            item.className = 'tag-item';
            item.innerHTML = `
                <span class="tag-key-val"><strong>${k}</strong> = ${v}</span>
                <span class="tag-delete" onclick="window.removeTagFromSelectedWay('${k}')">&times;</span>
            `;
            elTagsList.appendChild(item);
        });
    } else {
        elTagsPanel.style.display = 'none';
        elNoSelectionMsg.style.display = 'block';
    }
}

window.removeTagFromSelectedWay = function(key) {
    if (selectedWay) {
        delete selectedWay.tags[key];
        selectWay(selectedWay);
        redrawOSM2D();
        rebuildOsmOverlays3D();
    }
};

window.addTagToSelectedWay = function() {
    if (!selectedWay) return;
    const k = document.getElementById('new-tag-key').value.trim();
    const v = document.getElementById('new-tag-val').value.trim();
    
    if (k && v) {
        selectedWay.tags[k] = v;
        document.getElementById('new-tag-key').value = '';
        document.getElementById('new-tag-val').value = '';
        selectWay(selectedWay);
        redrawOSM2D();
        rebuildOsmOverlays3D();
    }
};

window.deleteSelectedWay = function() {
    if (!selectedWay) return;
    
    // Remove references
    const refs = selectedWay.nodeRefs;
    osmWays = osmWays.filter(w => w !== selectedWay);
    
    // Clean orphaned nodes
    refs.forEach(nid => {
        const contains = osmWays.some(w => w.nodeRefs.includes(nid));
        if (!contains) {
            delete osmNodes[nid];
        }
    });
    
    selectWay(null);
    activeSelectedNode = null;
    redrawOSM2D();
    rebuildOsmOverlays3D();
};

// --- Loading Panel Helpers ---
function showLoading(text) {
    const overlay = document.getElementById('loading-overlay');
    document.getElementById('loading-text').innerText = text;
    overlay.classList.add('active');
}

function hideLoading() {
    document.getElementById('loading-overlay').classList.remove('active');
}

// --- Menu Tab Selector ---
window.switchTab = function(tabId) {
    document.querySelectorAll('.sidebar .tab-btn').forEach(btn => btn.classList.remove('active'));
    document.querySelectorAll('.sidebar .tab-content').forEach(content => content.style.display = 'none');
    
    document.getElementById(tabId).style.display = 'block';
    // Highlight corresponding tab button
    if (tabId === 'tab-dem') document.querySelector('.sidebar .tab-btn:nth-child(1)').classList.add('active');
    if (tabId === 'tab-osm') document.querySelector('.sidebar .tab-btn:nth-child(2)').classList.add('active');
    if (tabId === 'tab-io') document.querySelector('.sidebar .tab-btn:nth-child(3)').classList.add('active');
};

// --- Active Tool Dispatcher ---
window.setDEMTool = function(tool) {
    activeTool = tool;
    
    // Update toolbar active tool text
    let label = "Elevación (Elevar Pincel)";
    if (tool === 'lower') label = "Elevación (Bajar Pincel)";
    if (tool === 'flatten') label = "Elevación (Aplanar Pincel)";
    if (tool === 'smooth') label = "Elevación (Suavizar Pincel)";
    if (tool === 'ramp-start') label = "Fijar inicio de Rampa...";
    if (tool === 'ramp-end') label = "Fijar fin de Rampa...";
    elActiveToolDisplay.innerText = label;
    
    document.querySelectorAll('#brush-tools .toggle-btn').forEach(btn => btn.classList.remove('active'));
    if (tool === 'raise') document.querySelector('#brush-tools .toggle-btn:nth-child(1)').classList.add('active');
    if (tool === 'lower') document.querySelector('#brush-tools .toggle-btn:nth-child(2)').classList.add('active');
    if (tool === 'flatten') document.querySelector('#brush-tools .toggle-btn:nth-child(3)').classList.add('active');
    if (tool === 'smooth') document.querySelector('#brush-tools .toggle-btn:nth-child(4)').classList.add('active');
    
    // Toggle flatten parameter display
    document.getElementById('flatten-height-row').style.display = (tool === 'flatten') ? 'block' : 'none';
};

window.setOSMTool = function(tool) {
    activeTool = (tool === 'draw') ? 'osm-draw' : 'osm-select';
    
    let label = (tool === 'draw') ? "Vectorial (Crear Way)" : "Vectorial (Editar Nodos)";
    elActiveToolDisplay.innerText = label;
    
    document.querySelectorAll('#osm-tools .toggle-btn').forEach(btn => btn.classList.remove('active'));
    if (tool === 'draw') {
        document.querySelector('#osm-tools .toggle-btn:nth-child(2)').classList.add('active');
        document.getElementById('draw-closed-row').style.display = 'block';
        document.getElementById('draw-type-row').style.display = 'block';
    } else {
        document.querySelector('#osm-tools .toggle-btn:nth-child(1)').classList.add('active');
        document.getElementById('draw-closed-row').style.display = 'none';
        document.getElementById('draw-type-row').style.display = 'none';
        
        // Cancel active draw if switches
        if (activeDrawPath.length > 0) {
            activeDrawPath.forEach(nid => delete osmNodes[nid]);
            activeDrawPath = [];
            redrawOSM2D();
            updateStatusToolHUD("");
        }
    }
};

window.updateParamValue = function(input, suffix = 'm') {
    const id = input.id;
    let labelId = id.replace('param-', 'val-').replace('brush-', 'val-');
    if (id === 'brush-target-height') labelId = 'val-brush-target-height';
    const label = document.getElementById(labelId);
    if (label) {
        label.innerText = input.value + suffix;
    }
    
    if (id === 'brush-size') brushRadiusMeters = parseFloat(input.value);
    if (id === 'brush-strength') brushStrength = parseFloat(input.value);
};

window.sampleNextPixelHeight = function() {
    isSamplingHeight = true;
    elActiveToolDisplay.innerText = "Haz clic en el mapa para muestrear la altura...";
};

function updateStatusToolHUD(text) {
    const el = document.getElementById('hud-tool-info-box');
    if (text) {
        el.style.display = 'flex';
        document.getElementById('hud-tool-val').innerText = text;
    } else {
        el.style.display = 'none';
    }
}

// --- Help Modal Panels ---
window.showHelp = function() {
    document.getElementById('help-modal').classList.add('active');
};

window.hideHelp = function() {
    document.getElementById('help-modal').classList.remove('active');
};

// --- Three.js 3D Preview Engine ---
function init3DPreview() {
    const container = document.getElementById('three-canvas-container');
    
    scene3D = new THREE.Scene();
    scene3D.background = new THREE.Color(0x090a0d);
    
    camera3D = new THREE.PerspectiveCamera(45, container.clientWidth / container.clientHeight, 10, 20000);
    camera3D.position.set(0, 3000, 4500);
    
    renderer3D = new THREE.WebGLRenderer({ antialias: true });
    renderer3D.setSize(container.clientWidth, container.clientHeight);
    renderer3D.shadowMap.enabled = true;
    container.appendChild(renderer3D.domElement);
    
    controls3D = new THREE.OrbitControls(camera3D, renderer3D.domElement);
    controls3D.enableDamping = true;
    controls3D.dampingFactor = 0.05;
    controls3D.maxPolarAngle = Math.PI / 2 - 0.05;
    controls3D.minDistance = 50;
    controls3D.maxDistance = 12000;
    controls3D.target.set(0, 100, 0);
    controls3D.update();
    
    // Lighting
    const ambLight = new THREE.AmbientLight(0xffffff, 0.45);
    scene3D.add(ambLight);
    
    const sunLight = new THREE.DirectionalLight(0xffffff, 0.8);
    sunLight.position.set(4000, 5000, 3000);
    scene3D.add(sunLight);
    
    // Playable area wire segments
    const playOffset = (MAP_SIZE - PLAYABLE_SIZE) / 2;
    const playMin = -PLAYABLE_SIZE / 2;
    const playMax = PLAYABLE_SIZE / 2;
    const boxGeom = new THREE.BufferGeometry();
    const boxVerts = [
        // floor
        playMin, 0, playMin,  playMax, 0, playMin,
        playMax, 0, playMin,  playMax, 0, playMax,
        playMax, 0, playMax,  playMin, 0, playMax,
        playMin, 0, playMax,  playMin, 0, playMin,
        // ceiling
        playMin, 400, playMin,  playMax, 400, playMin,
        playMax, 400, playMin,  playMax, 400, playMax,
        playMax, 400, playMax,  playMin, 400, playMax,
        playMin, 400, playMax,  playMin, 400, playMin,
        // pillars
        playMin, 0, playMin,  playMin, 400, playMin,
        playMax, 0, playMin,  playMax, 400, playMin,
        playMax, 0, playMax,  playMax, 400, playMax,
        playMin, 0, playMax,  playMin, 400, playMax,
    ];
    boxGeom.setAttribute('position', new THREE.Float32BufferAttribute(boxVerts, 3));
    const boxMat = new THREE.LineBasicMaterial({ color: 0x4f46e5, transparent: true, opacity: 0.6 });
    playableBox3D = new THREE.LineSegments(boxGeom, boxMat);
    playableBox3D.visible = false;
    scene3D.add(playableBox3D);
    
    // Add terrain mesh
    buildTerrain3DMesh();
    
    // Resize handler
    window.addEventListener('resize', onResize3D);
    
    animate3D();
}

function onResize3D() {
    const container = document.getElementById('three-canvas-container');
    if (!container || !renderer3D) return;
    camera3D.aspect = container.clientWidth / container.clientHeight;
    camera3D.updateProjectionMatrix();
    renderer3D.setSize(container.clientWidth, container.clientHeight);
}

function buildTerrain3DMesh() {
    if (terrainMesh3D) {
        scene3D.remove(terrainMesh3D);
        terrainGeom3D.dispose();
    }
    
    const res = gridWidth;
    terrainGeom3D = new THREE.PlaneGeometry(MAP_SIZE, MAP_SIZE, res - 1, res - 1);
    
    updateTerrainGeometryVertices();
    
    // Rotate and compute normals
    terrainGeom3D.rotateX(-Math.PI / 2);
    terrainGeom3D.computeVertexNormals();
    
    // Materials
    updateTerrainMaterial3D();
    
    terrainMesh3D = new THREE.Mesh(terrainGeom3D, terrainMaterial3D);
    scene3D.add(terrainMesh3D);
}

function updateTerrainGeometryVertices() {
    if (!terrainGeom3D) return;
    
    const posAttr = terrainGeom3D.attributes.position;
    const count = posAttr.count;
    const res = gridWidth;
    
    // In Three.js PlaneGeometry, vertices go row by row
    for (let i = 0; i < count; i++) {
        // Map vertices index to grid index
        // Plane X, Y coordinates before rotation go from -MAP_SIZE/2 to MAP_SIZE/2
        const vx = posAttr.getX(i);
        const vy = posAttr.getY(i);
        
        // Map vertex coordinate to heightmap pixel grid
        const u = (vx + MAP_SIZE / 2) / MAP_SIZE;
        const v = 1 - (vy + MAP_SIZE / 2) / MAP_SIZE;
        
        const gx = Math.max(0, Math.min(res - 1, Math.round(u * (res - 1))));
        const gy = Math.max(0, Math.min(res - 1, Math.round(v * (res - 1))));
        
        const heightVal = heights[gy * res + gx];
        
        // Set height in displaced axis
        // Plane geometry is flat on X, Y, vertex displacement sits on Z before rotation
        posAttr.setZ(i, heightVal * exaggeration3D);
    }
    posAttr.needsUpdate = true;
    terrainGeom3D.computeVertexNormals();
    
    // Update colors if elevation view mode
    if (renderMode3D === 'elevation') {
        rebuildVertexColors3D();
    }
}

function updateTerrainMaterial3D() {
    if (renderMode3D === 'texture') {
        // Generate high dynamic texture from 2D Canvas
        const texture = new THREE.CanvasTexture(elHeightCanvas);
        terrainMaterial3D = new THREE.MeshStandardMaterial({
            map: texture,
            roughness: 0.85,
            metalness: 0.05,
            flatShading: false
        });
    } else if (renderMode3D === 'elevation') {
        rebuildVertexColors3D();
        terrainMaterial3D = new THREE.MeshStandardMaterial({
            vertexColors: true,
            roughness: 0.8,
            metalness: 0.05
        });
    } else {
        // Wireframe mesh
        terrainMaterial3D = new THREE.MeshBasicMaterial({
            color: 0x6366f1,
            wireframe: true
        });
    }
    
    if (terrainMesh3D) {
        terrainMesh3D.material = terrainMaterial3D;
    }
}

function rebuildVertexColors3D() {
    if (!terrainGeom3D) return;
    
    const count = terrainGeom3D.attributes.position.count;
    const colors = [];
    const minHeight = 0;
    const maxHeight = 300;
    
    const colorRamp = [
        { h: 0, c: new THREE.Color(0x1a3a1e) }, // dark valley green
        { h: 15, c: new THREE.Color(0x2d6a3f) }, // grass green
        { h: 100, c: new THREE.Color(0xd4a373) }, // yellow clay
        { h: 220, c: new THREE.Color(0x7f5539) }, // mountain brown
        { h: 300, c: new THREE.Color(0xffffff) }  // peak white
    ];
    
    const posAttr = terrainGeom3D.attributes.position;
    
    for (let i = 0; i < count; i++) {
        // Get the real height (before exaggeration)
        // Since geometry was rotated, real height sits in Y axis of Three.js space now
        const yVal = posAttr.getY(i) / exaggeration3D;
        
        const col = new THREE.Color(0xffffff);
        if (yVal <= colorRamp[0].h) {
            col.copy(colorRamp[0].c);
        } else if (yVal >= colorRamp[colorRamp.length - 1].h) {
            col.copy(colorRamp[colorRamp.length - 1].c);
        } else {
            for (let j = 0; j < colorRamp.length - 1; j++) {
                const lower = colorRamp[j];
                const upper = colorRamp[j+1];
                if (yVal >= lower.h && yVal <= upper.h) {
                    const t = (yVal - lower.h) / (upper.h - lower.h);
                    col.copy(lower.c).lerp(upper.c, t);
                    break;
                }
            }
        }
        colors.push(col.r, col.g, col.b);
    }
    
    terrainGeom3D.setAttribute('color', new THREE.Float32BufferAttribute(colors, 3));
    terrainGeom3D.attributes.color.needsUpdate = true;
}

function rebuildOsmOverlays3D() {
    if (osmLines3DGroup) {
        scene3D.remove(osmLines3DGroup);
    }
    
    osmLines3DGroup = new THREE.Group();
    
    function getMapHeight(mx, mz) {
        const u = Math.max(0, Math.min(1, mx / MAP_SIZE));
        const v = Math.max(0, Math.min(1, mz / MAP_SIZE));
        
        const gx = Math.max(0, Math.min(gridWidth - 1, Math.floor(u * (gridWidth - 1))));
        const gy = Math.max(0, Math.min(gridHeight - 1, Math.floor(v * (gridHeight - 1))));
        
        return heights[gy * gridWidth + gx];
    }
    
    osmWays.forEach(way => {
        if (way.nodeRefs.length < 2) return;
        
        let color = 0xffffff;
        if (way.tags.natural === 'wood' || way.tags.landuse === 'forest') color = 0x22c55e;
        else if (way.tags.landuse === 'farmyard') color = 0xeab308;
        else if (way.tags.natural === 'water' || way.tags.water) color = 0x2563eb;
        else if (way.tags.highway) color = 0x9ca3af;
        
        const points = [];
        for (const nid of way.nodeRefs) {
            const node = osmNodes[nid];
            if (!node) continue;
            
            // Map coordinates centered to match 3D Plane coordinates (-4096 to 4096)
            const x3d = node.x - MAP_SIZE / 2;
            const z3d = node.z - MAP_SIZE / 2;
            const hVal = getMapHeight(node.x, node.z);
            
            points.push(new THREE.Vector3(x3d, hVal * exaggeration3D + 2.5, z3d)); // Raised 2.5m to prevent z-fighting
        }
        
        const geometry = new THREE.BufferGeometry().setFromPoints(points);
        const material = new THREE.LineBasicMaterial({
            color: color,
            linewidth: 3,
            transparent: true,
            opacity: 0.95
        });
        
        // Loop standard closed geometries
        const line = (way.nodeRefs[0] === way.nodeRefs[way.nodeRefs.length - 1]) 
            ? new THREE.LineLoop(geometry, material)
            : new THREE.Line(geometry, material);
            
        osmLines3DGroup.add(line);
    });
    
    scene3D.add(osmLines3DGroup);
}

window.trigger3DRebuild = function() {
    showLoading("Reconstruyendo escena 3D...");
    setTimeout(() => {
        buildTerrain3DMesh();
        rebuildOsmOverlays3D();
        hideLoading();
    }, 50);
};

window.setRenderMode3D = function(mode) {
    renderMode3D = mode;
    document.querySelectorAll('#render-modes-3d .toggle-btn').forEach(btn => btn.classList.remove('active'));
    if (mode === 'texture') document.querySelector('#render-modes-3d .toggle-btn:nth-child(1)').classList.add('active');
    if (mode === 'elevation') document.querySelector('#render-modes-3d .toggle-btn:nth-child(2)').classList.add('active');
    if (mode === 'wireframe') document.querySelector('#render-modes-3d .toggle-btn:nth-child(3)').classList.add('active');
    
    updateTerrainMaterial3D();
};

window.updateExaggeration3D = function(val) {
    exaggeration3D = parseFloat(val);
    document.getElementById('val-exaggeration-3d').innerText = val + 'x';
    updateTerrainGeometryVertices();
    rebuildOsmOverlays3D();
};

window.togglePlayableBox3D = function(visible) {
    if (playableBox3D) {
        playableBox3D.visible = visible;
    }
};

window.resetCamera3D = function() {
    if (camera3D && controls3D) {
        camera3D.position.set(0, 3000, 4500);
        controls3D.target.set(0, 100, 0);
        controls3D.update();
    }
};

let lastFrameTime = performance.now();
const keysPressed = {};

function updateCameraKeyboard(deltaTime) {
    if (!camera3D || !controls3D) return;
    
    // Check if typing in inputs
    const activeEl = document.activeElement;
    if (activeEl && (activeEl.tagName === 'INPUT' || activeEl.tagName === 'SELECT' || activeEl.tagName === 'TEXTAREA')) {
        return;
    }
    
    const speed = 1500 * deltaTime; // meters per second
    
    const dir = new THREE.Vector3();
    camera3D.getWorldDirection(dir);
    
    // Horizontal direction to keep movement parallel to terrain plane
    const dirH = new THREE.Vector3(dir.x, 0, dir.z).normalize();
    
    const right = new THREE.Vector3();
    right.crossVectors(dirH, camera3D.up).normalize();
    
    const moveVector = new THREE.Vector3(0, 0, 0);
    
    if (keysPressed['w'] || keysPressed['arrowup']) {
        moveVector.addScaledVector(dirH, speed);
    }
    if (keysPressed['s'] || keysPressed['arrowdown']) {
        moveVector.addScaledVector(dirH, -speed);
    }
    if (keysPressed['a'] || keysPressed['arrowleft']) {
        moveVector.addScaledVector(right, -speed);
    }
    if (keysPressed['d'] || keysPressed['arrowright']) {
        moveVector.addScaledVector(right, speed);
    }
    if (keysPressed['q']) {
        moveVector.y += speed; // fly up
    }
    if (keysPressed['e']) {
        moveVector.y -= speed; // fly down
    }
    
    if (moveVector.lengthSq() > 0) {
        camera3D.position.add(moveVector);
        controls3D.target.add(moveVector);
        controls3D.update();
    }
    
    // Orbital rotation around the focus target (R: clockwise, F: counter-clockwise)
    if (keysPressed['r']) {
        const theta = 1.2 * deltaTime; // radians/sec
        const offset = camera3D.position.clone().sub(controls3D.target);
        const nx = offset.x * Math.cos(theta) - offset.z * Math.sin(theta);
        const nz = offset.x * Math.sin(theta) + offset.z * Math.cos(theta);
        camera3D.position.set(nx + controls3D.target.x, offset.y + controls3D.target.y, nz + controls3D.target.z);
        controls3D.update();
    }
    if (keysPressed['f']) {
        const theta = -1.2 * deltaTime;
        const offset = camera3D.position.clone().sub(controls3D.target);
        const nx = offset.x * Math.cos(theta) - offset.z * Math.sin(theta);
        const nz = offset.x * Math.sin(theta) + offset.z * Math.cos(theta);
        camera3D.position.set(nx + controls3D.target.x, offset.y + controls3D.target.y, nz + controls3D.target.z);
        controls3D.update();
    }
}

function animate3D() {
    requestAnimationFrame(animate3D);
    
    const now = performance.now();
    const deltaTime = Math.min(0.1, (now - lastFrameTime) / 1000.0);
    lastFrameTime = now;
    
    updateCameraKeyboard(deltaTime);
    
    if (controls3D) controls3D.update();
    if (renderer3D && scene3D && camera3D) {
        renderer3D.render(scene3D, camera3D);
    }
}

// --- File I/O Implementations (Drag & Drop, Import & Export) ---

// 1. Export DEM Map in 16-bit Grayscale PNG format
window.exportDEM = function() {
    const resolution = parseInt(document.getElementById('export-res').value);
    showLoading(`Exportando DEM (${resolution}px 16-bits)...`);
    
    setTimeout(() => {
        // Upscale heights data array to target export resolution if needed
        let exportHeights = heights;
        
        if (resolution !== gridWidth) {
            exportHeights = new Float32Array(resolution * resolution);
            const w = gridWidth;
            const h = gridHeight;
            
            // Bilinear interpolation upscaling
            for (let y = 0; y < resolution; y++) {
                for (let x = 0; x < resolution; x++) {
                    const u = x / (resolution - 1);
                    const v = y / (resolution - 1);
                    
                    const px = u * (w - 1);
                    const py = v * (h - 1);
                    const x0 = Math.floor(px);
                    const y0 = Math.floor(py);
                    const x1 = Math.min(x0 + 1, w - 1);
                    const y1 = Math.min(y0 + 1, h - 1);
                    const tx = px - x0;
                    const ty = py - y0;
                    
                    const h00 = heights[y0 * w + x0];
                    const h10 = heights[y0 * w + x1];
                    const h01 = heights[y1 * w + x0];
                    const h11 = heights[y1 * w + x1];
                    
                    const h0 = h00 * (1 - tx) + h10 * tx;
                    const h1 = h01 * (1 - tx) + h11 * tx;
                    exportHeights[y * resolution + x] = h0 * (1 - ty) + h1 * ty;
                }
            }
        }
        
        try {
            const pngBytes = create16BitGrayscalePNG(resolution, resolution, exportHeights);
            
            // Trigger browser download
            const blob = new Blob([pngBytes], { type: 'image/png' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `map_dem_edited_${resolution}.png`;
            a.click();
            URL.revokeObjectURL(url);
        } catch (e) {
            alert(`Error durante la exportación: ${e.message}`);
        }
        hideLoading();
    }, 50);
};

// 2. Export OSM Map in XML format
window.exportOSM = function() {
    showLoading("Generando XML de OSM...");
    
    setTimeout(() => {
        let xml = `<?xml version="1.0" encoding="UTF-8"?>\n`;
        xml += `<osm version="0.6" generator="Antigravity FS25 DEM-OSM Editor v1.0">\n`;
        
        // Bounding box
        xml += `  <bounds minlat="${MIN_LAT}" minlon="${MIN_LON}" maxlat="${MAX_LAT}" maxlon="${MAX_LON}"/>\n`;
        
        // Write nodes
        Object.values(osmNodes).forEach(node => {
            xml += `  <node id="${node.id}" lat="${node.lat}" lon="${node.lon}"/>\n`;
        });
        
        // Write ways
        osmWays.forEach(way => {
            xml += `  <way id="${way.id}">\n`;
            way.nodeRefs.forEach(ref => {
                xml += `    <nd ref="${ref}"/>\n`;
            });
            Object.entries(way.tags).forEach(([k, v]) => {
                xml += `    <tag k="${k}" v="${v}"/>\n`;
            });
            xml += `  </way>\n`;
        });
        
        xml += `</osm>\n`;
        
        const blob = new Blob([xml], { type: 'application/xml' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'map_edited.osm';
        a.click();
        URL.revokeObjectURL(url);
        
        hideLoading();
    }, 50);
};

// 3. Import DEM file
window.importDEM = function(input) {
    const file = input.files[0];
    if (!file) return;
    
    showLoading("Cargando imagen de altura...");
    
    const reader = new FileReader();
    reader.onload = function(e) {
        const img = new Image();
        img.src = e.target.result;
        img.onload = function() {
            // Load onto a canvas to inspect pixel colors
            const canvas = document.createElement('canvas');
            canvas.width = img.width;
            canvas.height = img.height;
            const ctx = canvas.getContext('2d');
            ctx.drawImage(img, 0, 0);
            
            const imgData = ctx.getImageData(0, 0, img.width, img.height);
            const data = imgData.data;
            
            // Check if encoding matches standard RGB 16-bit or Grayscale
            // We read and scale values to height (0 - 300 meters)
            const targetRes = gridWidth;
            const scaleX = img.width / targetRes;
            const scaleY = img.height / targetRes;
            
            // Sample heights onto heights array
            for (let y = 0; y < targetRes; y++) {
                for (let x = 0; x < targetRes; x++) {
                    const sx = Math.max(0, Math.min(img.width - 1, Math.floor(x * scaleX)));
                    const sy = Math.max(0, Math.min(img.height - 1, Math.floor(y * scaleY)));
                    const idx = (sy * img.width + sx) * 4;
                    
                    const r = data[idx];
                    const g = data[idx+1];
                    const b = data[idx+2];
                    
                    let realH = 0;
                    // Standard heuristic: if blue channel is extremely low and R and G have high values, it's likely RGB 16-bit encoded
                    if (b < 10 && (r > 0 || g > 0)) {
                        // Decode 16-bit value (in cm) and convert to meters
                        realH = (r + g * 256) / 100.0;
                    } else {
                        // Standard Grayscale 8-bit
                        const intensity = (r + g + b) / 3;
                        realH = (intensity / 255.0) * 250.0; // scale 255 intensity to 250m
                    }
                    
                    heights[y * targetRes + x] = realH;
                }
            }
            
            redrawCanvas2D();
            buildTerrain3DMesh();
            hideLoading();
        };
    };
    reader.readAsDataURL(file);
};

// 4. Import OSM File (.osm)
window.importOSM = function(input) {
    const file = input.files[0];
    if (!file) return;
    
    showLoading("Importando mapa.osm...");
    
    const reader = new FileReader();
    reader.onload = function(e) {
        try {
            const parser = new DOMParser();
            const xmlDoc = parser.parseFromString(e.target.result, "text/xml");
            
            const loadedNodes = {};
            const loadedWays = [];
            
            // Parse XML elements
            const nodes = xmlDoc.getElementsByTagName("node");
            for (let i = 0; i < nodes.length; i++) {
                const node = nodes[i];
                const id = node.getAttribute("id");
                const lat = parseFloat(node.getAttribute("lat"));
                const lon = parseFloat(node.getAttribute("lon"));
                
                // Map Latitude and Longitude to layout coordinates (meters: 0 to 8192)
                // Coordinates mapping:
                // lat -> z coord
                // lon -> x coord
                // Playable area center bounds
                const u = (lon - MIN_LON) / (MAX_LON - MIN_LON);
                const v = (MAX_LAT - lat) / (MAX_LAT - MIN_LAT);
                
                // Maps linearly relative to the center playable area of size 4096 (from 2048 to 6144)
                const px = 2048 + u * PLAYABLE_SIZE;
                const pz = 2048 + v * PLAYABLE_SIZE;
                
                loadedNodes[id] = { id, lat, lon, x: px, z: pz };
            }
            
            const ways = xmlDoc.getElementsByTagName("way");
            for (let i = 0; i < ways.length; i++) {
                const way = ways[i];
                const id = way.getAttribute("id");
                
                const nodeRefs = [];
                const nds = way.getElementsByTagName("nd");
                for (let j = 0; j < nds.length; j++) {
                    nodeRefs.push(nds[j].getAttribute("ref"));
                }
                
                const tags = {};
                const tagsList = way.getElementsByTagName("tag");
                for (let j = 0; j < tagsList.length; j++) {
                    const t = tagsList[j];
                    tags[t.getAttribute("k")] = t.getAttribute("v");
                }
                
                loadedWays.push({ id, tags, nodeRefs });
            }
            
            // Overwrite current OSM state
            osmNodes = loadedNodes;
            osmWays = loadedWays;
            
            // Track IDs to prevent collissions
            nextNodeId = Math.min(-1, ...Object.keys(osmNodes).map(k => parseInt(k)).filter(n => n < 0)) - 1;
            nextWayId = Math.min(-1, ...osmWays.map(w => parseInt(w.id)).filter(n => n < 0)) - 1;
            
            selectWay(null);
            redrawOSM2D();
            rebuildOsmOverlays3D();
            
        } catch (err) {
            alert(`Error al procesar el archivo XML: ${err.message}`);
        }
        hideLoading();
    };
    reader.readAsText(file);
};

function initSplitterResizer() {
    const resizer = document.getElementById('resizer-3d');
    const previewPanel = document.getElementById('preview-panel');
    if (!resizer || !previewPanel) return;
    
    let startX, startWidth;
    
    resizer.addEventListener('mousedown', function(e) {
        startX = e.clientX;
        startWidth = parseInt(document.defaultView.getComputedStyle(previewPanel).width, 10);
        resizer.classList.add('active');
        
        document.documentElement.addEventListener('mousemove', doDrag, false);
        document.documentElement.addEventListener('mouseup', stopDrag, false);
        e.preventDefault();
    });
    
    function doDrag(e) {
        const deltaX = e.clientX - startX;
        let newWidth = startWidth - deltaX;
        
        const minW = 150;
        const maxW = window.innerWidth - 450;
        newWidth = Math.max(minW, Math.min(maxW, newWidth));
        
        previewPanel.style.width = newWidth + 'px';
        
        onResize3D();
    }
    
    function stopDrag() {
        resizer.classList.remove('active');
        document.documentElement.removeEventListener('mousemove', doDrag, false);
        document.documentElement.removeEventListener('mouseup', stopDrag, false);
        
        onResize3D();
    }
}

// --- Initialization & UI Binding ---
window.onload = function() {
    // Canvas setup
    elHeightCanvas = document.getElementById('height-canvas');
    elVectorCanvas = document.getElementById('vector-canvas');
    ctxHeight = elHeightCanvas.getContext('2d');
    ctxVector = elVectorCanvas.getContext('2d');
    
    elHeightCanvas.width = gridWidth;
    elHeightCanvas.height = gridHeight;
    elVectorCanvas.width = elHeightCanvas.clientWidth || 600;
    elVectorCanvas.height = elHeightCanvas.clientHeight || 600;
    
    // Status UI
    elStatusCoords = document.getElementById('hud-coords');
    elStatusElevation = document.getElementById('hud-elevation');
    elStatusZone = document.getElementById('hud-zone');
    elActiveToolDisplay = document.getElementById('active-tool-display');
    elTagsPanel = document.getElementById('osm-selection-panel');
    elNoSelectionMsg = document.getElementById('osm-no-selection');
    elTagsList = document.getElementById('selected-way-tags-list');
    elRampStatus = document.getElementById('ramp-points-status');
    
    // Init arrays with base flat valley height (100.0m)
    heights.fill(100.0);
    
    // Resize vector canvas to match physical size
    const resizeObserver = new ResizeObserver(entries => {
        for (let entry of entries) {
            elVectorCanvas.width = entry.contentRect.width;
            elVectorCanvas.height = entry.contentRect.height;
            redrawOSM2D();
        }
    });
    resizeObserver.observe(document.querySelector('.canvas-stack'));
    
    // Input bindings
    bindMouseAndTouchEvents();
    
    // Init splitter resizer
    initSplitterResizer();
    
    // Generate initial procedural terrain
    window.generateBaseDEM();
    
    // Launch WebGL 3D preview
    init3DPreview();
};

// --- Mouse and Touch Controls for Canvas Stack ---
function bindMouseAndTouchEvents() {
    let mouseStartGridX = 0, mouseStartGridY = 0;
    let nodeBeingDragged = null;
    let lastTime = 0;
    
    function getMouseCoords(e) {
        const rect = elVectorCanvas.getBoundingClientRect();
        const clientX = e.touches ? e.touches[0].clientX : e.clientX;
        const clientY = e.touches ? e.touches[0].clientY : e.clientY;
        
        // Canvas relative coordinates (0 to width/height)
        const cx = clientX - rect.left;
        const cy = clientY - rect.top;
        
        // Scale to Map dimensions in meters (0 to 8192)
        const mx = (cx / rect.width) * MAP_SIZE;
        const my = (cy / rect.height) * MAP_SIZE;
        
        return { cx, cy, mx, my };
    }
    
    elVectorCanvas.addEventListener('mousedown', function(e) {
        const coords = getMouseCoords(e);
        const cellScale = MAP_SIZE / gridWidth;
        
        // A) Height sampling check
        if (isSamplingHeight) {
            const gx = Math.max(0, Math.min(gridWidth - 1, Math.round(coords.mx / cellScale)));
            const gy = Math.max(0, Math.min(gridHeight - 1, Math.round(coords.my / cellScale)));
            const sampledH = heights[gy * gridWidth + gx];
            
            document.getElementById('brush-target-height').value = sampledH.toFixed(2);
            document.getElementById('val-brush-target-height').innerText = sampledH.toFixed(2) + 'm';
            targetHeight = sampledH;
            
            isSamplingHeight = false;
            window.setDEMTool('flatten');
            return;
        }
        
        // B) Ramp points plotting
        if (activeTool === 'ramp-start') {
            rampStart = { x: coords.mx, y: coords.my };
            elRampStatus.innerText = `Inicio fijado: (${Math.round(rampStart.x)}m, ${Math.round(rampStart.y)}m)`;
            window.setDEMTool('raise');
            redrawOSM2D();
            return;
        }
        if (activeTool === 'ramp-end') {
            rampEnd = { x: coords.mx, y: coords.my };
            elRampStatus.innerText = `Ramp start & end set. Click Apply.`;
            window.setDEMTool('raise');
            redrawOSM2D();
            return;
        }
        
        // C) OSM vector interactions
        if (activeTool === 'osm-select') {
            // Check if clicking near node to drag it
            if (activeHoverNode) {
                nodeBeingDragged = activeHoverNode;
                isDraggingNode = true;
                activeSelectedNode = activeHoverNode;
                const parentWay = oswaysContainingNode(activeHoverNode.id)[0];
                selectWay(parentWay);
                return;
            }
        }
        
        // D) Manual Painting Brush initialization
        if (activeTool === 'raise' || activeTool === 'lower' || activeTool === 'flatten' || activeTool === 'smooth') {
            startPaintingLoop(coords.mx, coords.my);
        }
        
        // Single click nodes placing
        handleOSMClick(coords.mx, coords.my);
    });
    
    elVectorCanvas.addEventListener('mousemove', function(e) {
        const coords = getMouseCoords(e);
        const cellScale = MAP_SIZE / gridWidth;
        
        // X, Y grids indexes
        const gx = Math.max(0, Math.min(gridWidth - 1, Math.floor(coords.mx / cellScale)));
        const gy = Math.max(0, Math.min(gridHeight - 1, Math.floor(coords.my / cellScale)));
        
        // Update Bottom Status HUD
        const currentH = heights[gy * gridWidth + gx];
        elStatusCoords.innerText = `X: ${Math.round(coords.mx)}m | Z: ${Math.round(coords.my)}m`;
        elStatusElevation.innerText = `${currentH.toFixed(2)}m`;
        
        // Zone determination
        const playOffset = (MAP_SIZE - PLAYABLE_SIZE) / 2;
        const inside = (coords.mx >= playOffset && coords.mx <= playOffset + PLAYABLE_SIZE &&
                        coords.my >= playOffset && coords.my <= playOffset + PLAYABLE_SIZE);
        
        if (!inside) {
            elStatusZone.innerText = "Fondo No Jugable";
            elStatusZone.style.color = "#ef4444";
        } else {
            // Check lake
            const dxL = coords.mx - 5800;
            const dyL = coords.my - 5800;
            const dL = Math.max(Math.abs(dxL), Math.abs(dyL));
            if (dL <= 90) {
                elStatusZone.innerText = "Lago / Reserva (225m)";
                elStatusZone.style.color = "#2563eb";
            } else {
                elStatusZone.innerText = "Área Jugable";
                elStatusZone.style.color = "#10b981";
            }
        }
        
        // A) Handles active node dragging
        if (isDraggingNode && nodeBeingDragged) {
            nodeBeingDragged.x = coords.mx;
            nodeBeingDragged.z = coords.my;
            nodeBeingDragged.lat = MAX_LAT - (coords.my / PLAYABLE_SIZE) * (MAX_LAT - MIN_LAT);
            nodeBeingDragged.lon = MIN_LON + (coords.mx / PLAYABLE_SIZE) * (MAX_LON - MIN_LON);
            
            redrawOSM2D();
            rebuildOsmOverlays3D();
            return;
        }
        
        // B) Handles active node hover highlight
        if (activeTool === 'osm-select' && !isDraggingNode) {
            let closest = null;
            let minDist = 40; // meters tolerance
            Object.values(osmNodes).forEach(node => {
                const d = Math.sqrt((node.x - coords.mx)**2 + (node.z - coords.my)**2);
                if (d < minDist) {
                    minDist = d;
                    closest = node;
                }
            });
            
            if (closest !== activeHoverNode) {
                activeHoverNode = closest;
                redrawOSM2D();
            }
        }
        
        // C) Draw Brush circle outline dynamically
        redrawOSM2D();
        drawBrushCursor2D(coords.cx, coords.cy);
        
        // D) Apply paint tick
        if (isPainting) {
            currentMouseMeters.x = coords.mx;
            currentMouseMeters.y = coords.my;
        }
    });
    
    window.addEventListener('mouseup', function() {
        if (isPainting) {
            isPainting = false;
            if (paintRequestId) {
                cancelAnimationFrame(paintRequestId);
                paintRequestId = null;
            }
            // Update complete standard mesh normals on release
            if (terrainGeom3D) {
                terrainGeom3D.computeVertexNormals();
                updateTerrainMaterial3D(); // regenerate standard texture maps
            }
        }
        
        if (isDraggingNode) {
            isDraggingNode = false;
            nodeBeingDragged = null;
            rebuildOsmOverlays3D();
        }
    });
    
    // Keyboard listener (ENTER to complete OSM drawing, ESC to cancel, WASDQE for 3D navigation)
    window.addEventListener('keydown', function(e) {
        keysPressed[e.key.toLowerCase()] = true;
        
        if (e.key === 'Enter') {
            if (activeTool === 'osm-draw') {
                finishOSMWayDrawing();
            }
        }
        if (e.key === 'Escape') {
            if (activeTool === 'osm-draw') {
                activeDrawPath.forEach(nid => delete osmNodes[nid]);
                activeDrawPath = [];
                redrawOSM2D();
                updateStatusToolHUD("");
            }
        }
        if (e.key === 'Delete' || e.key === 'Backspace') {
            // Delete node or way if selected
            if (activeSelectedNode && activeTool === 'osm-select') {
                const nid = activeSelectedNode.id;
                delete osmNodes[nid];
                // Remove from all ways refs
                osmWays.forEach(way => {
                    way.nodeRefs = way.nodeRefs.filter(ref => ref !== nid);
                });
                // Clean empty ways
                osmWays = osmWays.filter(w => w.nodeRefs.length >= 2);
                activeSelectedNode = null;
                selectWay(null);
                redrawOSM2D();
                rebuildOsmOverlays3D();
            }
        }
    });

    window.addEventListener('keyup', function(e) {
        keysPressed[e.key.toLowerCase()] = false;
    });

    window.addEventListener('blur', function() {
        // Reset all keys when focus is lost
        for (const k in keysPressed) {
            keysPressed[k] = false;
        }
    });
}

function drawBrushCursor2D(cx, cy) {
    if (!ctxVector) return;
    
    // Scale brush radius to canvas pixels
    const canvasRect = elVectorCanvas.getBoundingClientRect();
    const rPixels = (brushRadiusMeters / MAP_SIZE) * canvasRect.width;
    
    if (activeTool === 'raise' || activeTool === 'lower' || activeTool === 'flatten' || activeTool === 'smooth') {
        ctxVector.strokeStyle = 'rgba(167, 139, 250, 0.8)';
        ctxVector.lineWidth = 1.5;
        ctxVector.beginPath();
        ctxVector.arc(cx, cy, rPixels, 0, Math.PI * 2);
        ctxVector.stroke();
        
        ctxVector.fillStyle = 'rgba(167, 139, 250, 0.15)';
        ctxVector.beginPath();
        ctxVector.arc(cx, cy, rPixels, 0, Math.PI * 2);
        ctxVector.fill();
    }
}
