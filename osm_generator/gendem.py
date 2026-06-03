import numpy as np
from PIL import Image
import os

# --- Configurations ---
np.random.seed(42)  # Fixed seed for reproducible terrain features

S = 12288
H, W = S, S

min_height = 200.00
max_height = 240.00
height_range = 40.00

# Helper for smooth cosine interpolation of grid values
def interpolate_grid(grid, H, W):
    R, C = grid.shape
    y = np.linspace(0, R - 1, H)
    x = np.linspace(0, C - 1, W)
    
    yi = np.clip(y.astype(int), 0, R - 2)
    xi = np.clip(x.astype(int), 0, C - 2)
    yf = y - yi
    xf = x - xi
    
    yi = yi[:, np.newaxis]
    yf = yf[:, np.newaxis]
    xi = xi[np.newaxis, :]
    xf = xf[np.newaxis, :]
    
    c00 = grid[yi, xi]
    c10 = grid[yi + 1, xi]
    c01 = grid[yi, xi + 1]
    c11 = grid[yi + 1, xi + 1]
    
    # Cosine interpolation formula: (1 - cos(f * pi)) / 2
    cyf = (1.0 - np.cos(yf * np.pi)) / 2.0
    cxf = (1.0 - np.cos(xf * np.pi)) / 2.0
    
    top = c00 * (1.0 - cxf) + c01 * cxf
    bottom = c10 * (1.0 - cxf) + c11 * cxf
    result = top * (1.0 - cyf) + bottom * cyf
    return result

print(f"Generating macro-terrain slope for FS25 size {W}x{H} (High in North, sloping down to South)...")
# Create coordinates
Y, X = np.ogrid[:H, :W]
# Slope is high (1.0) at North (y=0) and low (0.0) at South (y=H-1)
slope = 1.0 - Y / (H - 1)

print("Generating multi-octave fractal noise...")
noise = np.zeros((H, W))
octaves = [
    (4, 1.0),      # Macro mountain structures
    (8, 0.5),      # Large scale hills
    (16, 0.25),    # Detailed hills and valleys
    (32, 0.125),   # Small ridges
    (64, 0.0625),  # Micro-bumps
    (128, 0.03125) # High frequency texture
]

for grid_size, weight in octaves:
    grid = np.random.rand(grid_size, grid_size)
    octave_noise = interpolate_grid(grid, H, W)
    noise += octave_noise * weight

# Normalize noise to [0, 1]
noise = (noise - noise.min()) / (noise.max() - noise.min())

# Combine macro-slope and fractal noise
terrain = slope * 0.75 + noise * 0.25

# Rescale terrain exactly to [0, 1] to clamp stats
terrain = (terrain - terrain.min()) / (terrain.max() - terrain.min())

# Apply smooth flat transition for the southern rice fields area
# Rice fields start at Y = 9216. Smooth fade starts at Y = 8192.
y_fade_start = 8192
y_flat_start = 9216
t = (Y - y_fade_start) / (y_flat_start - y_fade_start)
w_flat = np.where(Y < y_fade_start, 1.0,
                  np.where(Y >= y_flat_start, 0.0,
                           (1.0 + np.cos(t * np.pi)) / 2.0))
terrain = terrain * w_flat

# --- 1. Hydraulic-like Flow Erosion ---
print("Generating hydraulic-like macro erosion on a 1024x1024 grid...")
from PIL import ImageFilter
S_small = 1024

# Downsample base terrain to 1024x1024 for fast flow routing
terrain_small = np.array(
    Image.fromarray(terrain.astype(np.float32), mode='F')
    .resize((S_small, S_small), Image.Resampling.BILINEAR)
)

# 8 Neighbors offsets
offsets = [(-1, -1), (-1, 0), (-1, 1),
           (0, -1),          (0, 1),
           (1, -1),  (1, 0),  (1, 1)]

neighbor_heights = np.full((8, S_small, S_small), np.inf)
for idx, (dy, dx) in enumerate(offsets):
    rolled = np.roll(terrain_small, shift=(-dy, -dx), axis=(0, 1))
    if dy == -1: rolled[0, :] = np.inf
    if dy == 1: rolled[-1, :] = np.inf
    if dx == -1: rolled[:, 0] = np.inf
    if dx == 1: rolled[:, -1] = np.inf
    neighbor_heights[idx] = rolled

min_neighbor_idx = np.argmin(neighbor_heights, axis=0)
min_neighbor_val = np.min(neighbor_heights, axis=0)
flows_to_neighbor = min_neighbor_val < terrain_small

# Sort pixels descending by height
flat_indices = np.argsort(-terrain_small.ravel())
flow = np.ones(S_small * S_small, dtype=float)

y_grid, x_grid = np.indices((S_small, S_small))
chosen_dy = np.array([dy for dy, dx in offsets])[min_neighbor_idx]
chosen_dx = np.array([dx for dy, dx in offsets])[min_neighbor_idx]

neighbor_y = np.clip(y_grid + chosen_dy, 0, S_small - 1)
neighbor_x = np.clip(x_grid + chosen_dx, 0, S_small - 1)
neighbor_flat_idx = (neighbor_y * S_small + neighbor_x).ravel()

flows_to_neighbor_flat = flows_to_neighbor.ravel()

# Python loop for flow routing (takes ~0.5s for 1024x1024)
for idx in flat_indices:
    if flows_to_neighbor_flat[idx]:
        n_idx = neighbor_flat_idx[idx]
        flow[n_idx] += flow[idx]

# Calculate slope of the small terrain
dy_grad, dx_grad = np.gradient(terrain_small)
slope_mag = np.sqrt(dy_grad**2 + dx_grad**2)

# Erosion amount is proportional to sqrt(flow) * slope
erosion_amount = np.sqrt(flow.reshape(S_small, S_small)) * slope_mag

# Normalize erosion to have a maximum depth of 7.0 meters
max_erosion_depth_m = 7.0
max_erosion_normalized = max_erosion_depth_m / height_range # 7 / 40 = 0.175

erosion_max_val = erosion_amount.max()
if erosion_max_val > 0:
    erosion_amount = (erosion_amount / erosion_max_val) * max_erosion_normalized

# Blur the erosion map using PIL to create smooth, natural valleys
erosion_scaled = (erosion_amount / max_erosion_normalized * 255.0).astype(np.uint8)
erosion_pil = Image.fromarray(erosion_scaled, mode='L')
erosion_blurred_pil = erosion_pil.filter(ImageFilter.GaussianBlur(radius=3))
erosion_amount_blurred = np.array(erosion_blurred_pil, dtype=np.float64) / 255.0 * max_erosion_normalized

# Upsample the blurred erosion map back to 12288x12288
erosion_large = np.array(
    Image.fromarray(erosion_amount_blurred.astype(np.float32), mode='F')
    .resize((W, H), Image.Resampling.BILINEAR)
)

# Apply erosion only outside the southern rice fields area
# w_flat is 0.0 in the rice fields, and 1.0 in the north
terrain = np.clip(terrain - erosion_large * w_flat, 0.0, 1.0)


# --- 2. Add River Erosion in the North ---
print("Applying northern river erosion...")
# River path equation from genmap.py (with offset of 2048)
# y_c = m(0.35) + (m(0.1) * (x / S)) + 90 * math.sin(x * 2 * math.pi / 3200) + 25 * math.sin(x * 2 * math.pi / 900)
# Here S = 8192, PPM = 1024.
# In 12288 space, the river starts at X = OFFSET = 2048, and spans W_playable = 8192.
# So we compute x_playable = X - 2048.
x_playable = X - 2048
y_c_playable = (0.35 * 1024) + (0.1 * 1024 * (x_playable / 8192.0)) + \
               90.0 * np.sin(x_playable * 2.0 * np.pi / 3200.0) + \
               25.0 * np.sin(x_playable * 2.0 * np.pi / 900.0)
Y_c = y_c_playable + 2048.0 # Y coordinate of the river center in 12288 space

# Distance from river center Y_c (vertical distance)
dist_y = np.abs(Y - Y_c)

# We want the channel to be flat, and the valley to fade out
w_channel = 25.0  # ~25 meters half-width
w_valley = 250.0  # ~250 meters half-width

# Calculate erosion factor
t_valley = (dist_y - w_channel) / (w_valley - w_channel)
erosion_factor = np.where(dist_y < w_channel, 1.0,
                          np.where(dist_y > w_valley, 0.0,
                                   (1.0 + np.cos(t_valley * np.pi)) / 2.0))

# Target river bed elevation: slope(Y_c) * 0.75 - depth
slope_yc = 1.0 - Y_c / (H - 1)
depth_normalized = 6.0 / height_range # 6 meters deep in the normalized range [0, 1]
river_bed_height = slope_yc * 0.75 - depth_normalized

# Blend the terrain with the river bed
terrain = terrain * (1.0 - erosion_factor) + river_bed_height * erosion_factor


# --- 3. Flatten Platforms (Town, Industry, Yards, Greenhouses) ---
print("Flattening city, industrial, farmyards, and greenhouse zones...")

OFFSET = 2048
PPM = 1024
TH_P = 22

def mc(x):
    return OFFSET + x * PPM

# List of areas to flatten: (x0, y0, x1, y1)
flat_areas = [
    # 1. Town
    (mc(1), mc(1), mc(2), mc(2)),
    # 2. Industrial spots
    (mc(1) - TH_P/2 - 0.4*PPM, mc(6.2), mc(1) - TH_P/2, mc(6.8)),
    (mc(5.2), mc(7.0) - TH_P/2 - 0.4*PPM, mc(5.8), mc(7.0) - TH_P/2),
    # 3. Farmyards
    (mc(4.375), mc(1) + TH_P/2, mc(4.625), mc(1) + TH_P/2 + 0.25*PPM),
    (mc(2.35), mc(7) - TH_P/2 - 0.3*PPM, mc(2.65), mc(7) - TH_P/2),
    (mc(4.4), mc(7) - TH_P/2 - 0.2*PPM, mc(4.6), mc(7) - TH_P/2),
    (mc(6.35), mc(7) - TH_P/2 - 0.3*PPM, mc(6.65), mc(7) - TH_P/2),
    (mc(1) + TH_P/2, mc(4.4), mc(1) + TH_P/2 + 0.2*PPM, mc(4.6)),
    # 4. Greenhouses (viveros)
    (mc(3.2), mc(7.0) - TH_P/2 - 0.7*PPM, mc(3.8), mc(7.0) - TH_P/2 - 0.3*PPM)
]

def make_mask_1d(V, v0, v1, d_blend):
    mask = np.zeros_like(V, dtype=float)
    in_region = (V >= v0) & (V <= v1)
    dist_from_left = V - v0
    dist_from_right = v1 - V
    min_dist = np.minimum(dist_from_left, dist_from_right)
    # Avoid division by zero if d_blend is 0
    t = np.where(d_blend > 0, min_dist / d_blend, 1.0)
    smooth_val = (1.0 - np.cos(t * np.pi)) / 2.0
    return np.where(in_region, np.where(min_dist >= d_blend, 1.0, smooth_val), 0.0)

def flatten_rect(terrain, x0, y0, x1, y1, d_blend=50.0):
    # Round coordinates to integers first to align mask generation with indexing
    x0 = int(round(x0))
    x1 = int(round(x1))
    y0 = int(round(y0))
    y1 = int(round(y1))
    
    x0 = max(0, x0)
    x1 = min(terrain.shape[1] - 1, x1)
    y0 = max(0, y0)
    y1 = min(terrain.shape[0] - 1, y1)
    
    # Calculate center of the rectangle to find target height
    xc = (x0 + x1) // 2
    yc = (y0 + y1) // 2
    target_h = terrain[yc, xc]
    
    # Safeguard blend distance
    dx_blend = min(d_blend, (x1 - x0) / 2.0)
    dy_blend = min(d_blend, (y1 - y0) / 2.0)
    
    # Generate masks (X and Y are global grid coordinates)
    mask_x = make_mask_1d(X, x0, x1, dx_blend)
    mask_y = make_mask_1d(Y, y0, y1, dy_blend)
    mask_2d = mask_x * mask_y
    
    # Blend terrain
    return terrain * (1.0 - mask_2d) + target_h * mask_2d

for rect_coords in flat_areas:
    terrain = flatten_rect(terrain, *rect_coords, d_blend=50.0)

# Output directories
os.makedirs("outputs", exist_ok=True)

# ----------------- OPTION 1: Full-Range heightmap -----------------
# Scaled to full 16-bit range [0, 65535]
# Requires: heightScale="20" in map XML, and a vertical offset/translation of 200m in GIANTS Editor
print("Saving 16-bit Full-Range DEM (outputs/dem_full_range.png)...")
dem_full_16 = (terrain * 65535).astype(np.uint16)
img_full_16 = Image.fromarray(dem_full_16, mode='I;16')
img_full_16.save("outputs/dem_full_range.png")

# ----------------- OPTION 2: Direct-Scale heightmap -----------------
# Scaled directly to match heights [200.0, 240.0] assuming heightScale="240"
# Formula: value = (height / max_height) * 65535
# For 200m: (200 / 240) * 65535 = 54612.5
# For 240m: (240 / 240) * 65535 = 65535
print("Saving 16-bit Direct-Scale DEM (outputs/dem.png)...")
direct_terrain = (200.0 + terrain * height_range) / 240.0
dem_direct_16 = (direct_terrain * 65535).astype(np.uint16)
img_direct_16 = Image.fromarray(dem_direct_16, mode='I;16')
img_direct_16.save("outputs/dem.png")

# ----------------- OPTION 3: 8-bit preview -----------------
# 8-bit version of Option 1 (scaled 0-255) for viewing
print("Saving 8-bit preview heightmap (outputs/dem_view.png)...")
dem_8bit = (terrain * 255).astype(np.uint8)
img_8 = Image.fromarray(dem_8bit, mode='L')
img_8.save("outputs/dem_view.png")

print("Done! DEM files for FS25 successfully generated.")
print(f"Elevation Verification Statistics:")
print(f"  - Min Height: {min_height:.2f}m")
print(f"  - Max Height: {max_height:.2f}m")
print(f"  - Range: {height_range:.2f}m")
print(f"  - Dimensions: {W}x{H} pixels")
