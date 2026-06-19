#!/usr/bin/env python3
import os
import argparse
import numpy as np
import matplotlib.pyplot as plt
import xml.etree.ElementTree as ET
from xml.dom import minidom
from scipy.ndimage import distance_transform_edt
from scipy.interpolate import make_interp_spline

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

def get_elevation_grid(S=8192, C=4096, seed=12345):
    """
    Recreates the playable area elevation grid exactly as in generate_layout_dem.py
    """
    offset = (S - C) // 2
    y_coords, x_coords = np.indices((S, S), dtype=np.float32)
    
    # Warping noise
    warp_x = generate_fractal_noise_2d((S, S), [16, 32], [80.0, 30.0], seed=seed + 100)
    warp_y = generate_fractal_noise_2d((S, S), [16, 32], [80.0, 30.0], seed=seed + 101)
    
    x_warped = x_coords + warp_x
    y_warped = y_coords + warp_y
    
    blue_boundary = float(offset + 600)
    south_boundary = float(offset + C)
    
    # Ramp width 2D map (extended in the NE)
    dx_ne = x_coords - 5500.0 * (S / 8192.0)
    dy_ne = y_coords - 3100.0 * (S / 8192.0)
    dist_ne = np.sqrt(dx_ne**2 + dy_ne**2)
    w_ne = np.clip(1.0 - dist_ne / (1600.0 * (S / 8192.0)), 0.0, 1.0)
    w_ne = 0.5 * (1.0 - np.cos(np.pi * w_ne))
    
    ramp_width = 500.0 + 800.0 * w_ne
    
    # Vertical ramp on western strip
    base_size = 500.0 * (S / 8192.0)
    denom = max(1.0, south_boundary - base_size - blue_boundary)
    t_y = np.clip((y_warped - blue_boundary) / denom, 0.0, 1.0)
    H_west = 5.0 + (250.0 - 5.0) * t_y
    
    # Low zone L-shape
    low_zone_mask = (x_warped <= blue_boundary) | (y_warped <= blue_boundary)
    dist_to_low = distance_transform_edt(~low_zone_mask)
    t = np.clip(dist_to_low / ramp_width, 0.0, 1.0)
    w_slope = 0.5 * (1.0 - np.cos(np.pi * t))
    
    dx = np.maximum(0.0, x_warped - blue_boundary)
    dy = np.maximum(0.0, y_warped - blue_boundary)
    sum_d = dx + dy
    sum_d = np.where(sum_d == 0.0, 1e-5, sum_d)
    w_blend = dy / sum_d
    w_blend = w_blend + (1.0 - w_blend) * (t_y ** 4)
    
    H_start = 5.0 + (H_west - 5.0) * w_blend
    
    baseline_meters = H_start + (250.0 - H_start) * w_slope
    
    # Crop to playable area
    playable = baseline_meters[offset:offset+C, offset:offset+C]
    return playable

def main():
    parser = argparse.ArgumentParser(description="Generate an OSM file with the slope forest polygon and winding road from the DEM layout.")
    script_dir = os.path.dirname(os.path.abspath(__file__))
    parser.add_argument("--output-osm", default=os.path.join(script_dir, "map.osm"), help="Path to output OSM XML file.")
    args = parser.parse_args()
    
    print("=== Generating OSM for FS25 (Slope Forest & Winding Road) ===")
    
    # 1. Define bounds and geographic mapping
    min_lon = -109.7277558150625
    min_lat = 27.061491919529106
    max_lon = -109.6863841849375
    max_lat = 27.098328080470894
    C = 4096
    
    def px_to_latlon(x, y):
        # x is horizontal index (0 to 4095) -> maps to min_lon to max_lon
        # y is vertical index (0 to 4095) -> maps to max_lat to min_lat (inverted since image y=0 is North)
        lon = min_lon + (x / float(C)) * (max_lon - min_lon)
        lat = max_lat - (y / float(C)) * (max_lat - min_lat)
        return lat, lon
    
    # 2. Get elevation grid
    print("Generating baseline elevation model...")
    elevation = get_elevation_grid()
    
    # 3. Compute contours for the slope (10m to 240m)
    print("Finding slope contours at 10m and 240m...")
    fig_temp, ax_temp = plt.subplots()
    cs = ax_temp.contour(elevation, levels=[10.0, 240.0])
    
    paths_10 = cs.collections[0].get_paths()
    paths_240 = cs.collections[1].get_paths()
    plt.close(fig_temp)
    
    if len(paths_10) == 0 or len(paths_240) == 0:
        raise ValueError("Could not find appropriate contours for the slope boundaries.")
    
    # Get the main paths
    path_10 = paths_10[0].vertices
    path_240 = paths_240[0].vertices
    
    # Filter out the western ramp (x < 1000)
    x_min = 1000.0
    path_10 = path_10[path_10[:, 0] >= x_min]
    path_240 = path_240[path_240[:, 0] >= x_min]
    
    print(f"Path 10m has {len(path_10)} vertices. Path 240m has {len(path_240)} vertices (filtered x >= {x_min}).")
    
    # Simplify paths to avoid bloating the OSM XML
    # We take every 10th vertex
    step = 10
    p10 = path_10[::step]
    if not np.array_equal(p10[-1], path_10[-1]):
        p10 = np.vstack([p10, path_10[-1]])
        
    p240 = path_240[::step]
    if not np.array_equal(p240[-1], path_240[-1]):
        p240 = np.vstack([p240, path_240[-1]])
        
    # 4. Construct the closed polygon of the slope
    # Walk along p10 forward (West to East), then p240 backward (East to West)
    # This forms a single closed loop covering the slope.
    # Note: p10 starts at x=0 (West) and ends at x=4095 (East)
    # p240 starts at x=0 (West) and ends at x=4095 (East)
    # So we join p10 with p240 reversed, and close the loop by returning to p10[0]
    polygon_vertices = np.vstack([p10, p240[::-1], p10[0]])
    print(f"Constructed slope polygon with {len(polygon_vertices)} vertices.")
    
    # Winding road coordinates generation
    print("Generating winding road coordinates...")
    # The winding road control points on the 8192x8192 canvas:
    road_pts = np.array([
        [5200.0, 2600.0],
        [5700.0, 2850.0],
        [5000.0, 3100.0],
        [5700.0, 3350.0],
        [5200.0, 3750.0]
    ])
    
    t_pts = np.linspace(0.0, 1.0, len(road_pts))
    spline = make_interp_spline(t_pts, road_pts, k=3)
    
    # Evaluate spline
    t_eval = np.linspace(0.0, 1.0, 1000)
    road_coords_8k = spline(t_eval)
    
    # Subtract offset 2048 to get playable area coords (0 to 4095)
    offset = 2048.0
    road_coords_playable = road_coords_8k - offset
    
    # Simplify the road path to keep the OSM file clean (every 10th point)
    road_vertices = road_coords_playable[::10]
    if not np.array_equal(road_vertices[-1], road_coords_playable[-1]):
        road_vertices = np.vstack([road_vertices, road_coords_playable[-1]])
        
    print(f"Constructed winding road with {len(road_vertices)} vertices.")
    
    # 4.5. Western Road Generation (Wobbly on ramp, straight on plateau)
    print("Generating western road coordinates...")
    S = 8192
    warp_x_8k = generate_fractal_noise_2d((S, S), [16, 32], [80.0, 30.0], seed=12345 + 100)
    
    # Control points for the wobbly and turning segment
    # Sample the ramp segment at y_c from 0 to 3596 in playable coords
    west_pts = []
    ramp_y_samples = [0.0, 500.0, 1000.0, 1500.0, 2000.0, 2500.0, 3000.0, 3300.0, 3500.0, 3596.0]
    for y_c in ramp_y_samples:
        # We sample warp_x_8k at [y_8k, 2048 + 580]
        # x_c is 580 in playable coords (on top of the flat ramp strip, 20m from hillside at 600)
        warp_val = warp_x_8k[int(2048 + y_c), int(2048 + 580)]
        x_c = 580.0 - warp_val
        west_pts.append([x_c, y_c])
        
    # Add curve points on the platform to turn East onto the plateau (y=3596)
    # y=3650 is on the southern platform of the ramp (y >= 3596)
    warp_val_3650 = warp_x_8k[int(2048 + 3650), int(2048 + 580)]
    x_3650 = 580.0 - warp_val_3650
    west_pts.append([x_3650, 3650.0])
    
    # Apex of the curve on the platform
    west_pts.append([800.0, 3900.0])
    
    # Transitioning back to the straight line
    west_pts.append([1200.0, 3750.0])
    west_pts.append([1500.0, 3596.0])
    
    # Interpolate wobbly and turning segment using cumulative distance parameterization
    # to prevent spline wiggles/overshoots
    west_pts = np.array(west_pts)
    dists = np.sqrt(np.sum(np.diff(west_pts, axis=0)**2, axis=1))
    t_pts_w = np.zeros(len(west_pts))
    t_pts_w[1:] = np.cumsum(dists)
    t_pts_w = t_pts_w / t_pts_w[-1]
    
    spline_w = make_interp_spline(t_pts_w, west_pts, k=3)
    
    t_eval_w = np.linspace(0.0, 1.0, 500)
    west_first_part = spline_w(t_eval_w)
    
    # Straight segment from x=1500 to x=4095 on plateau (y=3596)
    west_straight_x = np.linspace(1500.0, 4095.0, 200)
    west_straight_y = np.ones_like(west_straight_x) * 3596.0
    west_straight = np.column_stack((west_straight_x, west_straight_y))
    
    # Combine both parts
    west_road_coords = np.vstack([west_first_part, west_straight])
    
    # Simplify the road path to keep the OSM file clean (every 10th point)
    west_road_vertices = west_road_coords[::10]
    if not np.array_equal(west_road_vertices[-1], west_road_coords[-1]):
        west_road_vertices = np.vstack([west_road_vertices, west_road_coords[-1]])
        
    print(f"Constructed western road with {len(west_road_vertices)} vertices.")
    
    # 5. Generate OSM XML
    print("Generating OSM XML structure...")
    osm_root = ET.Element("osm", version="0.6", generator="Antigravity OSM Generator")
    
    # Add bounds
    ET.SubElement(osm_root, "bounds", 
                  minlat=str(min_lat), minlon=str(min_lon), 
                  maxlat=str(max_lat), maxlon=str(max_lon))
    
    # Add nodes for the polygon (forest)
    node_ids = []
    current_node_id = 1
    for vertex in polygon_vertices:
        x, y = vertex
        lat, lon = px_to_latlon(x, y)
        
        ET.SubElement(osm_root, "node", 
                      id=str(current_node_id), 
                      lat=f"{lat:.9f}", 
                      lon=f"{lon:.9f}", 
                      version="1")
        node_ids.append(current_node_id)
        current_node_id += 1
        
    # Add nodes for the road
    road_node_ids = []
    for vertex in road_vertices:
        x, y = vertex
        lat, lon = px_to_latlon(x, y)
        
        ET.SubElement(osm_root, "node", 
                      id=str(current_node_id), 
                      lat=f"{lat:.9f}", 
                      lon=f"{lon:.9f}", 
                      version="1")
        road_node_ids.append(current_node_id)
        current_node_id += 1
        
    # Add nodes for the western road
    west_road_node_ids = []
    for vertex in west_road_vertices:
        x, y = vertex
        lat, lon = px_to_latlon(x, y)
        
        ET.SubElement(osm_root, "node", 
                      id=str(current_node_id), 
                      lat=f"{lat:.9f}", 
                      lon=f"{lon:.9f}", 
                      version="1")
        west_road_node_ids.append(current_node_id)
        current_node_id += 1
        
    # Add way for the forest polygon
    forest_way = ET.SubElement(osm_root, "way", id="1", version="1")
    for nid in node_ids:
        ET.SubElement(forest_way, "nd", ref=str(nid))
        
    # Add tags for the forest polygon
    ET.SubElement(forest_way, "tag", k="landuse", v="farmyard")
    ET.SubElement(forest_way, "tag", k="natural", v="wood")
    
    # Add way for the winding road
    road_way = ET.SubElement(osm_root, "way", id="2", version="1")
    for nid in road_node_ids:
        ET.SubElement(road_way, "nd", ref=str(nid))
        
    # Add tags for the winding road
    ET.SubElement(road_way, "tag", k="highway", v="primary")
    
    # Add way for the western road
    west_road_way = ET.SubElement(osm_root, "way", id="3", version="1")
    for nid in west_road_node_ids:
        ET.SubElement(west_road_way, "nd", ref=str(nid))
        
    # Add tags for the western road
    ET.SubElement(west_road_way, "tag", k="highway", v="primary")
    
    # Format and save XML
    xml_str = ET.tostring(osm_root, encoding="utf-8")
    parsed_xml = minidom.parseString(xml_str)
    pretty_xml = parsed_xml.toprettyxml(indent="  ")
    
    with open(args.output_osm, "w", encoding="utf-8") as f:
        f.write(pretty_xml)
    print(f"Saved OSM file to: {args.output_osm}")
    print("=== Finished successfully! ===")

if __name__ == '__main__':
    main()
