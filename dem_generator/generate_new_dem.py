import os
import sys
import time
import math
import numpy as np
from PIL import Image, ImageDraw
from scipy.ndimage import gaussian_filter

# Import irregular forest coordinates from common.py
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../osm_generator_4096")))
from common import IRREGULAR_FOREST_PTS

# For generating visual maps
import matplotlib
matplotlib.use('Agg') # Non-interactive backend
import matplotlib.pyplot as plt
from matplotlib.colors import LightSource

def val_noise(shape, grid_size, weight, seed=20260608):
    """Generates smooth value noise by upscaling a small random grid using bicubic interpolation."""
    np.random.seed(seed)
    small = np.random.uniform(-1.0, 1.0, size=(grid_size, grid_size)).astype(np.float32)
    temp_img = Image.fromarray(small)
    temp_img = temp_img.resize((shape[1], shape[0]), Image.Resampling.BICUBIC)
    return np.array(temp_img) * weight

def main():
    t_start = time.time()
    print("=== FS25 8K New DEM Generator (Exactly 8192x8192) ===")
    
    # Configuration
    S = 8192  # Exactly 8192x8192 pixels
    seed = 20260608
    np.random.seed(seed)
    
    output_dem_path = "dem_new.png"
    output_vis_path = "dem_new_visual.png"
    output_detail_vis_path = "dem_new_visual_detail.png"
    
    print(f"1. Generating coordinate grids for size {S}x{S}...")
    y_indices, x_indices = np.indices((S, S), dtype=np.float32)
    
    print("2. Generating geographic features (slope + rolling hills)...")
    # Global geographic slope: NW to SE
    slope = (x_indices / (S - 1)) * 8000 + (y_indices / (S - 1)) * 26000 + 12000
    
    # Playable terrain noise (mostly flat rolling hills)
    noise_playable = (
        val_noise((S, S), 8, 3500, seed=seed) +
        val_noise((S, S), 16, 1200, seed=seed+1) +
        val_noise((S, S), 32, 400, seed=seed+2) +
        val_noise((S, S), 64, 100, seed=seed+3)
    )
    
    # Background mountain noise (high amplitude, surrounding the map)
    noise_mountains = (
        val_noise((S, S), 12, 22000, seed=seed+4) +
        val_noise((S, S), 24, 8000, seed=seed+5) +
        val_noise((S, S), 48, 2000, seed=seed+6)
    )
    
    # Compute background mountain weight (0 inside playable area x,y in [2048, 6144], rises to 1.0 at 1024m away)
    dx_bg = np.maximum(0.0, np.maximum(2048.0 - x_indices, x_indices - 6144.0))
    dy_bg = np.maximum(0.0, np.maximum(2048.0 - y_indices, y_indices - 6144.0))
    dist_border_bg = np.sqrt(dx_bg*dx_bg + dy_bg*dy_bg)
    w_bg = np.minimum(1.0, dist_border_bg / 1024.0)
    
    # Natural base terrain (slope + hills + background mountains)
    natural_terrain = slope + noise_playable + w_bg * noise_mountains
    
    print("3. Implementing flat valley floor in the northern playable area...")
    # Flat zone boundary inside the playable area:
    # x in [2048, 6144] and y in [2048, 3072]
    rx0, rx1 = 2048, 6144
    ry0, ry1 = 2048, 3072
    W_TRANSITION = 500.0  # 500-meter transition ramp in all directions
    
    # Compute flat elevation height H_north dynamically as the median of the natural terrain
    # along the southern boundary of the flat zone inside the playable area
    H_north = np.median(natural_terrain[ry1, rx0:rx1+1])
    print(f"   Flat North Height (H_north): {H_north:.1f}")
    
    # Compute Euclidean distance from every pixel to the flat rectangle
    dx_flat = np.maximum(0.0, np.maximum(rx0 - x_indices, x_indices - rx1))
    dy_flat = np.maximum(0.0, np.maximum(ry0 - y_indices, y_indices - ry1))
    dist_flat = np.sqrt(dx_flat*dx_flat + dy_flat*dy_flat)
    
    # Define flat weight: 1.0 inside the flat zone, transitions to 0.0 outside over 500m
    w_flat = np.zeros_like(dist_flat)
    w_flat[dist_flat == 0] = 1.0
    
    trans_mask = (dist_flat > 0) & (dist_flat <= W_TRANSITION)
    t = dist_flat[trans_mask] / W_TRANSITION
    w_flat[trans_mask] = 0.5 * (1.0 + np.cos(np.pi * t))
    
    # Blend flat height with natural terrain
    terrain = w_flat * H_north + (1.0 - w_flat) * natural_terrain
    
    print("   Smoothing entire terrain (macro-smoothing)...")
    terrain = gaussian_filter(terrain, sigma=6)
    
    # Add the irregular hill corresponding to the forest in Column 1 Row 3
    print("4. Adding the irregular hill for the western forest (Colina)...")
    # Scale coordinates from 4096px zoning map to 8192px DEM (x_dem = x_zoning + 2048)
    offset = 2048
    forest_pts_dem = [(x + offset, y + offset) for (x, y) in IRREGULAR_FOREST_PTS]
    
    # Create mask of the irregular forest
    hill_mask_img = Image.new("L", (S, S), 0)
    draw_hill = ImageDraw.Draw(hill_mask_img)
    draw_hill.polygon(forest_pts_dem, fill=255)
    
    # Convert mask to float numpy array
    hill_mask = np.array(hill_mask_img, dtype=np.float32) / 255.0
    
    # Smooth the mask to get an organic hill shape (sigma=150.0 = ~150 meters transition)
    smooth_hill = gaussian_filter(hill_mask, sigma=150.0)
    
    # Normalize so peak is exactly 1.0
    if smooth_hill.max() > 0:
        smooth_hill = smooth_hill / smooth_hill.max()
        
    # Scale to 300 meters height (300m * 100 units/m = 30000 units)
    hill_elevation = smooth_hill * 30000.0
    
    # Add to the terrain
    terrain = terrain + hill_elevation
    
    # High-frequency micro-detail noise is omitted to ensure the DEM is completely smooth
    # and suitable for farming vehicle physics without roughness or jitter.
    
    print("5. Flattening southern farmyards with extra-gentle transitions...")
    offset = 2048
    southern_yards = [
        (3088 + offset, 3607 + offset, 3316 + offset, 4076 + offset, "Yard 0 (SE)"),
        (268 + offset, 3607 + offset, 500 + offset, 3828 + offset, "Yard 5 (S1)"),
        (1292 + offset, 3607 + offset, 1524 + offset, 3828 + offset, "Yard 6 (S2)"),
        (2316 + offset, 3607 + offset, 2548 + offset, 3828 + offset, "Yard 7 (S3)")
    ]
    
    margin = 120.0  # 120m transition margin for southern yards
    
    for x0, y0, x1, y1, name in southern_yards:
        x0_c = max(0, min(S-1, x0))
        x1_c = max(0, min(S-1, x1))
        y0_c = max(0, min(S-1, y0))
        y1_c = max(0, min(S-1, y1))
        
        # Calculate target height
        sub = terrain[y0_c:y1_c+1, x0_c:x1_c+1]
        H_target = np.median(sub)
        print(f"   Flattening {name} to target height = {H_target:.1f} (margin={margin}m)")
        
        bx0 = max(0, int(x0_c - margin - 5))
        bx1 = min(S-1, int(x1_c + margin + 5))
        by0 = max(0, int(y0_c - margin - 5))
        by1 = min(S-1, int(y1_c + margin + 5))
        
        terrain_ref = terrain.copy()
        
        ny = by1 - by0 + 1
        nx = bx1 - bx0 + 1
        local_ramp = np.zeros((ny, nx), dtype=bool)
        
        for y_offset, y in enumerate(range(by0, by1 + 1)):
            for x_offset, x in enumerate(range(bx0, bx1 + 1)):
                dx_pt = max(0.0, x0_c - x, x - x1_c)
                dy_pt = max(0.0, y0_c - y, y - y1_c)
                d = math.sqrt(dx_pt*dx_pt + dy_pt*dy_pt)
                
                if d == 0:
                    terrain[y, x] = H_target
                elif d <= margin:
                    w = 0.5 * (1.0 + math.cos(math.pi * d / margin))
                    terrain[y, x] = w * H_target + (1.0 - w) * terrain_ref[y, x]
                    local_ramp[y_offset, x_offset] = True
                    
        # Local Gaussian smoothing specifically to the transition ramp (sigma=10)
        local_terrain = terrain[by0:by1+1, bx0:bx1+1].copy()
        local_smoothed = gaussian_filter(local_terrain, sigma=10)
        
        for y_offset, y in enumerate(range(by0, by1 + 1)):
            for x_offset, x in enumerate(range(bx0, bx1 + 1)):
                if local_ramp[y_offset, x_offset]:
                    terrain[y, x] = local_smoothed[y_offset, x_offset]
                    
    # Clamp terrain to valid 16-bit range
    terrain = np.clip(terrain, 2000.0, 62000.0)
    
    print(f"6. Saving final DEM heightmap to '{output_dem_path}'...")
    img_out = Image.fromarray(terrain.astype(np.int32), mode="I")
    img_out.save(output_dem_path)
    print(f"   Saved heightmap successfully (Min={terrain.min():.1f}, Max={terrain.max():.1f}).")
    
    print("7. Generating visual maps...")
    vis_scale = 8
    terrain_vis = terrain[::vis_scale, ::vis_scale]
    
    ls = LightSource(azdeg=315, altdeg=45)
    hs = ls.shade(terrain_vis, cmap=plt.get_cmap('terrain'), vert_exag=0.12, blend_mode='overlay')
    
    # List of all areas (for highlighting)
    all_areas = [
        (3088 + offset, 3607 + offset, 3316 + offset, 4076 + offset, "Yard 0 (SE)"),
        (780 + offset, 24 + offset, 1008 + offset, 489 + offset, "Yard 1 (NW)"),
        (1292 + offset, 268 + offset, 1524 + offset, 489 + offset, "Yard 2 (N1)"),
        (2316 + offset, 268 + offset, 2548 + offset, 489 + offset, "Yard 3 (N2)"),
        (3340 + offset, 268 + offset, 3572 + offset, 489 + offset, "Yard 4 (N3)"),
        (268 + offset, 3607 + offset, 500 + offset, 3828 + offset, "Yard 5 (S1)"),
        (1292 + offset, 3607 + offset, 1524 + offset, 3828 + offset, "Yard 6 (S2)"),
        (2316 + offset, 3607 + offset, 2548 + offset, 3828 + offset, "Yard 7 (S3)"),
        (1024 + offset, 512 + offset, 1664 + offset, 1024 + offset, "Town")
    ]
    
    # --- Map 1: Full 8K Map View ---
    print("   Generating full map visualization...")
    fig, ax = plt.subplots(figsize=(12, 12), dpi=150)
    ax.imshow(hs)
    ax.axis('off')
    ax.set_title("Full 8K DEM Map (Exactly 8192x8192px - Valley Style)", fontsize=16, fontweight='bold', pad=15)
    
    rect_playable = plt.Rectangle((2048/vis_scale, 2048/vis_scale), 4096/vis_scale, 4096/vis_scale, 
                                  fill=False, edgecolor='white', linewidth=2, linestyle='--', label='Playable Border (4km)')
    ax.add_patch(rect_playable)
    
    for x0, y0, x1, y1, name in all_areas:
        rect = plt.Rectangle((x0/vis_scale, y0/vis_scale), (x1-x0)/vis_scale, (y1-y0)/vis_scale, 
                              fill=False, edgecolor='#00FF00', linewidth=1.5, linestyle='-')
        ax.add_patch(rect)
        
    rect_flat_north = plt.Rectangle((rx0/vis_scale, ry0/vis_scale), (rx1-rx0)/vis_scale, (ry1-ry0)/vis_scale,
                                     fill=False, edgecolor='yellow', linewidth=2, linestyle=':', label='Flat North Area')
    ax.add_patch(rect_flat_north)
    
    # Draw the irregular forest hill polygon
    vis_x = [(x + offset) / vis_scale for (x, y) in IRREGULAR_FOREST_PTS]
    vis_y = [(y + offset) / vis_scale for (x, y) in IRREGULAR_FOREST_PTS]
    vis_x.append(vis_x[0])
    vis_y.append(vis_y[0])
    line_hill, = ax.plot(vis_x, vis_y, color='cyan', linewidth=2, linestyle='-', label='Hill (Colina)')
    
    plt.legend(handles=[rect_playable, rect_flat_north, line_hill], loc='upper right', facecolor='black', labelcolor='white')
    plt.savefig(output_vis_path, bbox_inches='tight')
    plt.close()
    print(f"   Saved full visualization to '{output_vis_path}'.")
    
    # --- Map 2: Zoomed-in Playable Area View ---
    print("   Generating detailed playable area visualization...")
    p_start = 2048 // vis_scale
    p_end = 6144 // vis_scale
    hs_detail = hs[p_start:p_end, p_start:p_end]
    
    fig, ax = plt.subplots(figsize=(10, 10), dpi=150)
    ax.imshow(hs_detail)
    ax.axis('off')
    ax.set_title("Detailed Playable Area (Exact 8192x8192 canvas size)", fontsize=16, fontweight='bold', pad=15)
    
    for x0, y0, x1, y1, name in all_areas:
        x0_p = (x0 / vis_scale) - p_start
        y0_p = (y0 / vis_scale) - p_start
        w_p = (x1 - x0) / vis_scale
        h_p = (y1 - y0) / vis_scale
        
        rect = plt.Rectangle((x0_p, y0_p), w_p, h_p, fill=False, edgecolor='#00FF00', linewidth=2.5, linestyle='-')
        ax.add_patch(rect)
        ax.text(x0_p + 2, y0_p - 3, name, color='#00FF00', fontsize=8, fontweight='bold')
        
    ax.axhline(y=(ry1/vis_scale) - p_start, color='yellow', linestyle=':', linewidth=2.5)
    ax.text(10, (ry1/vis_scale) - p_start - 8, "FLAT VALLEY FLOOR (North)", color='yellow', fontsize=10, fontweight='bold')
    ax.text(10, (ry1/vis_scale) - p_start + 15, "TRANSITION RAMP (500m)", color='yellow', fontsize=10, fontweight='bold')
    
    # Draw detailed irregular hill polygon
    vis_detail_x = [((x + offset) / vis_scale) - p_start for (x, y) in IRREGULAR_FOREST_PTS]
    vis_detail_y = [((y + offset) / vis_scale) - p_start for (x, y) in IRREGULAR_FOREST_PTS]
    vis_detail_x.append(vis_detail_x[0])
    vis_detail_y.append(vis_detail_y[0])
    ax.plot(vis_detail_x, vis_detail_y, color='cyan', linewidth=2.5, linestyle='-')
    ax.text(vis_detail_x[0] + 5, vis_detail_y[0] + 15, "Hill (Colina)", color='cyan', fontsize=10, fontweight='bold')
    
    plt.savefig(output_detail_vis_path, bbox_inches='tight')
    plt.close()
    print(f"   Saved detailed visualization to '{output_detail_vis_path}'.")
    
    t_end = time.time()
    print(f"\n=== Script Completed Successfully in {t_end - t_start:.2f} seconds ===")
    print(f"Output files:")
    print(f" - New Heightmap: {output_dem_path}")
    print(f" - Full Map Visual: {output_vis_path}")
    print(f" - Detailed Visual: {output_detail_vis_path}")

if __name__ == "__main__":
    main()
