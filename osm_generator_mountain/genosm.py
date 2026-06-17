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
    IRREGULAR_FOREST_PTS,
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
parcels = []

# 1. Northern strip (Row 0): [0, 512] - Medium farmlands
build_northern_strip(parcels)

# 2. Southern strip: [3584, 4096] - Medium farmlands
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

# Clip fields inside the bounding box of the winding forest
if len(IRREGULAR_FOREST_PTS) > 0:
    min_x = min(p[0] for p in IRREGULAR_FOREST_PTS)
    max_x = max(p[0] for p in IRREGULAR_FOREST_PTS)
    min_y = min(p[1] for p in IRREGULAR_FOREST_PTS)
    max_y = max(p[1] for p in IRREGULAR_FOREST_PTS)
    clips.append((min_x - 12, min_y - 12, max_x + 12, max_y + 12))

# Add road footprints to clips (only horizontal roads y=512 and y=3584)
for y in hlines:
    hw = TH_P/2 + W_ROAD_BORDER
    clips.append((0, y - hw, S, y + hw))

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

# Add parcels as ways, clipping them with other area elements first
for p in parcels:
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

# ================= 2.6 FOREST =================
if len(IRREGULAR_FOREST_PTS) > 0:
    irr_forest_nodes = [create_unique_node(x, y) for (x, y) in IRREGULAR_FOREST_PTS]
    irr_forest_nodes.append(irr_forest_nodes[0])
    add_way(irr_forest_nodes, {'natural': 'wood', 'landuse': 'farmyard', 'name': 'Bosque de la Meseta'})

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

# Winding mountain road (follows the path from dem_new.png)
from scipy.interpolate import CubicSpline
import numpy as np
y_control = np.array([1152, 1552, 1952, 2352, 2752], dtype=np.float32)
x_control = np.array([1452, 2352, 1952, 3152, 3752], dtype=np.float32)
cs = CubicSpline(y_control, x_control, bc_type='clamped')

road_pts = []
# 1. North connection (straight vertical from y=512 to y=1152 at x=1452)
for y_val in np.linspace(512, 1152, 15):
    road_pts.append((1452.0, float(y_val)))

# 2. Middle winding road (spline from y=1152 to y=2752, skipping the first node because it's (1452, 1152))
for y_val in np.linspace(1152, 2752, 35)[1:]:
    x_val = float(cs(y_val))
    road_pts.append((x_val, float(y_val)))

# 3. South connection (straight vertical from y=2752 to y=3584 at x=3752, skipping first because it's (3752, 2752))
for y_val in np.linspace(2752, 3584, 15)[1:]:
    road_pts.append((3752.0, float(y_val)))

road_nodes = [get_node(x, y) for (x, y) in road_pts]
add_way(road_nodes, {'highway': 'primary', 'name': 'Camino de la Meseta'})

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
os.makedirs("outputs", exist_ok=True)
xml_str = ET.tostring(root, encoding='utf-8')
parsed = minidom.parseString(xml_str)
pretty_xml = parsed.toprettyxml(indent="  ")

cleaned_lines = [line for line in pretty_xml.split('\n') if line.strip() != ""]
cleaned_xml = '\n'.join(cleaned_lines)

output_file = "outputs/zoning_map.osm"
with open(output_file, "w", encoding="utf-8") as f:
    f.write(cleaned_xml)

print(f"OSM file successfully written to {output_file}")
print(f"Generated {len(node_coords)} nodes and {len(ways)} ways.")
