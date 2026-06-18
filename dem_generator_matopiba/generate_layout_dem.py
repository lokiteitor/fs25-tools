#!/usr/bin/env python3
import os
import argparse
import time
import math
import numpy as np
from PIL import Image
from scipy.ndimage import distance_transform_edt

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
    
    # Vertical ramp profile for the western strip (from blue_boundary to south_boundary)
    # Reach the 250m plateau early (500m before the southern playable border)
    # to create a flat base landing ("como una escalera").
    base_size = 500.0 * (S / 8192.0)
    denom = max(1.0, south_boundary - base_size - blue_boundary)
    t_y = np.clip((y_warped - blue_boundary) / denom, 0.0, 1.0)
    H_west = 5.0 + (250.0 - 5.0) * t_y
    
    # Constant ramp width for uniform slope across the map
    ramp_width = 500.0
    
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
    
    # 5. Add Realistic Imperfections
    print("4. Adding realistic imperfections (slope ravines, erosion gullies & micro-roughness)...")
    # 5a. Slope imperfections (general organic ridges and valleys)
    slope_noise = generate_fractal_noise_2d((S, S), [16, 32, 64], [12.0, 6.0, 3.0], seed=args.seed + 102)
    slope_mask = 4.0 * w_slope * (1.0 - w_slope) # Only active on slopes (reaches 1.0 at midpoint)
    baseline_meters += slope_noise * slope_mask
    
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
    baseline_meters -= gullies * slope_mask
    
    # 5c. Micro-roughness in flat terrain areas (smoothed to avoid bumpy farming fields)
    micro_roughness = generate_fractal_noise_2d((S, S), [64, 128, 256], [0.15, 0.08, 0.04], seed=args.seed + 103)
    baseline_meters += micro_roughness
    

    
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
