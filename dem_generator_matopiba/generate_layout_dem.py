#!/usr/bin/env python3
import os
import argparse
import time
import math
import numpy as np
from PIL import Image
from scipy.ndimage import distance_transform_edt, gaussian_filter
from scipy.interpolate import make_interp_spline

# For generating high-quality visual relief maps
import matplotlib
matplotlib.use('Agg') # Non-interactive backend
import matplotlib.pyplot as plt
from matplotlib.colors import LightSource

def generate_perlin_noise_2d(shape, res, seed=42):
    """
    Generates a 2D numpy array of Perlin noise.
    """
    np.random.seed(seed)
    grid_y, grid_x = res
    delta = (shape[0] // grid_y, shape[1] // grid_x)
    
    angles = np.random.uniform(0, 2 * np.pi, size=(grid_y + 1, grid_x + 1))
    gradients = np.dstack((np.cos(angles), np.sin(angles)))
    
    y = np.arange(shape[0], dtype=np.float32) / delta[0]
    x = np.arange(shape[1], dtype=np.float32) / delta[1]
    
    y_floor = np.floor(y).astype(np.int32)
    x_floor = np.floor(x).astype(np.int32)
    
    dy_top = y[:, None] - y_floor[:, None]
    dx_left = x[None, :] - x_floor[None, :]
    dy_bot = dy_top - 1.0
    dx_right = dx_left - 1.0
    
    def fade(t):
        return t * t * t * (t * (t * 6 - 15) + 10)
        
    fade_y = fade(dy_top)
    fade_x = fade(dx_left)
    
    g00 = gradients[y_floor[:, None], x_floor[None, :]]
    g10 = gradients[y_floor[:, None] + 1, x_floor[None, :]]
    g01 = gradients[y_floor[:, None], x_floor[None, :] + 1]
    g11 = gradients[y_floor[:, None] + 1, x_floor[None, :] + 1]
    
    n00 = g00[..., 0] * dx_left + g00[..., 1] * dy_top
    n10 = g10[..., 0] * dx_left + g10[..., 1] * dy_bot
    n01 = g01[..., 0] * dx_right + g01[..., 1] * dy_top
    n11 = g11[..., 0] * dx_right + g11[..., 1] * dy_bot
    
    n0 = n00 * (1.0 - fade_x) + n01 * fade_x
    n1 = n10 * (1.0 - fade_x) + n11 * fade_x
    return n0 * (1.0 - fade_y) + n1 * fade_y

def generate_fractal_noise_2d(shape, resolutions, amplitudes, seed=42):
    """
    Generates multi-octave fractal Perlin noise.
    """
    noise = np.zeros(shape, dtype=np.float32)
    for i, (res, amp) in enumerate(zip(resolutions, amplitudes)):
        noise += generate_perlin_noise_2d(shape, (res, res), seed=seed + i) * amp
    return noise

def main():
    parser = argparse.ArgumentParser(description="Generate a DEM map following a specific layout with realistic imperfections.")
    script_dir = os.path.dirname(os.path.abspath(__file__))
    parser.add_argument("--output", default=os.path.join(script_dir, "map_dem_new.png"), help="Path to output DEM image.")
    parser.add_argument("--output-visual", default=os.path.join(script_dir, "map_dem_new_visual.png"), help="Path to output 3D visualization.")
    parser.add_argument("--canvas-size", type=int, default=8192, help="Output canvas size in pixels.")
    parser.add_argument("--center-size", type=int, default=4096, help="Playable area size in pixels.")
    parser.add_argument("--blend-margin", type=int, default=256, help="Blend margin width in pixels.")
    parser.add_argument("--seed", type=int, default=12345, help="Random seed for procedural border.")
    parser.add_argument("--noise-scale", type=float, default=1.0, help="Scale factor for border noise amplitude.")
    
    args = parser.parse_args()
    t_start = time.time()
    print("=== FS25 8K DEM Layout Generator with Realistic Imperfections ===")
    
    S = args.canvas_size
    C = args.center_size
    offset = (S - C) // 2
    
    # 1. Coordinate Grids
    y_coords, x_coords = np.indices((S, S), dtype=np.float32)
    
    # 2. Domain Warping for organic, winding boundaries
    print("1. Computing coordinate warping (domain warping) for organic ridges...")
    # Low frequency noise for warping
    warp_x = generate_fractal_noise_2d((S, S), [16, 32], [80.0, 30.0], seed=args.seed + 100)
    warp_y = generate_fractal_noise_2d((S, S), [16, 32], [80.0, 30.0], seed=args.seed + 101)
    
    x_warped = x_coords + warp_x
    y_warped = y_coords + warp_y
    
    # 3. Define the Low flat area & West North-to-South Ramp (Scenario A)
    print("2. Generating baseline geometry (low north flat area & west north-to-south ramp)...")
    blue_boundary = float(offset + 600)
    south_boundary = float(offset + C)
    
    # Extend the slope in the North-East quadrant to accommodate the road
    # Default ramp_width is 500m.
    # We increase it smoothly up to 1300m in the North-East region.
    dx_ne = x_coords - 5500.0 * (S / 8192.0)
    dy_ne = y_coords - 3100.0 * (S / 8192.0)
    dist_ne = np.sqrt(dx_ne**2 + dy_ne**2)
    # Cosine falloff over 1600 meters (scaled)
    w_ne = np.clip(1.0 - dist_ne / (1600.0 * (S / 8192.0)), 0.0, 1.0)
    w_ne = 0.5 * (1.0 - np.cos(np.pi * w_ne))
    
    # ramp_width is now a 2D map
    ramp_width = 500.0 + 800.0 * w_ne
    
    # Vertical ramp profile for the western strip (from blue_boundary to south_boundary)
    # Reach the 250m plateau early (500m before the southern playable border)
    # to create a flat base landing ("como una escalera").
    base_size = 500.0 * (S / 8192.0)
    denom = max(1.0, south_boundary - base_size - blue_boundary)
    t_y = np.clip((y_warped - blue_boundary) / denom, 0.0, 1.0)
    H_west = 5.0 + (250.0 - 5.0) * t_y
    
    # Low zone mask is the L-shape (for distance transform)
    low_zone_mask = (x_warped <= blue_boundary) | (y_warped <= blue_boundary)
    
    # Compute distance to the lowland L-shape
    dist_to_low = distance_transform_edt(~low_zone_mask)
    t = np.clip(dist_to_low / ramp_width, 0.0, 1.0)
    w_slope = 0.5 * (1.0 - np.cos(np.pi * t))
    
    # Blend starting height smoothly in the quadrant based on distance components
    dx = np.maximum(0.0, x_warped - blue_boundary)
    dy = np.maximum(0.0, y_warped - blue_boundary)
    sum_d = dx + dy
    sum_d = np.where(sum_d == 0.0, 1e-5, sum_d)
    w_blend = dy / sum_d
    
    # Smooth the junction only at the south where the ramp and the plateau meet,
    # without affecting the slope in the northern and middle parts of the map.
    w_blend = w_blend + (1.0 - w_blend) * (t_y ** 4)
    
    H_start = 5.0 + (H_west - 5.0) * w_blend
    
    # Base elevation in meters
    baseline_meters = H_start + (250.0 - H_start) * w_slope
    
    # --- Winding Road Generation (Camino Ondulado) ---
    print("3. Generating winding road in the North-East slope...")
    scale = S / 8192.0
    pts = np.array([
        [5200.0, 2600.0],
        [5700.0, 2850.0],
        [5000.0, 3100.0],
        [5700.0, 3350.0],
        [5200.0, 3750.0]
    ]) * scale
    
    t_pts = np.linspace(0.0, 1.0, len(pts))
    spline = make_interp_spline(t_pts, pts, k=3)
    
    # Evaluate at high resolution to avoid gaps
    t_eval = np.linspace(0.0, 1.0, 10000)
    road_coords = spline(t_eval)
    road_x = road_coords[:, 0]
    road_y = road_coords[:, 1]
    
    # Calculate cumulative distance along the road
    dx_road = np.diff(road_x)
    dy_road = np.diff(road_y)
    seg_lengths = np.sqrt(dx_road**2 + dy_road**2)
    cum_dist = np.zeros(len(road_x))
    cum_dist[1:] = np.cumsum(seg_lengths)
    total_length = cum_dist[-1]
    
    # Road height goes from 5m to 250m
    road_height = 5.0 + (250.0 - 5.0) * (cum_dist / total_length)
    
    # Rasterize the road onto a grid
    road_grid = np.zeros((S, S), dtype=bool)
    rx = np.clip(road_x.astype(np.int32), 0, S - 1)
    ry = np.clip(road_y.astype(np.int32), 0, S - 1)
    road_grid[ry, rx] = True
    
    # Calculate distance transform to the road
    dist_to_road, indices = distance_transform_edt(~road_grid, return_indices=True)
    nearest_y = indices[0]
    nearest_x = indices[1]
    
    # Populate the road height grid
    road_height_grid = np.zeros((S, S), dtype=np.float32)
    road_height_grid[ry, rx] = road_height
    nearest_road_height = road_height_grid[nearest_y, nearest_x]
    
    # Road parameters
    road_r = 8.0 * scale
    margin = 50.0 * scale  # Increased margin from 15.0 to 50.0 for much wider shoulders
    blend_r = road_r + margin
    
    # Longitudinal weight based on road height to ensure it is 100% flat sideways on the slope
    w_long = np.clip((nearest_road_height - 5.0) / 5.0, 0.0, 1.0) * np.clip((250.0 - nearest_road_height) / 5.0, 0.0, 1.0)
    w_long = 0.5 * (1.0 - np.cos(np.pi * w_long))
    
    # Elevate the terrain around the road to create a natural supporting ridge/embankment
    influence_r = 160.0 * scale
    w_bump = np.clip(1.0 - dist_to_road / influence_r, 0.0, 1.0)
    w_bump = 0.5 * (1.0 - np.cos(np.pi * w_bump))
    baseline_meters += 2.0 * w_bump * w_long
    
    # Blend the flat resting platforms at the curve apexes
    idx1 = np.argmin(np.abs(road_y - 2850.0 * scale))
    idx2 = np.argmin(np.abs(road_y - 3100.0 * scale))
    idx3 = np.argmin(np.abs(road_y - 3350.0 * scale))
    
    ax1, ay1, ah1 = road_x[idx1], road_y[idx1], road_height[idx1]
    ax2, ay2, ah2 = road_x[idx2], road_y[idx2], road_height[idx2]
    ax3, ay3, ah3 = road_x[idx3], road_y[idx3], road_height[idx3]
    
    px1, py1 = ax1 - 100.0 * scale, ay1
    px2, py2 = ax2 + 100.0 * scale, ay2
    px3, py3 = ax3 - 100.0 * scale, ay3
    
    dist_p1 = np.sqrt((x_coords - px1)**2 + (y_coords - py1)**2)
    dist_p2 = np.sqrt((x_coords - px2)**2 + (y_coords - py2)**2)
    dist_p3 = np.sqrt((x_coords - px3)**2 + (y_coords - py3)**2)
    
    # 100m flat radius + 40m blend radius (200m flat surface, 240m total influence width inside curve)
    w_p1 = np.clip(1.0 - (dist_p1 - 100.0 * scale) / (40.0 * scale), 0.0, 1.0)
    w_p1 = 0.5 * (1.0 - np.cos(np.pi * w_p1))
    
    w_p2 = np.clip(1.0 - (dist_p2 - 100.0 * scale) / (40.0 * scale), 0.0, 1.0)
    w_p2 = 0.5 * (1.0 - np.cos(np.pi * w_p2))
    
    w_p3 = np.clip(1.0 - (dist_p3 - 100.0 * scale) / (40.0 * scale), 0.0, 1.0)
    w_p3 = 0.5 * (1.0 - np.cos(np.pi * w_p3))
    
    w_p_sum = w_p1 + w_p2 + w_p3
    w_p_sum_clip = np.clip(w_p_sum, 0.0, 1.0)
    
    baseline_meters = w_p1 * ah1 + w_p2 * ah2 + w_p3 * ah3 + (1.0 - w_p_sum_clip) * baseline_meters
    
    # Smooth the terrain surrounding the road (using Gaussian filter)
    # to eliminate sharp cuts and blend the road naturally into the hillside.
    smoothed_baseline = gaussian_filter(baseline_meters, sigma=35.0 * scale)
    w_smooth = np.clip(1.0 - dist_to_road / (160.0 * scale), 0.0, 1.0)
    w_smooth = 0.5 * (1.0 - np.cos(np.pi * w_smooth)) * w_long
    baseline_meters = w_smooth * smoothed_baseline + (1.0 - w_smooth) * baseline_meters
    
    # Apply the flat road surface and blend the shoulders
    t_road = np.clip((blend_r - dist_to_road) / margin, 0.0, 1.0)
    w_road = 0.5 * (1.0 - np.cos(np.pi * t_road))
    w_combined = w_road * w_long
    
    baseline_meters = w_combined * nearest_road_height + (1.0 - w_combined) * baseline_meters
    
    # Road suppression mask for terrain features (gullies, roughness)
    road_suppression_base = np.clip((dist_to_road - road_r) / margin, 0.0, 1.0)
    road_suppression = 1.0 - (1.0 - road_suppression_base) * w_long
    road_suppression = road_suppression * (1.0 - w_p_sum_clip)
    
    # 5. Add Realistic Imperfections
    print("4. Adding realistic imperfections (slope ravines, erosion gullies & micro-roughness)...")
    # 5a. Slope imperfections (general organic ridges and valleys)
    slope_noise = generate_fractal_noise_2d((S, S), [16, 32, 64], [12.0, 6.0, 3.0], seed=args.seed + 102)
    slope_mask = 4.0 * w_slope * (1.0 - w_slope) # Only active on slopes (reaches 1.0 at midpoint)
    baseline_meters += slope_noise * slope_mask * road_suppression
    
    # 5b. Anisotropic Water Erosion Gullies (Cárcavas) running downhill
    print("   - Generating directional water erosion gullies on slopes...")
    # Western slope erosion (horizontal channels: varies fast in Y, slow in X)
    gw1 = np.maximum(0.0, generate_perlin_noise_2d((S, S), (64, 8), seed=args.seed + 150))
    gw2 = np.maximum(0.0, generate_perlin_noise_2d((S, S), (128, 16), seed=args.seed + 151))
    gullies_west = (gw1 * 12.0 + gw2 * 6.0) ** 1.3
    
    # Northern slope erosion (vertical channels: varies fast in X, slow in Y)
    gn1 = np.maximum(0.0, generate_perlin_noise_2d((S, S), (8, 64), seed=args.seed + 152))
    gn2 = np.maximum(0.0, generate_perlin_noise_2d((S, S), (16, 128), seed=args.seed + 153))
    gullies_north = (gn1 * 12.0 + gn2 * 6.0) ** 1.3
    
    # Blend erosion channels based on quadrant position to align with downhill gradient
    gullies = w_blend * gullies_west + (1.0 - w_blend) * gullies_north
    baseline_meters -= gullies * slope_mask * road_suppression
    
    # 5c. Micro-roughness in flat terrain areas (smoothed to avoid bumpy farming fields)
    micro_roughness = generate_fractal_noise_2d((S, S), [64, 128, 256], [0.15, 0.08, 0.04], seed=args.seed + 103)
    baseline_meters += micro_roughness * road_suppression
    
    # 5d. Plateau irregular terrain (altiplano undulations, peak-to-peak range of 5 meters)
    print("   - Adding irregular undulations to the plateau (altiplano)...")
    w_plateau = np.clip((w_slope - 0.9) / 0.1, 0.0, 1.0)
    w_plateau = 0.5 * (1.0 - np.cos(np.pi * w_plateau))
    
    raw_plateau_noise = generate_fractal_noise_2d((S, S), [16, 32, 64], [1.0, 0.5, 0.2], seed=args.seed + 200)
    p_min, p_max = raw_plateau_noise.min(), raw_plateau_noise.max()
    if p_max - p_min > 1e-5:
        scaled_plateau_noise = (raw_plateau_noise - p_min) / (p_max - p_min) - 0.5  # Range -0.5 to 0.5
        scaled_plateau_noise *= 5.0  # Range -2.5 to 2.5 meters (5m peak-to-peak difference)
    else:
        scaled_plateau_noise = raw_plateau_noise * 0.0
        
    baseline_meters += scaled_plateau_noise * w_plateau * road_suppression
    
    # Convert meters to raw heightmap units
    baseline = baseline_meters * 100.0
    
    # 6. Carve the lake (Pink Zone) in the bottom-right corner
    print("5. Carving bottom-right lake with organic shoreline...")
    # Center lake at (5800, 5800) which is on the 250m plateau
    lake_cx, lake_cy = 5800.0, 5800.0
    lake_bottom_half = 60.0  # 120x120m flat bottom
    lake_shore_half = 90.0   # 180x180m shore boundary
    bank_width = lake_shore_half - lake_bottom_half
    
    # Warp coordinates of the lake to make the shoreline organic
    lake_warp_x = generate_fractal_noise_2d((S, S), [32, 64], [15.0, 5.0], seed=args.seed + 104)
    lake_warp_y = generate_fractal_noise_2d((S, S), [32, 64], [15.0, 5.0], seed=args.seed + 105)
    
    dist_lake = np.maximum(np.abs(x_coords + lake_warp_x - lake_cx), np.abs(y_coords + lake_warp_y - lake_cy))
    
    lake_mask_bottom = dist_lake <= lake_bottom_half
    lake_mask_slope = (dist_lake > lake_bottom_half) & (dist_lake <= lake_shore_half)
    
    # Lake bottom is 25m below the surrounding 250m plateau, so it sits at 225m (22500 raw units)
    lake_bottom_units = 225.0 * 100.0
    
    # Apply flat bottom
    baseline[lake_mask_bottom] = lake_bottom_units
    
    # Apply bank slope blending smoothly with the surrounding terrain
    t_lake = (dist_lake[lake_mask_slope] - lake_bottom_half) / bank_width
    lake_slope_profile = 0.5 * (1.0 - np.cos(np.pi * t_lake))
    baseline[lake_mask_slope] = lake_bottom_units + (baseline[lake_mask_slope] - lake_bottom_units) * lake_slope_profile
    
    # 7. Generate procedural non-playable border (valleys, hills, and ridged mountains)
    print("6. Generating procedural background details for the border...")
    # 7a. Selector map
    selector = (
        generate_perlin_noise_2d((S, S), (4, 4), seed=args.seed) * 0.7 +
        generate_perlin_noise_2d((S, S), (8, 8), seed=args.seed + 1) * 0.3
    )
    selector = np.clip(selector / 0.7, -1.0, 1.0)
    
    # 7b. Smoothstep weights for terrain categories
    def smoothstep(edge0, edge1, x):
        t_val = np.clip((x - edge0) / (edge1 - edge0), 0.0, 1.0)
        return t_val * t_val * (3.0 - 2.0 * t_val)
        
    w_mountain = smoothstep(-0.2, 0.4, selector)
    w_valley = smoothstep(0.2, -0.4, selector)
    w_hill = 1.0 - w_mountain - w_valley
    
    # 7c. Generate Valleys (low amplitude fractal noise)
    print("   - Generating valley noise...")
    noise_valley = generate_fractal_noise_2d((S, S), [16, 32, 64], [1000, 500, 250], seed=args.seed + 10)
    
    # 7d. Generate Hills (medium amplitude fractal noise)
    print("   - Generating hill noise...")
    noise_hill = generate_fractal_noise_2d((S, S), [16, 32, 64, 128], [4000, 2000, 1000, 500], seed=args.seed + 20)
    
    # 7e. Generate Mountains (high amplitude ridged Perlin noise)
    print("   - Generating mountain noise...")
    m1 = (1.0 - np.abs(generate_perlin_noise_2d((S, S), (8, 8), seed=args.seed + 30))) * 18000
    m2 = (1.0 - np.abs(generate_perlin_noise_2d((S, S), (16, 16), seed=args.seed + 31))) * 8000
    m3 = (1.0 - np.abs(generate_perlin_noise_2d((S, S), (32, 32), seed=args.seed + 32))) * 3000
    noise_mountain = m1 + m2 + m3
    
    procedural_noise = (
        w_valley * noise_valley +
        w_hill * noise_hill +
        w_mountain * noise_mountain
    )
    procedural_noise *= args.noise_scale
    
    # 8. Blend the playable terrain and the procedural border at the 4096 playable boundary
    print(f"7. Blending terrain with procedural border (transition margin: {args.blend_margin}px)...")
    dx = np.maximum(0.0, np.maximum(offset - x_coords, x_coords - (offset + C - 1)))
    dy = np.maximum(0.0, np.maximum(offset - y_coords, y_coords - (offset + C - 1)))
    dist = np.sqrt(dx*dx + dy*dy)
    
    w_noise = np.zeros((S, S), dtype=np.float32)
    trans_mask = (dist > 0) & (dist <= args.blend_margin)
    w_noise[trans_mask] = 0.5 * (1.0 - np.cos(np.pi * dist[trans_mask] / args.blend_margin))
    w_noise[dist > args.blend_margin] = 1.0
    
    # Apply noise ONLY to the border
    final_elevation = baseline + procedural_noise * w_noise
    
    # Clamp to valid 16-bit range
    final_elevation = np.clip(final_elevation, 0.0, 65535.0)
    
    # 9. Save final DEM map
    print(f"8. Saving final 8K DEM heightmap to '{args.output}'...")
    img_out = Image.fromarray(final_elevation.astype(np.int32), mode="I")
    img_out.save(args.output)
    print(f"   Saved heightmap. Size: {img_out.size}, Range: Min={final_elevation.min():.1f}, Max={final_elevation.max():.1f}")
    
    # 10. Generate 3D visual relief map
    print(f"9. Generating 3D visual relief map in '{args.output_visual}'...")
    vis_scale = 8
    vis_data = final_elevation[::vis_scale, ::vis_scale]
    
    ls = LightSource(azdeg=315, altdeg=45)
    hs = ls.shade(vis_data, cmap=plt.get_cmap('terrain'), vert_exag=0.1, blend_mode='overlay')
    
    fig, ax = plt.subplots(figsize=(12, 12), dpi=150)
    ax.imshow(hs)
    ax.axis('off')
    ax.set_title("Layout-Based DEM Map (8192x8192 - Wavy Slopes, Northern Lowland & Western Ramp)", fontsize=16, fontweight='bold', pad=15)
    
    # Add playable border rectangle
    rect_playable = plt.Rectangle((offset / vis_scale, offset / vis_scale), 
                                  C / vis_scale, C / vis_scale, 
                                  fill=False, edgecolor='white', linewidth=2, linestyle='--',
                                  label='Playable Area (4km)')
    ax.add_patch(rect_playable)
    
    # Add transition border rectangle
    rect_transition = plt.Rectangle(((offset - args.blend_margin) / vis_scale, (offset - args.blend_margin) / vis_scale), 
                                     (C + 2 * args.blend_margin) / vis_scale, (C + 2 * args.blend_margin) / vis_scale, 
                                     fill=False, edgecolor='yellow', linewidth=1.5, linestyle=':',
                                     label='Transition Zone')
    ax.add_patch(rect_transition)
    
    ax.legend(loc='upper right', facecolor='black', labelcolor='white')
    
    plt.savefig(args.output_visual, bbox_inches='tight')
    plt.close()
    
    print(f"   Visual map saved to '{args.output_visual}'.")
    print(f"=== Completed successfully in {time.time() - t_start:.2f}s ===")

if __name__ == "__main__":
    main()
