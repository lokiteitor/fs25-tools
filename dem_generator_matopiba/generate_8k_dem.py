#!/usr/bin/env python3
import os
import argparse
import time
import math
import numpy as np
from PIL import Image

# For generating high-quality visual relief maps
import matplotlib
matplotlib.use('Agg') # Non-interactive backend
import matplotlib.pyplot as plt
from matplotlib.colors import LightSource

def generate_perlin_noise_2d(shape, res, seed=42):
    """
    Generates a 2D numpy array of Perlin noise.
    shape: (height, width)
    res: (res_y, res_x) - grid resolution (must divide shape)
    """
    np.random.seed(seed)
    
    grid_y, grid_x = res
    delta = (shape[0] // grid_y, shape[1] // grid_x)
    
    # Gradients on the grid vertices
    angles = np.random.uniform(0, 2 * np.pi, size=(grid_y + 1, grid_x + 1))
    gradients = np.dstack((np.cos(angles), np.sin(angles)))
    
    # Grids of coordinates
    y = np.arange(shape[0], dtype=np.float32) / delta[0]
    x = np.arange(shape[1], dtype=np.float32) / delta[1]
    
    # Coordinate fractional and grid parts
    y_floor = np.floor(y).astype(np.int32)
    x_floor = np.floor(x).astype(np.int32)
    
    # Distances to cell corners
    dy_top = y[:, None] - y_floor[:, None]
    dx_left = x[None, :] - x_floor[None, :]
    
    dy_bot = dy_top - 1.0
    dx_right = dx_left - 1.0
    
    # Interpolant weight function: 6t^5 - 15t^4 + 10t^3
    def fade(t):
        return t * t * t * (t * (t * 6 - 15) + 10)
        
    fade_y = fade(dy_top)
    fade_x = fade(dx_left)
    
    # Retrieve gradients for the 4 corners of each cell
    g00 = gradients[y_floor[:, None], x_floor[None, :]]
    g10 = gradients[y_floor[:, None] + 1, x_floor[None, :]]
    g01 = gradients[y_floor[:, None], x_floor[None, :] + 1]
    g11 = gradients[y_floor[:, None] + 1, x_floor[None, :] + 1]
    
    # Compute dot products
    n00 = g00[..., 0] * dx_left + g00[..., 1] * dy_top
    n10 = g10[..., 0] * dx_left + g10[..., 1] * dy_bot
    n01 = g01[..., 0] * dx_right + g01[..., 1] * dy_top
    n11 = g11[..., 0] * dx_right + g11[..., 1] * dy_bot
    
    # Interpolate along x
    n0 = n00 * (1.0 - fade_x) + n01 * fade_x
    n1 = n10 * (1.0 - fade_x) + n11 * fade_x
    
    # Interpolate along y
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
    parser = argparse.ArgumentParser(description="Scale a DEM map and fill the background with Perlin noise.")
    parser.add_argument("--input", default="map_dem.png", help="Path to input 2K DEM image.")
    parser.add_argument("--output", default="map_dem_8k.png", help="Path to output 8K DEM image.")
    parser.add_argument("--output-visual", default="map_dem_8k_visual.png", help="Path to output 3D visualization.")
    parser.add_argument("--canvas-size", type=int, default=8192, help="Output canvas size in pixels.")
    parser.add_argument("--center-size", type=int, default=4096, help="Target size for input image inside canvas.")
    parser.add_argument("--blend-margin", type=int, default=256, help="Blend margin width in pixels.")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for Perlin noise.")
    parser.add_argument("--noise-scale", type=float, default=1.0, help="Global scaling factor for noise amplitude.")
    
    args = parser.parse_args()
    
    t_start = time.time()
    print("=== FS25 8K DEM Generator with Perlin Noise Border ===")
    
    if not os.path.exists(args.input):
        print(f"Error: Input file '{args.input}' not found.")
        return
        
    print(f"1. Loading input DEM heightmap from '{args.input}'...")
    img_in = Image.open(args.input)
    print(f"   Original dimensions: {img_in.size}, Mode: {img_in.mode}")
    
    # Load raw heightmap data
    arr_orig = np.array(img_in, dtype=np.float32)
    print(f"   Original elevation range: Min={arr_orig.min():.1f}, Max={arr_orig.max():.1f}")
    
    print(f"2. Scaling input DEM to {args.center_size}x{args.center_size} using Bicubic interpolation...")
    img_resized = img_in.resize((args.center_size, args.center_size), Image.Resampling.BICUBIC)
    arr_center = np.array(img_resized, dtype=np.float32)
    
    print(f"3. Initializing canvas of size {args.canvas_size}x{args.canvas_size}...")
    S = args.canvas_size
    C = args.center_size
    offset = (S - C) // 2
    
    print(f"   Placement offset: {offset} pixels (coordinates {offset} to {offset + C - 1})")
    
    # 4. Create base clamping array (coordinates extended from the borders)
    print("4. Extending borders of the center image to fill the canvas baseline...")
    x_indices = np.clip(np.arange(S) - offset, 0, C - 1)
    y_indices = np.clip(np.arange(S) - offset, 0, C - 1)
    baseline = arr_center[y_indices[:, None], x_indices[None, :]]
    
    # 5. Generate procedural terrain (valleys, hills, and mountains) for the non-playable border
    print("5. Generating procedural terrain (valleys, hills, mountains) for non-playable border...")
    
    # 5a. Selector map (low frequency noise to divide the terrain into valleys, hills, and mountains)
    selector = (
        generate_perlin_noise_2d((S, S), (4, 4), seed=args.seed) * 0.7 +
        generate_perlin_noise_2d((S, S), (8, 8), seed=args.seed + 1) * 0.3
    )
    # Normalize selector to range [-1.0, 1.0]
    selector = np.clip(selector / 0.7, -1.0, 1.0)
    
    # 5b. Define blend weights for valleys, hills, and mountains using smoothstep
    def smoothstep(edge0, edge1, x):
        t = np.clip((x - edge0) / (edge1 - edge0), 0.0, 1.0)
        return t * t * (3.0 - 2.0 * t)
        
    w_mountain = smoothstep(-0.2, 0.4, selector)
    w_valley = smoothstep(0.2, -0.4, selector)
    w_hill = 1.0 - w_mountain - w_valley
    
    # 5c. Generate Valleys (low amplitude fractal noise)
    print("   - Generating valley noise...")
    noise_valley = generate_fractal_noise_2d((S, S), [16, 32, 64], [1000, 500, 250], seed=args.seed + 10)
    
    # 5d. Generate Hills (medium amplitude fractal noise)
    print("   - Generating hill noise...")
    noise_hill = generate_fractal_noise_2d((S, S), [16, 32, 64, 128], [4000, 2000, 1000, 500], seed=args.seed + 20)
    
    # 5e. Generate Mountains (high amplitude ridged Perlin noise for sharp ridges)
    print("   - Generating mountain noise (ridged Perlin)...")
    m1 = (1.0 - np.abs(generate_perlin_noise_2d((S, S), (8, 8), seed=args.seed + 30))) * 18000
    m2 = (1.0 - np.abs(generate_perlin_noise_2d((S, S), (16, 16), seed=args.seed + 31))) * 8000
    m3 = (1.0 - np.abs(generate_perlin_noise_2d((S, S), (32, 32), seed=args.seed + 32))) * 3000
    noise_mountain = m1 + m2 + m3
    
    # Combine the terrains using the selector weights
    procedural_noise = (
        w_valley * noise_valley +
        w_hill * noise_hill +
        w_mountain * noise_mountain
    )
    
    # Apply global scale factor
    procedural_noise *= args.noise_scale
    
    # 6. Perform smooth cosine blending at the boundary
    print(f"6. Blending center heightmap with procedural noise (transition margin: {args.blend_margin}px)...")
    y_coords, x_coords = np.indices((S, S), dtype=np.float32)
    
    # Distance from center box
    dx = np.maximum(0.0, np.maximum(offset - x_coords, x_coords - (offset + C - 1)))
    dy = np.maximum(0.0, np.maximum(offset - y_coords, y_coords - (offset + C - 1)))
    dist = np.sqrt(dx*dx + dy*dy)
    
    # Compute noise blend weight: 0.0 in center, smoothly rises to 1.0 outside margin
    w_noise = np.zeros((S, S), dtype=np.float32)
    
    # Inside center box (dist == 0), w_noise is 0.0
    # In transition zone (0 < dist <= blend_margin)
    trans_mask = (dist > 0) & (dist <= args.blend_margin)
    w_noise[trans_mask] = 0.5 * (1.0 - np.cos(np.pi * dist[trans_mask] / args.blend_margin))
    # Outside transition zone (dist > blend_margin)
    w_noise[dist > args.blend_margin] = 1.0
    
    # Final elevation = baseline + procedural_noise * w_noise
    final_elevation = baseline + procedural_noise * w_noise
    
    # Clamp to valid 16-bit range (0 to 65535)
    final_elevation = np.clip(final_elevation, 0.0, 65535.0)
    
    # Save output heightmap
    print(f"7. Saving new 8K DEM heightmap to '{args.output}'...")
    img_out = Image.fromarray(final_elevation.astype(np.int32), mode="I")
    img_out.save(args.output)
    print(f"   Heightmap saved successfully. Size: {img_out.size}")
    print(f"   New elevation range: Min={final_elevation.min():.1f}, Max={final_elevation.max():.1f}")
    
    # 8. Generate 3D shaded relief comparison map
    print(f"8. Generating 3D relief visual comparison map in '{args.output_visual}'...")
    # Scale down for visual rendering speed and memory efficiency
    vis_scale = 8
    orig_vis = arr_orig[::vis_scale // 2, ::vis_scale // 2] if arr_orig.shape[0] > 1024 else arr_orig
    new_vis = final_elevation[::vis_scale, ::vis_scale]
    
    ls = LightSource(azdeg=315, altdeg=45)
    hs_orig = ls.shade(orig_vis, cmap=plt.get_cmap('terrain'), vert_exag=0.1, blend_mode='overlay')
    hs_new = ls.shade(new_vis, cmap=plt.get_cmap('terrain'), vert_exag=0.1, blend_mode='overlay')
    
    fig, axes = plt.subplots(1, 2, figsize=(20, 10), dpi=150)
    
    axes[0].imshow(hs_orig)
    axes[0].set_title(f"Original DEM ({img_in.size[0]}x{img_in.size[1]})", fontsize=16, fontweight='bold', pad=15)
    axes[0].axis('off')
    
    axes[1].imshow(hs_new)
    axes[1].set_title(f"Expanded DEM ({S}x{S} with Perlin background)", fontsize=16, fontweight='bold', pad=15)
    axes[1].axis('off')
    
    # Highlight the boundaries of the original image inside the expanded one
    rect_playable = plt.Rectangle((offset / vis_scale, offset / vis_scale), 
                                  C / vis_scale, C / vis_scale, 
                                  fill=False, edgecolor='white', linewidth=2, linestyle='--',
                                  label='Scaled Center (4km)')
    axes[1].add_patch(rect_playable)
    
    # Add a border for transition zone
    margin_vis = args.blend_margin / vis_scale
    rect_transition = plt.Rectangle(((offset - args.blend_margin) / vis_scale, (offset - args.blend_margin) / vis_scale), 
                                     (C + 2 * args.blend_margin) / vis_scale, (C + 2 * args.blend_margin) / vis_scale, 
                                     fill=False, edgecolor='yellow', linewidth=1.5, linestyle=':',
                                     label='Transition Zone')
    axes[1].add_patch(rect_transition)
    axes[1].legend(loc='upper right', facecolor='black', labelcolor='white')
    
    plt.tight_layout()
    plt.savefig(args.output_visual, bbox_inches='tight')
    plt.close()
    
    print(f"   Visual comparison map saved to '{args.output_visual}'.")
    print(f"=== Process completed successfully in {time.time() - t_start:.2f}s ===")

if __name__ == "__main__":
    main()
