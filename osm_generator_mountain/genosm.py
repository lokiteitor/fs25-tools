import random
import xml.etree.ElementTree as ET
from xml.dom import minidom
import os

from common import (
    S, MILES, PPM, m,
    TH_P, TH_S, TH_T, W_ROAD_BORDER, GAP, BORDER,
    hlines, yards,
    build_northern_strip, build_southern_strip,
    TOWN_X0, TOWN_X1, TOWN_Y0, TOWN_Y1, TOWN_STREET_SPACING,
    TOWN_VSTREETS, TOWN_HSTREETS, COL4_FIELDS,
    IRREGULAR_FOREST_PTS, get_merged_forest_edge_y, get_south_dirt_road_y_end,
    NORTH_DIRT_ROADS_X, SOUTH_DIRT_ROADS_X,
    NORTH_DIRT_ROAD_Y, SOUTH_DIRT_ROAD_Y,
    build_middle_fields,
)

# --- Configurations ---
random.seed(20240605)

# --- Georeferencing ---
# Center: (27.07991, -109.70707)
# Map Size: 4096x4096m (2048m distance from center)
min_lon = -109.7277558150625
min_lat = 27.061491919529106
max_lon = -109.6863841849375
max_lat = 27.098328080470894

def to_gps(x, y):
    lon = min_lon + (x / S) * (max_lon - min_lon)
    lat = max_lat - (y / S) * (max_lat - min_lat)
    return lat, lon

# --- Node & Way Registries ---
node_id_counter = 1
way_id_counter = 1
node_map = {}     # (rounded_x, rounded_y) -> node_id
node_coords = {}  # node_id -> (lat, lon)
ways = []         # list of dict: {'id': int, 'nodes': [int], 'tags': dict}

def get_node(x, y):
    global node_id_counter
    key = (round(x, 2), round(y, 2))
    if key not in node_map:
        node_map[key] = node_id_counter
        lat, lon = to_gps(x, y)
        node_coords[node_id_counter] = (lat, lon)
        node_id_counter += 1
    return node_map[key]

def create_unique_node(x, y):
    global node_id_counter
    nid = node_id_counter
    lat, lon = to_gps(x, y)
    node_coords[nid] = (lat, lon)
    node_id_counter += 1
    return nid

def add_way(nodes_list, tags):
    global way_id_counter
    ways.append({
        'id': way_id_counter,
        'nodes': nodes_list,
        'tags': tags
    })
    way_id_counter += 1

# ================= 1. FIELDS (Farmland Parcels) =================
# Winding mountain road (follows the path from dem_new.png)
from scipy.interpolate import CubicSpline
import numpy as np
y_control = np.array([1152, 1272, 1302, 1332, 1522, 1552, 1582, 1772, 1802, 1832, 2022, 2052, 2082, 2272, 2302, 2332, 2522, 2552, 2582, 2752], dtype=np.float32)
x_control = np.array([1452, 1702, 1552, 1702, 2402, 2552, 2402, 1702, 1552, 1702, 2402, 2552, 2402, 1702, 1552, 1702, 2402, 2552, 2402, 3752], dtype=np.float32)
cs = CubicSpline(y_control, x_control, bc_type='clamped')

road_pts = []
# 1. North connection (straight vertical from y=512 to y=1152 at x=1452)
for y_val in np.linspace(512, 1152, 15):
    road_pts.append((1452.0, float(y_val)))

# 2. Middle winding road (spline from y=1152 to y=2752, skipping the first node because it's (1452, 1152))
for y_val in np.linspace(1152, 2752, 150)[1:]:
    x_val = float(cs(y_val))
    road_pts.append((x_val, float(y_val)))

# 3. South connection (straight vertical from y=2752 to y=3584 at x=3752, skipping first because it's (3752, 2752))
for y_val in np.linspace(2752, 3584, 15)[1:]:
    road_pts.append((3752.0, float(y_val)))

parcels = []

# 1. Northern strip (Row 0): [0, 512] - Medium farmlands
build_northern_strip(parcels)

# 2. Middle grid fields (bounded by roads and contours)
build_middle_fields(parcels)

# 3. Southern strip: [3584, 4096] - Medium farmlands
build_southern_strip(parcels)

# --- Farmland Clipping Geometry ---
clips = []
# 25m unassigned border clip
clips.append((0, 0, S, BORDER))
clips.append((0, S - BORDER, S, S))
clips.append((0, 0, BORDER, S))
clips.append((S - BORDER, 0, S, S))

clips.append((TOWN_X0, TOWN_Y0, TOWN_X1, TOWN_Y1)) # Town residential clip

# Add yards to clips to avoid overlap with farmland
for y_yd in yards:
    clips.append(y_yd)

# Add road footprints to clips (only horizontal roads y=512 and y=3584)
for y in hlines:
    hw = TH_P/2 + W_ROAD_BORDER
    clips.append((0, y - hw, S, y + hw))

# Add winding road forest rectangle to clips
clips.append((1400.0, 1152.0, 2700.0, 2552.0))

# Add winding road connection segments to clips (those outside the forest y-range)
hw_primary = 23.0
for i in range(len(road_pts) - 1):
    x1, y1 = road_pts[i]
    x2, y2 = road_pts[i+1]
    if y1 < 1152.0 or y1 > 2552.0:
        clips.append((
            min(x1, x2) - hw_primary,
            min(y1, y2) - hw_primary,
            max(x1, x2) + hw_primary,
            max(y1, y2) + hw_primary
        ))

# Add vertical dirt road footprints to clips
hw_dirt = TH_T/2 + W_ROAD_BORDER
for x in NORTH_DIRT_ROADS_X:
    y_end = get_merged_forest_edge_y(x, 'upper') - GAP
    clips.append((x - hw_dirt, 512.0, x + hw_dirt, y_end))
for x in SOUTH_DIRT_ROADS_X:
    y_end = get_south_dirt_road_y_end(x)
    clips.append((x - hw_dirt, y_end, x + hw_dirt, 3584.0))

# Add horizontal dirt road footprints to clips
clips.append((0, NORTH_DIRT_ROAD_Y - hw_dirt, S, NORTH_DIRT_ROAD_Y + hw_dirt))
clips.append((0, SOUTH_DIRT_ROAD_Y - hw_dirt, S, SOUTH_DIRT_ROAD_Y + hw_dirt))

def subtract_single(A, B):
    ax0, ay0, ax1, ay1 = A
    bx0, by0, bx1, by1 = B
    
    # Find intersection region
    ix0 = max(ax0, bx0)
    iy0 = max(ay0, by0)
    ix1 = min(ax1, bx1)
    iy1 = min(ay1, by1)
    
    # Check if there is a valid intersection
    if ix0 >= ix1 or iy0 >= iy1:
        return [A]
        
    parts = []
    # 1. Top region
    if ay0 < iy0:
        parts.append((ax0, ay0, ax1, iy0))
    # 2. Bottom region
    if iy1 < ay1:
        parts.append((ax0, iy1, ax1, ay1))
    # 3. Left region
    if ax0 < ix0:
        parts.append((ax0, iy0, ix0, iy1))
    # 4. Right region
    if ix1 < ax1:
        parts.append((ix1, iy0, ax1, iy1))
        
    return [p for p in parts if (p[2] - p[0] > 1.0 and p[3] - p[1] > 1.0)]

def subtract_rects(subject, clip_list):
    current_rects = [subject]
    for clip in clip_list:
        next_rects = []
        for r in current_rects:
            next_rects.extend(subtract_single(r, clip))
        current_rects = next_rects
    return current_rects

# Add parcels as ways, clipping them with other area elements first (rectangles only)
for p in parcels:
    if isinstance(p, list) or (isinstance(p, tuple) and len(p) > 4):
        # It's a polygon! We create nodes for each vertex directly and add it as a way
        ns = [get_node(px, py) for (px, py) in p]
        ns.append(ns[0])
        add_way(ns, {'landuse': 'farmland'})
    else:
        # It's a rectangle!
        x0, y0, x1, y1 = p
        clipped_parts = subtract_rects(p, clips)
        for (cx0, cy0, cx1, cy1) in clipped_parts:
            margin = 6
            cx0_s = cx0 + margin
            cx1_s = cx1 - margin
            cy0_s = cy0 + margin
            cy1_s = cy1 - margin
            
            if cx1_s - cx0_s <= 10.0 or cy1_s - cy0_s <= 10.0:
                continue
                
            ns = [
                create_unique_node(cx0_s, cy0_s),
                create_unique_node(cx1_s, cy0_s),
                create_unique_node(cx1_s, cy1_s),
                create_unique_node(cx0_s, cy1_s),
            ]
            ns.append(ns[0])
            add_way(ns, {'landuse': 'farmland'})

# ================= 2. TOWN =================

town_nodes = [
    create_unique_node(TOWN_X0, TOWN_Y0),
    create_unique_node(TOWN_X1, TOWN_Y0),
    create_unique_node(TOWN_X1, TOWN_Y1),
    create_unique_node(TOWN_X0, TOWN_Y1),
]
town_nodes.append(town_nodes[0])
add_way(town_nodes, {'landuse': 'residential'})

# Town streets
for i in range(1, TOWN_VSTREETS + 1):
    x = TOWN_X0 + i * TOWN_STREET_SPACING
    pts = [TOWN_Y0 + 10] + [TOWN_Y0 + j * TOWN_STREET_SPACING for j in range(1, TOWN_HSTREETS + 1)] + [TOWN_Y1]
    ns = [get_node(x, y_val) for y_val in pts]
    add_way(ns, {'highway': 'secondary'})

for j in range(1, TOWN_HSTREETS + 1):
    y = TOWN_Y0 + j * TOWN_STREET_SPACING
    pts = [TOWN_X0 + 10] + [TOWN_X0 + i * TOWN_STREET_SPACING for i in range(1, TOWN_VSTREETS + 1)] + [TOWN_X1]
    ns = [get_node(x_val, y) for x_val in pts]
    add_way(ns, {'highway': 'secondary'})

# ================= 2.5 FARMYARDS =================
for (x0, y0, x1, y1) in yards:
    ns = [
        create_unique_node(x0, y0),
        create_unique_node(x1, y0),
        create_unique_node(x1, y1),
        create_unique_node(x0, y1),
    ]
    ns.append(ns[0])
    add_way(ns, {'landuse': 'farmyard', 'building': 'industrial'})

if len(IRREGULAR_FOREST_PTS) > 0:
    irr_forest_nodes = [create_unique_node(x, y) for (x, y) in IRREGULAR_FOREST_PTS]
    irr_forest_nodes.append(irr_forest_nodes[0])
    add_way(irr_forest_nodes, {'natural': 'wood', 'landuse': 'forest', 'name': 'Bosque de la Meseta y del Camino Sinuoso'})

# ================= 3. ROADS =================
# Horizontal roads
for y in hlines:
    coords = [0, S]
    # Add intersection points with town streets if applicable
    if y == 512 or y == 1024 or y == 2048 or y == 3584:
        for i in range(1, TOWN_VSTREETS + 1):
            coords.append(TOWN_X0 + i * TOWN_STREET_SPACING)
    # Add intersection points with the connecting mountain road
    if y == 512:
        coords.append(1452.0)
    if y == 3584:
        coords.append(3752.0)
    coords = sorted(list(set(coords)))
    ns = [get_node(x, y) for x in coords]
    add_way(ns, {'highway': 'primary'})

# Winding mountain road (reusing pre-generated road_pts)

road_nodes = [get_node(x, y) for (x, y) in road_pts]
add_way(road_nodes, {'highway': 'primary', 'name': 'Camino de la Meseta'})

# Dirt roads (tracks) from main roads to forest edge
for i, x in enumerate(NORTH_DIRT_ROADS_X):
    y_end = get_merged_forest_edge_y(x, 'upper') - GAP
    # Generate nodes from y=512 down to y_end
    pts = [(x, float(y_val)) for y_val in np.linspace(512, y_end, 5)]
    road_nodes = [get_node(px, py) for (px, py) in pts]
    add_way(road_nodes, {'highway': 'track', 'name': f'Sendero Norte {i+1}', 'surface': 'dirt'})

for i, x in enumerate(SOUTH_DIRT_ROADS_X):
    y_end = get_south_dirt_road_y_end(x)
    # Generate nodes from y=3584 up to y_end
    pts = [(x, float(y_val)) for y_val in np.linspace(3584, y_end, 5)]
    road_nodes = [get_node(px, py) for (px, py) in pts]
    add_way(road_nodes, {'highway': 'track', 'name': f'Sendero Sur {i+1}', 'surface': 'dirt'})

# Horizontal dirt roads (tracks)
# North horizontal dirt road at y=1050
north_horiz_pts = [25.0, 600.0, 1452.0, 2700.0, 3500.0, 4071.0]
north_horiz_nodes = [get_node(x_val, NORTH_DIRT_ROAD_Y) for x_val in north_horiz_pts]
add_way(north_horiz_nodes, {'highway': 'track', 'name': 'Sendero Horizontal Norte', 'surface': 'dirt'})

# South horizontal dirt road at y=3200
south_horiz_pts = [25.0, 800.0, 1800.0, 2600.0, 3752.0, 4071.0]
south_horiz_nodes = [get_node(x_val, SOUTH_DIRT_ROAD_Y) for x_val in south_horiz_pts]
add_way(south_horiz_nodes, {'highway': 'track', 'name': 'Sendero Horizontal Sur', 'surface': 'dirt'})

# ================= 4. BUILD OSM XML =================
root = ET.Element('osm', {
    'version': '0.6',
    'generator': 'osm_generator_py'
})

# Bounds
ET.SubElement(root, 'bounds', {
    'minlat': str(min_lat),
    'minlon': str(min_lon),
    'maxlat': str(max_lat),
    'maxlon': str(max_lon)
})

# Nodes
sorted_node_ids = sorted(node_coords.keys())
for nid in sorted_node_ids:
    lat, lon = node_coords[nid]
    ET.SubElement(root, 'node', {
        'id': str(nid),
        'lat': f"{lat:.8f}",
        'lon': f"{lon:.8f}",
        'version': '1',
        'changeset': '1',
        'user': 'osm_generator',
        'uid': '1',
        'timestamp': '2026-06-02T00:00:00Z'
    })

# Ways
for w in ways:
    w_el = ET.SubElement(root, 'way', {
        'id': str(w['id']),
        'version': '1',
        'changeset': '1',
        'user': 'osm_generator',
        'uid': '1',
        'timestamp': '2026-06-02T00:00:00Z'
    })
    for ref in w['nodes']:
        ET.SubElement(w_el, 'nd', {
            'ref': str(ref)
        })
    for k, v in w['tags'].items():
        ET.SubElement(w_el, 'tag', {
            'k': k,
            'v': v
        })

# Format and write
script_dir = os.path.dirname(os.path.abspath(__file__))
os.makedirs(os.path.join(script_dir, "outputs"), exist_ok=True)
xml_str = ET.tostring(root, encoding='utf-8')
parsed = minidom.parseString(xml_str)
pretty_xml = parsed.toprettyxml(indent="  ")

cleaned_lines = [line for line in pretty_xml.split('\n') if line.strip() != ""]
cleaned_xml = '\n'.join(cleaned_lines)

output_file = os.path.join(script_dir, "outputs/zoning_map.osm")
with open(output_file, "w", encoding="utf-8") as f:
    f.write(cleaned_xml)

print(f"OSM file successfully written to {output_file}")
print(f"Generated {len(node_coords)} nodes and {len(ways)} ways.")
