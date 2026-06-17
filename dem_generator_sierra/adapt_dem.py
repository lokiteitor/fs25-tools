import os
import time
import math
import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter, distance_transform_edt

# For generating the visual map
import matplotlib
matplotlib.use('Agg') # Non-interactive backend
import matplotlib.pyplot as plt
from matplotlib.colors import LightSource

def main():
    t_start = time.time()
    print("=== FS25 DEM Adaptor Script ===")
    
    # Paths
    dem_path = "dem.png"
    output_dem_path = "dem_processed.png"
    output_vis_path = "dem_visual.png"
    
    if not os.path.exists(dem_path):
        print(f"Error: {dem_path} not found in current directory.")
        return
        
    print(f"1. Loading original DEM from '{dem_path}'...")
    img = Image.open(dem_path)
    arr_orig = np.array(img, dtype=np.float32)
    print(f"   DEM Shape: {arr_orig.shape}, Mode: {img.mode}")
    print(f"   Original range: Min={arr_orig.min():.1f}, Max={arr_orig.max():.1f}, Mean={arr_orig.mean():.1f}")
    
    print("2. Detecting depressions and lake beds ('huecos')...")
    # We blur the terrain with a large sigma to get the regional trend
    smoothed = gaussian_filter(arr_orig, sigma=25)
    dip = smoothed - arr_orig
    
    # Hole mask: pixels below absolute water level (6000) OR containing local dips (> 6000)
    hole_mask = (arr_orig < 6000) | (dip > 6000)
    print(f"   Hole pixels: {np.sum(hole_mask)} ({np.sum(hole_mask) / arr_orig.size * 100:.2f}%)")
    
    print("3. Filling the detected holes using Euclidean Distance Transform...")
    t_edt = time.time()
    # distance_transform_edt finds the nearest non-hole pixel
    distances, indices = distance_transform_edt(hole_mask, return_indices=True)
    
    arr_filled = arr_orig.copy()
    y_nearest = indices[0]
    x_nearest = indices[1]
    arr_filled[hole_mask] = arr_orig[y_nearest[hole_mask], x_nearest[hole_mask]]
    print(f"   Distance transform filled in {time.time() - t_edt:.2f}s")
    
    print("4. Blending and smoothing filled regions...")
    # Smooth the filled regions so they transition naturally (avoiding Voronoi lines)
    arr_smoothed_holes = gaussian_filter(arr_filled, sigma=15)
    arr_filled[hole_mask] = arr_smoothed_holes[hole_mask]
    
    print("5. Flattening farmyards with smooth margins...")
    # Coordinates of the 8 farmyards from osm_generator_4096/genmap.py (x0, y0, x1, y1)
    yards = [
        (3088, 3607, 3316, 4076), # Southeast farmyard
        (780, 24, 1008, 489),     # Northwest farmyard
        (1292, 268, 1524, 489),   # Northern road industrial zone 1
        (2316, 268, 2548, 489),   # Northern road industrial zone 2
        (3340, 268, 3572, 489),   # Northern road industrial zone 3
        (268, 3607, 500, 3828),   # Southern road industrial zone 1
        (1292, 3607, 1524, 3828), # Southern road industrial zone 2
        (2316, 3607, 2548, 3828)  # Southern road industrial zone 3
    ]
    
    arr_processed = arr_filled.copy()
    margin = 30.0  # 30-meter smooth transition margin
    
    for idx, (x0, y0, x1, y1) in enumerate(yards):
        # Clamp coordinates to valid ranges
        x0_c = max(0, min(4096, x0))
        x1_c = max(0, min(4096, x1))
        y0_c = max(0, min(4096, y0))
        y1_c = max(0, min(4096, y1))
        
        # Calculate target height as the median of the filled DEM in this area
        yard_sub = arr_processed[y0_c:y1_c+1, x0_c:x1_c+1]
        H_target = np.median(yard_sub)
        print(f"   Yard {idx} ({x0},{y0} to {x1},{y1}): Flattening to height = {H_target:.1f}")
        
        # Define neighborhood box including margin
        bx0 = max(0, int(x0_c - margin - 5))
        bx1 = min(4096, int(x1_c + margin + 5))
        by0 = max(0, int(y0_c - margin - 5))
        by1 = min(4096, int(y1_c + margin + 5))
        
        # Blend height inside and around the farmyard
        for y in range(by0, by1 + 1):
            for x in range(bx0, bx1 + 1):
                dx = max(0.0, x0_c - x, x - x1_c)
                dy = max(0.0, y0_c - y, y - y1_c)
                d = math.sqrt(dx*dx + dy*dy)
                
                if d == 0:
                    arr_processed[y, x] = H_target
                elif d <= margin:
                    # Cosine ramp blend
                    w = 0.5 * (1.0 + math.cos(math.pi * d / margin))
                    arr_processed[y, x] = w * H_target + (1.0 - w) * arr_filled[y, x]
                    
    print(f"6. Saving final DEM heightmap to '{output_dem_path}'...")
    # Save as 32-bit signed integer (mode 'I') to preserve 16-bit grayscale values
    img_out = Image.fromarray(arr_processed.astype(np.int32), mode="I")
    img_out.save(output_dem_path)
    print(f"   Saved '{output_dem_path}' successfully.")
    
    print("7. Generating visual comparison map ('dem_visual.png')...")
    # Build 3D relief using a light source
    ls = LightSource(azdeg=315, altdeg=45)
    
    # Compute hillshades
    hs_orig = ls.shade(arr_orig, cmap=plt.get_cmap('terrain'), vert_exag=0.1, blend_mode='overlay')
    hs_proc = ls.shade(arr_processed, cmap=plt.get_cmap('terrain'), vert_exag=0.1, blend_mode='overlay')
    
    # Set up matplotlib figure
    fig, axes = plt.subplots(1, 2, figsize=(20, 10), dpi=150)
    
    # Subplot 1: Original DEM
    axes[0].imshow(hs_orig)
    axes[0].set_title("Original DEM Map (with holes / lake beds)", fontsize=16, fontweight='bold', pad=15)
    axes[0].axis('off')
    
    # Highlight the holes in the original DEM in red overlay
    # Downsample overlay for speed and nicer rendering
    axes[0].imshow(hole_mask, cmap='Reds', alpha=0.25, interpolation='nearest')
    
    # Subplot 2: Processed DEM
    axes[1].imshow(hs_proc)
    axes[1].set_title("Processed DEM Map (holes filled, yards flattened)", fontsize=16, fontweight='bold', pad=15)
    axes[1].axis('off')
    
    # Draw farmyards on the processed map as green rectangles
    for idx, (x0, y0, x1, y1) in enumerate(yards):
        rect = plt.Rectangle((x0, y0), x1-x0, y1-y0, fill=False, edgecolor='#00FF00', linewidth=2, linestyle='--')
        axes[1].add_patch(rect)
        axes[1].text(x0 + 10, y0 - 15, f"Yard {idx}", color='#00FF00', fontsize=10, fontweight='bold')
        
    plt.tight_layout()
    plt.savefig(output_vis_path, bbox_inches='tight')
    plt.close()
    print(f"   Saved visual comparison to '{output_vis_path}'.")
    
    t_end = time.time()
    print(f"\n=== Process Completed Successfully in {t_end - t_start:.2f} seconds ===")
    print(f"Output files:")
    print(f" - Heightmap: {output_dem_path}")
    print(f" - Visualization: {output_vis_path}")

if __name__ == "__main__":
    main()
