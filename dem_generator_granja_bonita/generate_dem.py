#!/usr/bin/env python3
import os
import time
import math
import numpy as np
from PIL import Image
from scipy.ndimage import distance_transform_edt, binary_fill_holes, gaussian_filter, label, binary_dilation, binary_erosion

def val_noise(shape, grid_size, weight, seed=20260608):
    """Generates smooth value noise by upscaling a small random grid using bicubic interpolation."""
    np.random.seed(seed)
    small = np.random.uniform(-1.0, 1.0, size=(grid_size, grid_size)).astype(np.float32)
    temp_img = Image.fromarray(small)
    temp_img = temp_img.resize((shape[1], shape[0]), Image.Resampling.BICUBIC)
    return np.array(temp_img) * weight

def main():
    t_start = time.time()
    print("=== Farming Simulator DEM Generator - Granja Bonita (Updated Water Coordinates) ===")
    
    # 1. Configuration
    S_px = 12288       # Canvas size (12K)
    C_px = 8192        # Playable area (8K)
    offset = (S_px - C_px) // 2  # 2048px offset
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    layout_path = os.path.join(script_dir, "dem_layout.jpg")
    output_dem_path = os.path.join(script_dir, "map_dem_new.png")
    
    if not os.path.exists(layout_path):
        print(f"Error: Layout image not found at {layout_path}")
        return
        
    print(f"Loading layout from {layout_path}...")
    layout_img = Image.open(layout_path)
    layout_rgb = np.array(layout_img.convert('RGB'))
    
    # 2. Segment colors in layout (800x600 px)
    # Orange: mountain ranges (close loops on left/right borders and fill holes)
    orange_mask = (layout_rgb[:,:,0] > 200) & (layout_rgb[:,:,1] > 80) & (layout_rgb[:,:,1] < 180) & (layout_rgb[:,:,2] < 80)
    
    # Close borders to prepare for filling
    closed_orange = orange_mask.copy()
    closed_orange[:, 0] = True
    closed_orange[:, -1] = True
    
    initial_filled = binary_fill_holes(closed_orange)
    labeled_array, num_features = label(initial_filled)
    
    # Left mountain (Component 1) is already closed.
    # Right mountain (Component 2) has gaps and needs morphological closing.
    left_mtn = (labeled_array == 1)
    right_mtn_outline = (labeled_array == 2)
    
    # Apply dilation-fill-erosion to right mountain only (R = 15 px)
    struct = np.ones((15, 15), dtype=bool)
    dilated_right = binary_dilation(right_mtn_outline, structure=struct)
    dilated_right[:, -1] = True
    filled_right = binary_fill_holes(dilated_right)
    eroded_right = binary_erosion(filled_right, structure=struct)
    
    # Combine filled mountains
    filled_orange = left_mtn | eroded_right
    
    # Black/Gray: road path
    gray_mask = (layout_rgb[:,:,0] < 120) & (layout_rgb[:,:,1] < 120) & (layout_rgb[:,:,2] < 120)
    
    # 3. Resize and construct masks at 8192x8192 px (playable area)
    print("Resizing masks to 8K playable area...")
    
    # Orange mountain mask (filled/solid mountains)
    orange_img = Image.fromarray(filled_orange.astype(np.uint8) * 255)
    orange_resized = orange_img.resize((C_px, C_px), Image.Resampling.BILINEAR)
    orange_smooth = gaussian_filter(np.array(orange_resized).astype(np.float32), sigma=15.0)
    orange_mask_8k = orange_smooth > 10.0
    
    # Road mask
    road_img = Image.fromarray(gray_mask.astype(np.uint8) * 255)
    road_resized = road_img.resize((C_px, C_px), Image.Resampling.BILINEAR)
    road_smooth = gaussian_filter(np.array(road_resized).astype(np.float32), sigma=8.0)
    road_mask_8k = road_smooth > 10.0
    
    # Red flat area mask: Complete logically with 6 clean rectangular fields (aligned)
    print("Generating clean rectangular red zones logically...")
    red_mask_8k = np.zeros((C_px, C_px), dtype=bool)
    # Top row boxes (left, middle, right) - North Area (reduced to 1/4 size: 500x500m, touching North Hwy)
    red_mask_8k[930:1430, 850:1350] = True
    red_mask_8k[930:1430, 3850:4350] = True
    red_mask_8k[930:1430, 6650:7150] = True
    # Bottom row boxes (left, middle, right) - South Area (reduced to 1/2 size: 700x700m, touching South Hwy)
    red_mask_8k[6770:7470, 750:1450] = True
    red_mask_8k[6770:7470, 3750:4450] = True
    red_mask_8k[6770:7470, 6550:7250] = True
    
    # 4. Generate base terrain with rolling hills (0-10m variation, base 35m)
    print("Generating base terrain with rolling hills (35m base)...")
    hills_noise = (
        val_noise((C_px, C_px), 16, 6.0, seed=456) +
        val_noise((C_px, C_px), 32, 3.0, seed=457) +
        val_noise((C_px, C_px), 64, 1.0, seed=458)
    )
    # Normalize hills noise to range [0.0, 10.0] meters
    h_min, h_max = hills_noise.min(), hills_noise.max()
    hills_noise = (hills_noise - h_min) / (h_max - h_min) * 10.0
    
    playable_terrain = 35.0 + hills_noise
    
    # 5. Generate mountains (orange mask) up to 350m height
    print("Generating solid mountains from filled area...")
    dist_to_orange_border = distance_transform_edt(orange_mask_8k)
    max_dist_orange = dist_to_orange_border.max()
    if max_dist_orange > 0:
        dist_norm = dist_to_orange_border / max_dist_orange
    else:
        dist_norm = np.zeros_like(dist_to_orange_border)
        
    mountain_noise = (
        val_noise((C_px, C_px), 16, 0.6, seed=123) +
        val_noise((C_px, C_px), 32, 0.3, seed=124) +
        val_noise((C_px, C_px), 64, 0.1, seed=125)
    )
    m_noise_min, m_noise_max = mountain_noise.min(), mountain_noise.max()
    mountain_noise = (mountain_noise - m_noise_min) / (m_noise_max - m_noise_min)
    
    # Mountains rise up to 350m total, so 315m above the 35m base.
    mountain_height = 315.0 * (dist_norm ** 0.7) * (0.5 + 0.5 * mountain_noise)
    playable_terrain = playable_terrain + mountain_height
    
    # 6. Carve the road path (black/gray mask)
    print("Carving road path...")
    dist_to_road = distance_transform_edt(~road_mask_8k)
    
    road_flat_r = 4.0
    road_transition_w = 20.0
    t_road = np.clip((dist_to_road - road_flat_r) / road_transition_w, 0.0, 1.0)
    w_road = 0.5 * (1.0 + np.cos(np.pi * t_road))
    
    playable_terrain = w_road * 35.0 + (1.0 - w_road) * playable_terrain
    
    # 7. Flatten red areas (completely flat at 35.0m)
    print("Flattening red zone fields (35m flat)...")
    dist_to_red = distance_transform_edt(~red_mask_8k)
    
    red_transition_w = 80.0
    t_red = np.clip(dist_to_red / red_transition_w, 0.0, 1.0)
    w_red = 0.5 * (1.0 + np.cos(np.pi * t_red))
    
    playable_terrain = w_red * 35.0 + (1.0 - w_red) * playable_terrain
    
    # 8. Assemble full 12K canvas
    print(f"Assembling full {S_px}x{S_px} map...")
    final_terrain = np.full((S_px, S_px), 35.0, dtype=np.float32)
    final_terrain[offset:offset+C_px, offset:offset+C_px] = playable_terrain
    
    # 9. Generate procedural border terrain (outside playable area)
    print("Generating procedural border mountains and valleys...")
    border_noise = (
        val_noise((S_px, S_px), 12, 280.0, seed=999) +
        val_noise((S_px, S_px), 24, 100.0, seed=1000) +
        val_noise((S_px, S_px), 48, 30.0, seed=1001)
    )
    b_min, b_max = border_noise.min(), border_noise.max()
    border_noise = (border_noise - b_min) / (b_max - b_min)
    border_terrain = 35.0 + border_noise * 315.0
    
    # Calculate distance to playable area boundary
    x_grid, y_grid = np.indices((S_px, S_px), dtype=np.float32)
    dx = np.maximum(0.0, np.maximum(offset - x_grid, x_grid - (offset + C_px - 1)))
    dy = np.maximum(0.0, np.maximum(offset - y_grid, y_grid - (offset + C_px - 1)))
    dist_to_playable = np.sqrt(dx*dx + dy*dy)
    
    # Blend transition margin: 256 meters
    blend_margin = 256.0
    t_blend = np.clip(dist_to_playable / blend_margin, 0.0, 1.0)
    w_blend = 0.5 * (1.0 - np.cos(np.pi * t_blend))
    
    final_terrain = (1.0 - w_blend) * final_terrain + w_blend * border_terrain
    
    # 10. Carve geometric lakes (180x180m, 25m deep, 600m inside) and outward canals (20m wide, 15m deep, extended)
    print("Carving channels pointing outward and corner lakes moved 600m inside...")
    
    lake_mask = np.zeros((S_px, S_px), dtype=bool)
    canal_mask = np.zeros((S_px, S_px), dtype=bool)
    
    # Top-left corner coordinates (absolute)
    # Lake is moved 600m inside the playable area (so x and y in [offset + 600, offset + 780])
    lake_mask[offset+600:offset+780, offset+600:offset+780] = True
    # Canals point OUTWARD (from lake edge all the way to the edge of the map)
    # Horizontal canal: extends left from lake to the map edge (x in [0, offset + 600], y centered on lake)
    canal_mask[offset+680:offset+700, 0:offset+600] = True
    # Vertical canal: extends up from lake to the map edge (y in [0, offset + 600], x centered on lake)
    canal_mask[0:offset+600, offset+680:offset+700] = True
    
    # Bottom-right corner coordinates (absolute)
    # Lake is moved 600m inside the playable area
    lake_mask[offset+C_px-780:offset+C_px-600, offset+C_px-780:offset+C_px-600] = True
    # Canals point OUTWARD (from lake edge all the way to the edge of the map)
    # Horizontal canal: extends right from lake to the map edge (x in [offset + C_px - 600, S_px])
    canal_mask[offset+C_px-700:offset+C_px-680, offset+C_px-600:S_px] = True
    # Vertical canal: extends down from lake to the map edge (y in [offset + C_px - 600, S_px])
    canal_mask[offset+C_px-600:S_px, offset+C_px-700:offset+C_px-680] = True
    
    # Flatten the terrain around the lakes and canals to 35m so they integrate cleanly
    water_mask = lake_mask | canal_mask
    dist_to_water = distance_transform_edt(~water_mask)
    water_buffer_w = 50.0
    t_water = np.clip(dist_to_water / water_buffer_w, 0.0, 1.0)
    w_water_flat = 0.5 * (1.0 + np.cos(np.pi * t_water))
    
    # Flatten surrounding buffer terrain to 35m base height
    final_terrain = w_water_flat * 35.0 + (1.0 - w_water_flat) * final_terrain
    
    # Now carve the water bodies
    dist_inside_lake = distance_transform_edt(lake_mask)
    dist_inside_canal = distance_transform_edt(canal_mask)
    
    # Lake bottom is 10.0m (25m depth)
    lake_bank_w = 15.0
    w_lake = np.clip(dist_inside_lake / lake_bank_w, 0.0, 1.0)
    w_lake = 0.5 * (1.0 - np.cos(np.pi * w_lake))
    lake_terrain = final_terrain * (1.0 - w_lake) + 10.0 * w_lake
    
    # Canal bottom is 20.0m (15m depth)
    canal_bank_w = 4.0
    w_canal = np.clip(dist_inside_canal / canal_bank_w, 0.0, 1.0)
    w_canal = 0.5 * (1.0 - np.cos(np.pi * w_canal))
    canal_terrain = final_terrain * (1.0 - w_canal) + 20.0 * w_canal
    
    # Apply to final_terrain
    final_terrain = np.where(canal_mask, canal_terrain, final_terrain)
    final_terrain = np.where(lake_mask, lake_terrain, final_terrain)
    
    # 11. Scale heights to raw heightmap units (1m = 100 units for 16-bit PNG)
    raw_heightmap = np.clip(final_terrain * 100.0, 0.0, 65535.0).astype(np.int32)
    
    print(f"Saving final 16-bit DEM heightmap to {output_dem_path}...")
    img_out = Image.fromarray(raw_heightmap, mode="I")
    img_out.save(output_dem_path)
    
    print(f"=== Success! Heightmap generated. ===")
    print(f"Dimensions: {img_out.size}")
    print(f"Elevation Range: {final_terrain.min():.2f}m to {final_terrain.max():.2f}m")
    print(f"Raw Range: {raw_heightmap.min()} to {raw_heightmap.max()}")
    print(f"Total time: {time.time() - t_start:.2f} seconds")

if __name__ == "__main__":
    main()
