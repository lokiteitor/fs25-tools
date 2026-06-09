import random
import math
import xml.etree.ElementTree as ET
from xml.dom import minidom
import os

# --- Configurations ---
random.seed(20240605)

S = 4096                      # canvas px
MILES = 4                     # real miles across
PPM = S / MILES               # px per mile = 1024
def m(x): return x * PPM      # helper for miles

def get_road_x(y):
    y_miles = y / PPM
    if y_miles <= 0.5:
        return m(3.0)
    elif y_miles >= 3.5:
        return m(1.0)
    else:
        u = (y_miles - 0.5) / (3.5 - 0.5)
        x_miles = 1.0 + 2.0 * (1.0 + math.cos(math.pi * u)) / 2.0
        return m(x_miles)

def crosses_diagonal_forest(x0, y0, x1, y1):
    if y1 <= m(0.5) or y0 >= m(3.5):
        return False
    y_start = max(y0, m(0.5))
    y_end = min(y1, m(3.5))
    for y in [y_start, (y_start + y_end)/2, y_end]:
        rx = get_road_x(y)
        if x0 - 350 <= rx <= x1 + 350:
            return True
    return False

TH_P = 22                     # primary
TH_S = 16                     # secondary
TH_T = 8                      # track
GAP = 40                      # Greater separation between polygons and roads
W_ROAD_BORDER = 12            # Black border/margin for roads

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
def in_town(cx, cy):
    return m(1) <= cx < m(2) and m(0.5) <= cy < m(1)

def split_block(x0, y0, x1, y1, depth, edge, near_town):
    w = x1 - x0
    h = y1 - y0
    
    maxdepth = 1
        
    if depth >= 1 and random.random() < 0.52:
        parcels.append((x0, y0, x1, y1))
        return
        
    if depth >= maxdepth or (w < m(0.15) or h < m(0.15)):
        parcels.append((x0, y0, x1, y1))
        return
        
    r = random.uniform(0.3, 0.7)
    if w >= h:
        xm = x0 + w * r
        split_block(x0, y0, xm, y1, depth + 1, edge, near_town)
        split_block(xm, y0, x1, y1, depth + 1, edge, near_town)
    else:
        ym = y0 + h * r
        split_block(x0, y0, x1, ym, depth + 1, edge, near_town)
        split_block(x0, ym, x1, y1, depth + 1, edge, near_town)

# 1. Northern strip (Row 0): [0, 512] - Medium farmlands
for i in range(MILES):
    x0, y0 = m(i), 0
    x1, y1 = m(i+1), m(0.5)
    if i == 0:
        # Sector 0: Left half = 2x1 rectangles; Right half = squares
        parcels.append((x0, y0, x0 + 512, y0 + 256))
        parcels.append((x0, y0 + 256, x0 + 512, y1))
        parcels.append((x0 + 512, y0, x0 + 768, y0 + 256))
        parcels.append((x0 + 512, y0 + 256, x0 + 768, y1))
    elif i == 1:
        # Sector 1: Left half = 2x1 rectangle + 1x1 square
        parcels.append((x0, y0, x0 + 512, y0 + 256))
        parcels.append((x0, y0 + 256, x0 + 256, y1))
        # Right half = four 256x256 squares
        parcels.append((x0 + 512, y0, x0 + 768, y0 + 256))
        parcels.append((x0 + 512, y0 + 256, x0 + 768, y1))
        parcels.append((x0 + 768, y0, x1, y0 + 256))
        parcels.append((x0 + 768, y0 + 256, x1, y1))
    elif i == 2:
        # Sector 2: Left half = 2x1 rectangle + 1x1 square
        parcels.append((x0, y0, x0 + 512, y0 + 256))
        parcels.append((x0, y0 + 256, x0 + 256, y1))
        # Right half = four 256x256 squares
        parcels.append((x0 + 512, y0, x0 + 768, y0 + 256))
        parcels.append((x0 + 512, y0 + 256, x0 + 768, y1))
        parcels.append((x0 + 768, y0, x1, y0 + 256))
        parcels.append((x0 + 768, y0 + 256, x1, y1))
    elif i == 3:
        # Sector 3: Left half = 2x1 rectangle + 1x1 square
        parcels.append((x0, y0, x0 + 512, y0 + 256))
        parcels.append((x0, y0 + 256, x0 + 256, y1))
        # Right half = four 256x256 squares
        parcels.append((x0 + 512, y0, x0 + 768, y0 + 256))
        parcels.append((x0 + 512, y0 + 256, x0 + 768, y1))
        parcels.append((x0 + 768, y0, x1, y0 + 256))
        parcels.append((x0 + 768, y0 + 256, x1, y1))

# 2. Main grid rows:
# Row 1: [512, 1024]
for i in range(MILES):
    if i == 1:
        # Town section: town itself is at [m(1.0), m(1.625)], the rest is farmland
        split_block(m(1.625), m(0.5), m(2.0), m(1.0), 0, True, True)
        continue
    x0, y0 = m(i), m(0.5)
    x1, y1 = m(i+1), m(1.0)
    if crosses_diagonal_forest(x0, y0, x1, y1):
        parcels.append((x0, y0, x1, y1))
        continue
    split_block(x0, y0, x1, y1, 0, True, True)

# Row 2: [1024, 2048]
for i in range(MILES):
    x0, y0 = m(i), m(1.0)
    x1, y1 = m(i+1), m(2.0)
    if crosses_diagonal_forest(x0, y0, x1, y1):
        if i == 3:
            continue
        parcels.append((x0, y0, x1, y1))
        continue
    split_block(x0, y0, x1, y1, 0, True, True)

# Row 3: [2048, 3072]
for i in range(MILES):
    x0, y0 = m(i), m(2.0)
    x1, y1 = m(i+1), m(3.0)
    if crosses_diagonal_forest(x0, y0, x1, y1):
        parcels.append((x0, y0, x1, y1))
        continue
    split_block(x0, y0, x1, y1, 0, True, True)

# Row 4 (Clean Area): [3072, 3584]
for i in range(MILES):
    x0, y0 = m(i), m(3.0)
    x1, y1 = m(i+1), m(3.5)
    parcels.append((x0, y0, x1, y1))

# 3. Southern strip: [3584, 4096] - Medium farmlands
for i in range(MILES):
    x0, y0 = m(i), m(3.5)
    x1, y1 = m(i+1), 4096
    if i == 0:
        # Sector 0: Left half = 1x1 square + 2x1 rectangle
        parcels.append((x0, y0, x0 + 256, y0 + 256))
        parcels.append((x0, y0 + 256, x0 + 512, y1))
        # Right half = four 256x256 squares
        parcels.append((x0 + 512, y0, x0 + 768, y0 + 256))
        parcels.append((x0 + 512, y0 + 256, x0 + 768, y1))
        parcels.append((x0 + 768, y0, x1, y0 + 256))
        parcels.append((x0 + 768, y0 + 256, x1, y1))
    elif i == 1:
        # Sector 1: Left half = 1x1 square + 2x1 rectangle
        parcels.append((x0, y0, x0 + 256, y0 + 256))
        parcels.append((x0, y0 + 256, x0 + 512, y1))
        # Right half = four 256x256 squares
        parcels.append((x0 + 512, y0, x0 + 768, y0 + 256))
        parcels.append((x0 + 512, y0 + 256, x0 + 768, y1))
        parcels.append((x0 + 768, y0, x1, y0 + 256))
        parcels.append((x0 + 768, y0 + 256, x1, y1))
    elif i == 2:
        # Sector 2: Left half = 1x1 square + 2x1 rectangle
        parcels.append((x0, y0, x0 + 256, y0 + 256))
        parcels.append((x0, y0 + 256, x0 + 512, y1))
        # Right half = four 256x256 squares
        parcels.append((x0 + 512, y0, x0 + 768, y0 + 256))
        parcels.append((x0 + 512, y0 + 256, x0 + 768, y1))
        parcels.append((x0 + 768, y0, x1, y0 + 256))
        parcels.append((x0 + 768, y0 + 256, x1, y1))
    elif i == 3:
        # Sector 3: Left half = two 1x1 squares
        parcels.append((x0 + 256, y0, x0 + 512, y0 + 256))
        parcels.append((x0 + 256, y0 + 256, x0 + 512, y1))
        # Right half = two 2x1 rectangles
        parcels.append((x0 + 512, y0, x1, y0 + 256))
        parcels.append((x0 + 512, y0 + 256, x1, y1))

# --- Geometries with GAP adjustments ---
TOWN_X0, TOWN_X1, TOWN_Y0, TOWN_Y1 = m(1), m(2), m(0.5), m(1)

forests = [
    (0, 0, S, 10),
    (0, S - 10, S, S),
    (0, 0, 10, S),
    (S - 10, 0, S, S)
]

diag_forests = []

yards = [
    # Main farmyard (Southeast)
    (3088, 3607, 3316, 4076),
    # Main farmyard (Northwest)
    (780, 24, 1008, 489),
    # Northern road industrial zones (West, Mid-West, Mid-East) in field corners
    (1292, 268, 1524, 489),
    (2316, 268, 2548, 489),
    (3340, 268, 3572, 489),
    # Southern road industrial zones (West, Mid-West, Mid-East) in field corners
    (268, 3607, 500, 3828),
    (1292, 3607, 1524, 3828),
    (2316, 3607, 2548, 3828)
]

num_forest_steps = 240
for i in range(num_forest_steps):
    y0 = m(0.5 + i * (2.5 / num_forest_steps))
    y1 = m(0.5 + (i + 1) * (2.5 / num_forest_steps))
    ym = (y0 + y1) / 2
    xc = get_road_x(ym)
    x0 = max(35.0, xc - 350.0)
    x1 = min(S - 35.0, xc + 350.0)
    diag_forests.append((x0, y0, x1, y1))

def find_intersection_y(target_x):
    low = m(0.5)
    high = m(3.5)
    for _ in range(20):
        mid = (low + high) / 2
        x = get_road_x(mid)
        if x > target_x:
            low = mid
        else:
            high = mid
    return mid

# --- Farmland Clipping Geometry ---
clips = []
# 35m unassigned border clip (includes forest from 0 to 10 and black strip from 10 to 35)
clips.append((0, 0, S, 35))
clips.append((0, S - 35, S, S))
clips.append((0, 0, 35, S))
clips.append((S - 35, 0, S, S))

clips.append((m(1.0), m(0.5), m(1.625), m(1.0))) # Town residential clip

for f in forests:
    clips.append(f)
for y in yards:
    clips.append(y)

# Set up road coordinates
hlines = [512, 1024, 2048, 3584]

# Add road footprints to clips
for y in hlines:
    hw = TH_P/2 + W_ROAD_BORDER if (y == 512 or y == 3584) else TH_T/2 + W_ROAD_BORDER
    clips.append((0, y - hw, S, y + hw))

for k in range(1, MILES):
    x = m(k)
    hw = TH_T/2 + W_ROAD_BORDER
    y_start = 0
    clips.append((x - hw, y_start, x + hw, m(3.5) + W_ROAD_BORDER))

# Add southern track footprints to clips
hw_track = TH_T/2 + W_ROAD_BORDER
clips.append((2445 - hw_track, 2048 - hw_track, 2445 + hw_track, 3584 + hw_track))


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
            
        in_forest_range = (cy0_s < m(3.5)) and (cy1_s > m(0.5))
        if not in_forest_range:
            ns = [
                create_unique_node(cx0_s, cy0_s),
                create_unique_node(cx1_s, cy0_s),
                create_unique_node(cx1_s, cy1_s),
                create_unique_node(cx0_s, cy1_s),
            ]
            ns.append(ns[0])
            add_way(ns, {'landuse': 'farmland'})
            continue
            
        # Sample every 16px along the y range to get a smooth curve
        y_vals = []
        y_curr = cy0_s
        while y_curr < cy1_s:
            y_vals.append(y_curr)
            y_curr += 16
        y_vals.append(cy1_s)
        
        has_left = False
        has_right = False
        for y_val in y_vals:
            L_y = get_road_x(y_val) - 350.0
            R_y = get_road_x(y_val) + 350.0
            if cx0_s < L_y:
                has_left = True
            if cx1_s > R_y:
                has_right = True
                
        # Generate left polygon nodes
        if has_left:
            valid_y_vals = [y for y in y_vals if get_road_x(y) - 350.0 > cx0_s]
            if len(valid_y_vals) >= 2:
                y_start = valid_y_vals[0]
                y_end = valid_y_vals[-1]
                pts = [(cx0_s, y_start), (cx0_s, y_end)]
                for y_val in reversed(valid_y_vals):
                    L_y = get_road_x(y_val) - 350.0
                    px = max(cx0_s, min(cx1_s, L_y))
                    if pts[-1] != (px, y_val):
                        pts.append((px, y_val))
                if pts[-1] != pts[0]:
                    pts.append(pts[0])
                    
                if len(pts) >= 4:
                    xs = [pt[0] for pt in pts]
                    ys = [pt[1] for pt in pts]
                    if (max(xs) - min(xs) > 10.0) and (max(ys) - min(ys) > 10.0):
                        ns = [create_unique_node(x, y) for (x, y) in pts[:-1]]
                        ns.append(ns[0])
                        add_way(ns, {'landuse': 'farmland'})
                        
        # Generate right polygon nodes
        if has_right:
            valid_y_vals = [y for y in y_vals if get_road_x(y) + 350.0 < cx1_s]
            if len(valid_y_vals) >= 2:
                y_start = valid_y_vals[0]
                y_end = valid_y_vals[-1]
                pts = [(cx1_s, y_start)]
                for y_val in valid_y_vals:
                    R_y = get_road_x(y_val) + 350.0
                    px = max(cx0_s, min(cx1_s, R_y))
                    if pts[-1] != (px, y_val):
                        pts.append((px, y_val))
                if pts[-1] != (cx1_s, y_end):
                    pts.append((cx1_s, y_end))
                if pts[-1] != pts[0]:
                    pts.append(pts[0])
                    
                if len(pts) >= 4:
                    xs = [pt[0] for pt in pts]
                    ys = [pt[1] for pt in pts]
                    if (max(xs) - min(xs) > 10.0) and (max(ys) - min(ys) > 10.0):
                        ns = [create_unique_node(x, y) for (x, y) in pts[:-1]]
                        ns.append(ns[0])
                        add_way(ns, {'landuse': 'farmland'})

# Southern zone fields removed

# ================= Column 4 Row 2 Circular Field in OSM =================
cx = 3072 + 512
cy = 1024 + 512
R = 472
pts = []
# Generate circle approximation (32 nodes)
for k in range(32):
    theta = k * 2 * math.pi / 32
    x = cx + R * math.cos(theta)
    y = cy + R * math.sin(theta)
    pts.append((x, y))
ns = [create_unique_node(x, y) for (x, y) in pts]
ns.append(ns[0])
add_way(ns, {'landuse': 'farmland'})

# ================= 2. TOWN =================

town_nodes = [
    create_unique_node(m(1.0), m(0.5)),
    create_unique_node(m(1.625), m(0.5)),
    create_unique_node(m(1.625), m(1.0)),
    create_unique_node(m(1.0), m(1.0)),
]
town_nodes.append(town_nodes[0])
add_way(town_nodes, {'landuse': 'residential'})

# Town streets
for i in range(1, 7):
    x = TOWN_X0 + i * 100
    pts = [TOWN_Y0 + 10] + [TOWN_Y0 + j * 100 for j in range(1, 5)] + [m(1.0)]
    ns = [get_node(x, y_val) for y_val in pts]
    add_way(ns, {'highway': 'secondary'})

for j in range(1, 5):
    y = TOWN_Y0 + j * 100
    pts = [TOWN_X0 + 10] + [TOWN_X0 + i * 100 for i in range(1, 7)] + [m(1.625)]
    ns = [get_node(x_val, y) for x_val in pts]
    add_way(ns, {'highway': 'secondary'})

# ================= 3. FORESTS =================

for (x0, y0, x1, y1) in forests:
    ns = [
        create_unique_node(x0, y0),
        create_unique_node(x1, y0),
        create_unique_node(x1, y1),
        create_unique_node(x0, y1),
    ]
    ns.append(ns[0])
    add_way(ns, {'landuse': 'forest'})

# Single curved forest polygon for OSM
forest_nodes = []
# Right side: from top to bottom (y = m(0.5) to m(3.5))
for y_px in range(int(m(0.5)), int(m(3.5)) + 1, 32):
    xc = get_road_x(y_px)
    xr = min(S - 35.0, xc + 318.0)
    forest_nodes.append(create_unique_node(xr, y_px))

# Left side: from bottom to top (y = m(3.5) to m(0.5))
for y_px in range(int(m(3.5)), int(m(0.5)) - 1, -32):
    xc = get_road_x(y_px)
    xl = max(35.0, xc - 318.0)
    forest_nodes.append(create_unique_node(xl, y_px))

forest_nodes.append(forest_nodes[0])
add_way(forest_nodes, {'natural': 'wood', 'name': 'Bosque de la Diagonal'})

# ================= 4. FARMYARDS =================

for (x0, y0, x1, y1) in yards:
    ns = [
        create_unique_node(x0, y0),
        create_unique_node(x1, y0),
        create_unique_node(x1, y1),
        create_unique_node(x0, y1),
    ]
    ns.append(ns[0])
    add_way(ns, {'landuse': 'farmyard', 'building': 'industrial'})

# ================= 8. ROADS =================
# Horizontal roads
for y in hlines:
    highway_tag = 'primary' if (y == 512 or y == 3584) else 'track'
    coords = [m(i) for i in range(MILES+1)]
    x_int = get_road_x(y)
    coords.append(x_int)
    coords = sorted(list(set(coords)))
    ns = [get_node(x, y) for x in coords]
    add_way(ns, {'highway': highway_tag})

# Vertical roads
for k in range(1, MILES):
    x = m(k)
    highway_tag = 'track'
    y_coords = [0, 512, 1024, 2048, 3584]
    y_int = find_intersection_y(x)
    y_coords.append(y_int)
    y_coords = sorted(list(set(y_coords)))
    ns = [get_node(x, y) for y in y_coords]
    add_way(ns, {'highway': highway_tag})

# Diagonal primary road
diag_pts = []
for k in range(25):
    y_val = m(0.5) + k * 122.88 # 3.0 miles = 3072px range, divided by 25 = 122.88px per step
    x_val = get_road_x(y_val)
    diag_pts.append((x_val, y_val))

for x_val in [1024, 2048, 3072]:
    y_val = find_intersection_y(x_val)
    diag_pts.append((x_val, y_val))

diag_pts = sorted(list(set(diag_pts)), key=lambda p: p[1])
diag_nodes = [get_node(x, y) for (x, y) in diag_pts]
add_way(diag_nodes, {'highway': 'primary'})

# Southern track roads
south_vertical_track = [
    get_node(2445, 2048),
    get_node(2445, 3584)
]
add_way(south_vertical_track, {'highway': 'track', 'name': 'Camino de Terracería del Sur'})


# ================= 9. BUILD OSM XML =================
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
