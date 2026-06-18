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

def hydraulic_erosion(heightmap, num_droplets=20000, inertia=0.15, sediment_capacity_factor=4.0, 
                      min_sediment_capacity=0.01, dissolve_rate=0.15, deposit_rate=0.15, 
                      evaporate_rate=0.02, gravity=9.81, max_droplet_lifetime=30):
    """
    Simulates basic particle-based hydraulic erosion on a heightmap.
    Spawns droplets only in sloped areas to maximize efficiency.
    """
    H, W = heightmap.shape
    map_data = heightmap.copy().astype(np.float32)
    
    # Calculate slopes to find active erosion zones (slopes and mountains)
    dy, dx = np.gradient(heightmap)
    slope_mag = np.sqrt(dx*dx + dy*dy)
    
    # We select pixels with a slope magnitude greater than a threshold (5.0 units)
    active_indices = np.argwhere(slope_mag > 5.0) 
    if len(active_indices) == 0:
        print("   No sloped areas found, skipping erosion.")
        return map_data
        
    print(f"   Spawning {num_droplets} droplets on {len(active_indices)} active slope pixels...")
    
    np.random.seed(42)
    selected = np.random.choice(len(active_indices), num_droplets, replace=True)
    py = active_indices[selected, 0].astype(np.float32)
    px = active_indices[selected, 1].astype(np.float32)
    
    # Add random subpixel offsets
    px += np.random.uniform(-0.5, 0.5, num_droplets).astype(np.float32)
    py += np.random.uniform(-0.5, 0.5, num_droplets).astype(np.float32)
    
    # Pre-fetch math functions for speed
    min_func = min
    max_func = max
    sqrt_func = math.sqrt
    
    for i in range(num_droplets):
        x = px[i]
        y = py[i]
        dir_x = 0.0
        dir_y = 0.0
        speed = 1.0
        water = 1.0
        sediment = 0.0
        
        for step in range(max_droplet_lifetime):
            x_int = int(x)
            y_int = int(y)
            tx = x - x_int
            ty = y - y_int
            
            x0 = x_int
            x1 = x_int + 1
            y0 = y_int
            y1 = y_int + 1
            
            if x1 >= W or y1 >= H or x0 < 0 or y0 < 0:
                break
                
            h00 = map_data[y0, x0]
            h10 = map_data[y0, x1]
            h01 = map_data[y1, x0]
            h11 = map_data[y1, x1]
            
            # Gradient
            grad_x = (h10 - h00) * (1.0 - ty) + (h11 - h01) * ty
            grad_y = (h01 - h00) * (1.0 - tx) + (h11 - h10) * tx
            
            # Height at current pos
            current_height = (h00 * (1.0 - tx) + h10 * tx) * (1.0 - ty) + (h01 * (1.0 - tx) + h11 * tx) * ty
            
            dir_x = dir_x * inertia - grad_x * (1.0 - inertia)
            dir_y = dir_y * inertia - grad_y * (1.0 - inertia)
            
            len_dir = sqrt_func(dir_x * dir_x + dir_y * dir_y)
            if len_dir > 0:
                dir_x /= len_dir
                dir_y /= len_dir
                
            new_x = x + dir_x
            new_y = y + dir_y
            
            if new_x < 2 or new_x >= W - 2 or new_y < 2 or new_y >= H - 2:
                break
                
            new_x_int = int(new_x)
            new_y_int = int(new_y)
            ntx = new_x - new_x_int
            nty = new_y - new_y_int
            
            nh00 = map_data[new_y_int, new_x_int]
            nh10 = map_data[new_y_int, new_x_int + 1]
            nh01 = map_data[new_y_int + 1, new_x_int]
            nh11 = map_data[new_y_int + 1, new_x_int + 1]
            
            new_height = (nh00 * (1.0 - ntx) + nh10 * ntx) * (1.0 - nty) + (nh01 * (1.0 - ntx) + nh11 * ntx) * nty
            
            delta_h = new_height - current_height
            
            # Sediment capacity
            capacity = max_func(min_sediment_capacity, -delta_h * speed * water * sediment_capacity_factor)
            
            if sediment > capacity or delta_h > 0:
                deposit = (sediment - capacity) * deposit_rate if delta_h < 0 else min_func(delta_h, sediment)
                sediment -= deposit
                
                map_data[y0, x0] += deposit * (1.0 - tx) * (1.0 - ty)
                map_data[y0, x1] += deposit * tx * (1.0 - ty)
                map_data[y1, x0] += deposit * (1.0 - tx) * ty
                map_data[y1, x1] += deposit * tx * ty
            else:
                erode = min_func((capacity - sediment) * dissolve_rate, -delta_h)
                sediment += erode
                
                map_data[y0, x0] -= erode * (1.0 - tx) * (1.0 - ty)
                map_data[y0, x1] -= erode * tx * (1.0 - ty)
                map_data[y1, x0] -= erode * (1.0 - tx) * ty
                map_data[y1, x1] -= erode * tx * ty
                
            speed = sqrt_func(speed * speed + max_func(0.0, -delta_h * gravity))
            water *= (1.0 - evaporate_rate)
            
            x = new_x
            y = new_y
            
    return map_data

def main():
    t_start = time.time()
    print("=== FS25 8K New DEM Generator (Exactly 8192x8192) ===")
    
    # Configuration
    S = 8192  # Exactly 8192x8192 pixels
    seed = 20260608
    np.random.seed(seed)
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_dem_path = os.path.join(script_dir, "dem_new.png")
    output_vis_path = os.path.join(script_dir, "dem_new_visual.png")
    output_detail_vis_path = os.path.join(script_dir, "dem_new_visual_detail.png")
    
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
    
    print("3. Implementing winding plateau in the southern playable area and flat northern valley floor...")
    # Flat zone boundary inside the playable area:
    # x in [2048, 6144] and y in [2048, 3072]
    rx0, rx1 = 2048, 6144
    ry0, ry1 = 2048, 3072
    
    print("3. Implementing winding plateau in the southern playable area and flat northern valley floor...")
    # Flat zone boundary inside the playable area:
    # x in [2048, 6144] and y in [2048, 3072]
    rx0, rx1 = 2048, 6144
    ry0, ry1 = 2048, 3072
    
    # Compute flat elevation height H_north dynamically as the median of the natural terrain
    # along the southern boundary of the flat zone inside the playable area
    H_north = np.median(natural_terrain[ry1, rx0:rx1+1])
    # The height difference between north and south is exactly 300 meters (30000 units)
    H_south = H_north + 30000.0
    print(f"   Flat North Height (H_north): {H_north:.1f}")
    print(f"   Flat South Height (H_south): {H_south:.1f}")
    
    # Define winding boundary separating north and south playable sectors (centered around y = 4096)
    # Using a combination of sine and cosine waves to create a serpentine shape
    y_boundary = 4096.0 + 400.0 * np.sin(2.0 * np.pi * x_indices / 8192.0) + 100.0 * np.cos(2.0 * np.pi * x_indices / 4096.0)
    
    # Create plateau mask
    # Start with a mask where the southern sector (y > y_boundary) is 1.0
    plateau_mask = np.zeros((S, S), dtype=np.float32)
    plateau_mask[y_indices > y_boundary] = 1.0
    
    # Smooth the plateau mask to create a natural, organic transition slope.
    # sigma=150.0 corresponds to a very smooth transition slope (~300-400 meters wide)
    print("   Smoothing the plateau mask to create natural transition slopes...")
    w_plateau = gaussian_filter(plateau_mask, sigma=150.0, mode='nearest')
    
    # Blend the flat north height (valley) and the flat south height (plateau) using the smoothed mask
    terrain_base = (1.0 - w_plateau) * H_north + w_plateau * H_south
    
    # Add background mountain noise surrounding the playable area (so they rise from the valley / plateau base)
    terrain = terrain_base + w_bg * noise_mountains
    
    print("   Smoothing entire terrain (macro-smoothing)...")
    # Apply macro-smoothing
    terrain = gaussian_filter(terrain, sigma=6)
    
    # --- Hydraulic Erosion ---
    print("   Simulating hydraulic erosion to carve natural water gullies on slopes and mountains...")
    # Downsample to 1024x1024 for fast particle simulation
    vis_scale_down = 8
    terrain_1024 = terrain[::vis_scale_down, ::vis_scale_down]
    
    # Run erosion simulation (20,000 droplets)
    eroded_1024 = hydraulic_erosion(terrain_1024, num_droplets=20000, sediment_capacity_factor=4.0, dissolve_rate=0.15, deposit_rate=0.15)
    
    # Compute the height difference
    erosion_detail = eroded_1024 - terrain_1024
    
    # Smooth the detail slightly to prevent pixelation artifacts
    erosion_detail = gaussian_filter(erosion_detail, sigma=1.0)
    
    # Upscale back to 8192x8192 using PIL bicubic interpolation
    detail_img = Image.fromarray(erosion_detail)
    detail_img = detail_img.resize((S, S), Image.Resampling.BICUBIC)
    erosion_detail_8K = np.array(detail_img)
    
    # Add erosion detail back to the 8K terrain
    terrain = terrain + erosion_detail_8K
    
    print("4. Creating winding mountain road hugging the slope (concentrated hairpin curves, under 8% slope)...")
    from scipy.interpolate import CubicSpline
    from scipy.spatial import cKDTree
    
    # Define control points for the winding road path (only for y in [3200, 4800])
    # Confined horizontally between x=3500 and x=4600 to preserve cultivable fields
    y_control = np.array([
        3200, 
        3320, 3350, 3380, 
        3570, 3600, 3630, 
        3820, 3850, 3880, 
        4070, 4100, 4130, 
        4320, 4350, 4380, 
        4570, 4600, 4630, 
        4800
    ], dtype=np.float32)
    x_control = np.array([
        3500,
        3750, 3600, 3750, 
        4450, 4600, 4450, 
        3750, 3600, 3750, 
        4450, 4600, 4450, 
        3750, 3600, 3750, 
        4450, 4600, 4450, 
        5800
    ], dtype=np.float32)
    
    # Fit clamped cubic spline (1D, since y is strictly increasing)
    cs = CubicSpline(y_control, x_control, bc_type='clamped')
    
    # 1. North connection (straight vertical from y=2560 to y=3200 at x=3500)
    Y_north = np.linspace(2560, 3200, 1000, dtype=np.float32)
    X_north = np.full_like(Y_north, 3500.0)
    H_north_seg = np.full_like(Y_north, H_north)
    
    # 2. Middle winding road (spline from y=3200 to y=4800)
    Y_mid = np.linspace(3200, 4800, 2000, dtype=np.float32)
    X_mid = cs(Y_mid).astype(np.float32)
    
    # Calculate cumulative distance along the middle section to interpolate heights
    mid_pts = np.column_stack((X_mid, Y_mid))
    mid_diffs = np.diff(mid_pts, axis=0)
    mid_dists = np.sqrt(np.sum(mid_diffs**2, axis=1))
    mid_cum_dists = np.zeros(len(Y_mid), dtype=np.float32)
    mid_cum_dists[1:] = np.cumsum(mid_dists)
    mid_total_len = mid_cum_dists[-1]
    
    # Distance-based parameter (u in [0, 1])
    u = mid_cum_dists / mid_total_len
    # Quintic smoothstep for smooth slope transition (C2 continuity)
    w = 6.0 * u**5 - 15.0 * u**4 + 10.0 * u**3
    H_mid_seg = H_north + (H_south - H_north) * w
    
    # 3. South connection (straight vertical from y=4800 to y=5632 at x=5800)
    Y_south = np.linspace(4800, 5632, 1000, dtype=np.float32)
    X_south = np.full_like(Y_south, 5800.0)
    H_south_seg = np.full_like(Y_south, H_south)
    
    # Concatenate all segments
    X_road = np.concatenate([X_north, X_mid, X_south])
    Y_road = np.concatenate([Y_north, Y_mid, Y_south])
    H_road = np.concatenate([H_north_seg, H_mid_seg, H_south_seg])
    
    # Combined road points
    road_pts = np.column_stack((X_road, Y_road))
    
    # Define road parameters
    road_width = 16.0    # 16 pixels/meters wide flat surface
    margin_width = 60.0  # Reduced margin to 60m for a narrower slope transition
    half_road = road_width / 2.0
    
    # Bounding box coordinates with margin for efficiency
    bbox_margin = margin_width + 70.0
    x_min = int(np.min(X_road) - bbox_margin)
    x_max = int(np.max(X_road) + bbox_margin)
    y_min = int(np.min(Y_road) - bbox_margin)
    y_max = int(np.max(Y_road) + bbox_margin)
    
    # Ensure indices are within bounds
    x_min = max(0, x_min)
    x_max = min(S - 1, x_max)
    y_min = max(0, y_min)
    y_max = min(S - 1, y_max)
    
    # Generate meshgrid for the bounding box
    bx = np.arange(x_min, x_max + 1, dtype=np.int32)
    by = np.arange(y_min, y_max + 1, dtype=np.int32)
    grid_x, grid_y = np.meshgrid(bx, by)
    grid_coords = np.column_stack((grid_x.ravel(), grid_y.ravel()))
    
    # Query KDTree to find closest road points
    tree = cKDTree(road_pts)
    pixel_dists, pixel_indices = tree.query(grid_coords)
    
    # Reshape results to match bounding box shape
    ny_b, nx_b = len(by), len(bx)
    dist_grid = pixel_dists.reshape((ny_b, nx_b))
    idx_grid = pixel_indices.reshape((ny_b, nx_b))
    
    # Get target heights for the bounding box
    target_heights = H_road[idx_grid]
    
    # Extract local terrain slice
    local_terrain = terrain[y_min:y_max+1, x_min:x_max+1].copy()
    
    # Masks
    road_mask = dist_grid <= half_road
    blend_mask = (dist_grid > half_road) & (dist_grid <= half_road + margin_width)
    
    # Apply flat road heights
    local_terrain[road_mask] = target_heights[road_mask]
    
    # Apply cosine blend for transition
    d_blend = dist_grid[blend_mask] - half_road
    w = 0.5 * (1.0 + np.cos(np.pi * d_blend / margin_width))
    local_terrain[blend_mask] = w * target_heights[blend_mask] + (1.0 - w) * local_terrain[blend_mask]
    
    # Apply smooth blending transition to eliminate abrupt cuts
    w_smooth = np.zeros_like(dist_grid, dtype=np.float32)
    
    # Rise from road center to road edge (so road center is completely untouched and flat)
    mask_rise = (dist_grid > half_road - 6.0) & (dist_grid <= half_road)
    w_smooth[mask_rise] = (dist_grid[mask_rise] - (half_road - 6.0)) / 6.0
    
    # Full smoothing in the transition zone
    mask_full = (dist_grid > half_road) & (dist_grid <= half_road + margin_width)
    w_smooth[mask_full] = 1.0
    
    # Fall from transition zone to natural terrain
    falloff_width = 40.0  # Reduced falloff to 40m
    mask_fall = (dist_grid > half_road + margin_width) & (dist_grid <= half_road + margin_width + falloff_width)
    w_smooth[mask_fall] = 1.0 - (dist_grid[mask_fall] - (half_road + margin_width)) / falloff_width
    
    # Apply Gaussian filter to the blended local terrain slice (with sigma=15.0 for extra smoothness without bleeding)
    local_smoothed = gaussian_filter(local_terrain, sigma=15.0)
    local_terrain = (1.0 - w_smooth) * local_terrain + w_smooth * local_smoothed
    
    # Write back to terrain
    terrain[y_min:y_max+1, x_min:x_max+1] = local_terrain
    
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
    
    # Draw winding boundary line
    vis_winding_x = np.arange(0, S, 64)
    vis_winding_y = (4096.0 + 400.0 * np.sin(2.0 * np.pi * vis_winding_x / 8192.0) + 100.0 * np.cos(2.0 * np.pi * vis_winding_x / 4096.0))
    line_winding, = ax.plot(vis_winding_x / vis_scale, vis_winding_y / vis_scale, color='magenta', linewidth=1.5, linestyle='--', label='Winding Boundary')
    
    # Draw winding road
    line_road, = ax.plot(X_road / vis_scale, Y_road / vis_scale, color='cyan', linewidth=2.0, linestyle='-', label='Mountain Road')
    
    plt.legend(handles=[rect_playable, rect_flat_north, line_winding, line_road], loc='upper right', facecolor='black', labelcolor='white')
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
        
    # Draw winding boundary line in detail
    vis_winding_detail_x = np.arange(2048, 6144, 32)
    vis_winding_detail_y = (4096.0 + 400.0 * np.sin(2.0 * np.pi * vis_winding_detail_x / 8192.0) + 100.0 * np.cos(2.0 * np.pi * vis_winding_detail_x / 4096.0))
    line_wind, = ax.plot((vis_winding_detail_x / vis_scale) - p_start, (vis_winding_detail_y / vis_scale) - p_start, color='magenta', linewidth=2.5, linestyle='--', label='Winding Boundary')
    
    # Draw winding road in detail
    line_rd, = ax.plot((X_road / vis_scale) - p_start, (Y_road / vis_scale) - p_start, color='cyan', linewidth=2.5, linestyle='-', label='Mountain Road')
    ax.legend(handles=[line_wind, line_rd], loc='upper right', facecolor='black', labelcolor='white')
    
    ax.text(10, 40, "FLAT VALLEY FLOOR (North)", color='yellow', fontsize=10, fontweight='bold')
    ax.text(10, 470, "FLAT PLATEAU (South)", color='orange', fontsize=10, fontweight='bold')
    
    # The irregular forest hill has been removed.
    
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
