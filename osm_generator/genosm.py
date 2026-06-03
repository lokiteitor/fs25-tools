import random
import math
import xml.etree.ElementTree as ET
from xml.dom import minidom
import os

# --- Configurations ---
random.seed(20240605)

S = 8192                      # canvas px
MILES = 8                     # real miles across
PPM = S / MILES               # px per mile = 1024
def m(x): return x * PPM      # helper for miles

def get_forest_top(x):
    y_c = m(0.35) + (m(0.1) * (x / S)) + 90 * math.sin(x * 2 * math.pi / 3200) + 25 * math.sin(x * 2 * math.pi / 900)
    w = 180 + 30 * math.sin(x * 2 * math.pi / 1000)
    return y_c - w/2

def get_forest_bottom(x):
    y_c = m(0.35) + (m(0.1) * (x / S)) + 90 * math.sin(x * 2 * math.pi / 3200) + 25 * math.sin(x * 2 * math.pi / 900)
    w = 180 + 30 * math.sin(x * 2 * math.pi / 1000)
    return y_c + w/2

def get_shrunk_x(x0, x1):
    if x0 == 0:
        x0_s = 20
    elif x0 == 1024:
        x0_s = 1024 + 23
    else:
        x0_s = x0 + 16
        
    if x1 == 8192:
        x1_s = 8192 - 20
    elif x1 == 1024:
        x1_s = 1024 - 23
    else:
        x1_s = x1 - 16
        
    return x0_s, x1_s

TH_P = 22                     # primary
TH_S = 16                     # secondary
TH_T = 8                      # track
GAP = 40                      # Greater separation between polygons and roads
W_ROAD_BORDER = 12            # Black border/margin for roads
W_CANAL_BORDER = 12           # Black border/margin for canals
CW = 26                       # Canal width
off = TH_T/2 + CW/2 + GAP


# --- Georeferencing ---
# Center: (27.07991, -109.70707)
min_lon = -109.748441630125
min_lat = 27.043073839058213
max_lon = -109.665698369875
max_lat = 27.11674616094179

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
    # Key by coordinate rounded to 2 decimal places in pixel space to ensure topological connection
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
    return m(1) <= cx < m(2) and m(1) <= cy < m(2)

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

def split_north_block(x0, y0, x1, y1, depth=0):
    w = x1 - x0
    h = y1 - y0
    if depth >= 1 or (w < m(0.15) or h < m(0.15)):
        parcels.append((x0, y0, x1, y1))
        return
        
    r = random.uniform(0.38, 0.62)
    if w >= h:
        xm = x0 + w * r
        split_north_block(x0, y0, xm, y1, depth + 1)
        split_north_block(xm, y0, x1, y1, depth + 1)
    else:
        ym = y0 + h * r
        split_north_block(x0, y0, x1, ym, depth + 1)
        split_north_block(x0, ym, x1, y1, depth + 1)

for i in range(MILES):
    for j in range(MILES):
        x0, y0 = m(i), m(j)
        x1, y1 = m(i+1), m(j+1)
        cx, cy = (x0+x1)/2, (y0+y1)/2
        
        if in_town(cx, cy):
            continue
            
        is_north = (j == 0)
        if is_north:
            split_north_block(x0, y0, x1, y1)
            continue

        near_town = (abs(i - 1.5) <= 1.5 and abs(j - 1.5) <= 1.5 and j > 0)
        along_canal = (i == 2 and (1 <= j <= 6)) or (j == 2 and (1 <= i <= 6))
        is_south = (j == MILES - 1)
        is_greenhouse_sector = (i == 3 and j == 6)
        
        if is_south:
            x_mid = x0 + 512
            # Generate 2 regular horizontal strips above the canal, split in half
            for k in range(2):
                y_start = m(7) + k * 256
                y_end = y_start + 256
                parcels.append((x0, y_start, x_mid, y_end))
                parcels.append((x_mid, y_start, x1, y_end))
            # Generate 2 regular horizontal strips below the canal, split in half
            for k in range(2):
                y_start = m(7.5) + k * 256
                y_end = y_start + 256
                parcels.append((x0, y_start, x_mid, y_end))
                parcels.append((x_mid, y_start, x1, y_end))
            continue
            
        if not (near_town or along_canal or is_greenhouse_sector):
            parcels.append((x0, y0, x1, y1))
            continue
            
        edge = (i == 0 or i == MILES - 1 or j == 0 or j == MILES - 1)
        split_block(x0, y0, x1, y1, 0, edge, near_town)

# --- Geometries with GAP adjustments ---
TOWN_X0, TOWN_X1, TOWN_Y0, TOWN_Y1 = m(1), m(2), m(1), m(2)

# Northern Reservoir & Forest (centered in grid cell [2, 3] x [1, 2], expanded to touch vertical canal at x=3015)
RX0, RY0 = m(2.1), m(1.2)
RX1, RY1 = m(3.0) - off, m(1.8)

FNX0, FNY0 = m(2.0) + TH_T/2 + W_ROAD_BORDER, m(1.0) + TH_P/2 + W_ROAD_BORDER
FNX1, FNY1 = m(3.0) - TH_T/2 - W_ROAD_BORDER, m(2.0) - TH_T/2 - W_ROAD_BORDER

# South Reservoir & Forest (centered in grid cell [0, 1] x [7, 8], expanded to connect to south canal)
SRX0, SRY0 = m(0.15), m(7.2)
SRX1, SRY1 = m(0.85), m(7.8)

FSX0, FSY0 = 0, m(7.0) + TH_P/2 + W_ROAD_BORDER
FSX1, FSY1 = m(1.0) - TH_P/2 - W_ROAD_BORDER, m(8.0)

forests = [
    (m(5.0), m(2.0), m(6.0), m(2.5)),
    (m(2.0), m(5.0), m(2.5), m(6.0)),
    (m(5.0), m(5.5), m(6.0), m(6.0)),
    (FNX0, FNY0, FNX1, FNY1),
    (FSX0, FSY0, FSX1, FSY1)
]

yards = [
    (m(4.375), m(1) + TH_P/2, m(4.625), m(1) + TH_P/2 + m(0.25)),
    (m(2.35), m(7) - TH_P/2 - m(0.3), m(2.65), m(7) - TH_P/2),
    (m(4.4), m(7) - TH_P/2 - m(0.2), m(4.6), m(7) - TH_P/2),
    (m(6.35), m(7) - TH_P/2 - m(0.3), m(6.65), m(7) - TH_P/2),
    (m(1) + TH_P/2, m(4.4), m(1) + TH_P/2 + m(0.2), m(4.6))
]

ind_spots = [
    (m(1) - TH_P/2 - m(0.4), m(6.2), m(1) - TH_P/2, m(6.8)),
    (m(5.2), m(7.0) - TH_P/2 - m(0.4), m(5.8), m(7.0) - TH_P/2)
]

gh_x0, gh_y0 = m(3.2), m(7.0) - TH_P/2 - m(0.7)
gh_x1, gh_y1 = m(3.8), m(7.0) - TH_P/2 - m(0.3)

# --- Farmland Clipping Geometry ---
clips = []
W_BORDER_FOREST = 20
clips.append((0, 0, S, W_BORDER_FOREST)) # Top border forest
clips.append((0, S - W_BORDER_FOREST, S, S)) # Bottom border forest

# Left border forest segments
left_segments = [
    (0, 340), (376, 1001), (1047, 2032), (2064, 3056), (3088, 4080),
    (4112, 5104), (5136, 6128), (6160, 7145), (7191, 8192)
]
for y0, y1 in left_segments:
    clips.append((0, y0, W_BORDER_FOREST, y1))

# Right border forest segments
right_segments = [
    (0, 491), (526, 1001), (1047, 2032), (2064, 3056), (3088, 4080),
    (4112, 5104), (5136, 6128), (6160, 7145), (7191, 7655), (7705, 8192)
]
for y0, y1 in right_segments:
    clips.append((S - W_BORDER_FOREST, y0, S, y1))

clips.append((TOWN_X0, TOWN_Y0, TOWN_X1, TOWN_Y1))
for f in forests:
    clips.append(f)
for y in yards:
    clips.append(y)
for ind in ind_spots:
    clips.append(ind)
clips.append((gh_x0, gh_y0, gh_x1, gh_y1))
clips.append((RX0, RY0, RX1, RY1))
clips.append((SRX0, SRY0, SRX1, SRY1))

# Add road footprints to clips to separate farmlands from roads
for k in range(1, MILES):
    y = m(k)
    hw = TH_P/2 + W_ROAD_BORDER if (k == 1 or k == 7) else TH_T/2 + W_ROAD_BORDER
    clips.append((0, y - hw, S, y + hw))

for k in range(1, MILES):
    x = m(k)
    hw = TH_P/2 + W_ROAD_BORDER if k == 1 else TH_T/2 + W_ROAD_BORDER
    # Vertical track roads (k != 1) start at y=20. Primary road (k==1) starts at m(1)-W_ROAD_BORDER.
    y_start = 20 if k != 1 else m(1) - W_ROAD_BORDER
    clips.append((x - hw, y_start, x + hw, m(7) + W_ROAD_BORDER))

# Connecting road footprint
clips.append((m(3.5) - (TH_T/2 + W_ROAD_BORDER), gh_y1 - W_ROAD_BORDER, m(3.5) + (TH_T/2 + W_ROAD_BORDER), m(7.0) - TH_P/2 + W_ROAD_BORDER))

# Add canal footprints to clips
vcanal_x = m(3) - off
clips.append((vcanal_x - CW/2 - W_CANAL_BORDER, m(1.2) - W_CANAL_BORDER, vcanal_x + CW/2 + W_CANAL_BORDER, m(7.5) + W_CANAL_BORDER))

hcanal_y = m(3) + off
clips.append((m(1) + TH_P/2 + GAP - W_CANAL_BORDER, hcanal_y - CW/2 - W_CANAL_BORDER, m(7) - TH_P/2 - GAP + W_CANAL_BORDER, hcanal_y + CW/2 + W_CANAL_BORDER))

clips.append((m(0.85) - W_CANAL_BORDER, m(7.5) - CW/2 - W_CANAL_BORDER, m(8.0), m(7.5) + CW/2 + W_CANAL_BORDER))

# Add gallery forest footprint as a single horizontal band to prevent fragmentation
clips.append((0, 180, S, 550))

# Add connecting channel footprint to clips (from y=550 to the main reservoir at 1228.8)
chan_x = 2550
chan_y0 = 550
chan_y1 = 1228.8
clips.append((chan_x - CW/2 - W_CANAL_BORDER, chan_y0, chan_x + CW/2 + W_CANAL_BORDER, chan_y1))

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
        
    # Return only sub-rectangles with positive area (avoiding 1px/0px slivers from rounding)
    return [p for p in parts if (p[2] - p[0] > 1.0 and p[3] - p[1] > 1.0)]

def subtract_rects(subject, clip_list):
    current_rects = [subject]
    for clip in clip_list:
        next_rects = []
        for r in current_rects:
            next_rects.extend(subtract_single(r, clip))
        current_rects = next_rects
    return current_rects

def add_northern_winding_ways(x0, x1):
    x0_s, x1_s = get_shrunk_x(x0, x1)
    
    # 1. Top Field Polygon
    top_poly_pts = [(x0_s, 20), (x1_s, 20), (x1_s, get_forest_top(x1_s))]
    for x_val in range(int(x1_s), int(x0_s) - 1, -16):
        top_poly_pts.append((x_val, get_forest_top(x_val)))
    top_poly_pts.append((x0_s, get_forest_top(x0_s)))
    
    ns_top = [create_unique_node(pt[0], pt[1]) for pt in top_poly_pts]
    ns_top.append(ns_top[0])
    add_way(ns_top, {'landuse': 'farmland'})
    
    # 2. Bottom Field Polygon(s)
    if x0_s < 2525 and x1_s > 2575:
        # Left Bottom
        left_poly_pts = [(x0_s, get_forest_bottom(x0_s))]
        for x_val in range(int(x0_s), 2526, 16):
            left_poly_pts.append((x_val, get_forest_bottom(x_val)))
        left_poly_pts.extend([(2525, 1001), (x0_s, 1001)])
        
        ns_left = [create_unique_node(pt[0], pt[1]) for pt in left_poly_pts]
        ns_left.append(ns_left[0])
        add_way(ns_left, {'landuse': 'farmland'})
        
        # Right Bottom
        right_poly_pts = [(2575, get_forest_bottom(2575))]
        for x_val in range(2575, int(x1_s) + 1, 16):
            right_poly_pts.append((x_val, get_forest_bottom(x_val)))
        right_poly_pts.extend([(x1_s, 1001), (2575, 1001)])
        
        ns_right = [create_unique_node(pt[0], pt[1]) for pt in right_poly_pts]
        ns_right.append(ns_right[0])
        add_way(ns_right, {'landuse': 'farmland'})
    else:
        bot_poly_pts = [(x0_s, get_forest_bottom(x0_s))]
        for x_val in range(int(x0_s), int(x1_s) + 1, 16):
            bot_poly_pts.append((x_val, get_forest_bottom(x_val)))
        bot_poly_pts.extend([(x1_s, 1001), (x0_s, 1001)])
        
        ns_bot = [create_unique_node(pt[0], pt[1]) for pt in bot_poly_pts]
        ns_bot.append(ns_bot[0])
        add_way(ns_bot, {'landuse': 'farmland'})

# Add parcels as ways, clipping them with other area elements first
for p in parcels:
    x0, y0, x1, y1 = p
    if y0 < m(1):
        add_northern_winding_ways(x0, x1)
    else:
        clipped_parts = subtract_rects(p, clips)
        for (cx0, cy0, cx1, cy1) in clipped_parts:
            # Shrink by 6 pixels on each side to create a margin and avoid node sharing
            margin = 6
            cx0_s = cx0 + margin
            cx1_s = cx1 - margin
            cy0_s = cy0 + margin
            cy1_s = cy1 - margin
            
            # Avoid invalid geometries for tiny slivers
            if cx1_s - cx0_s <= 2.0 or cy1_s - cy0_s <= 2.0:
                continue
                
            ns = [
                create_unique_node(cx0_s, cy0_s),
                create_unique_node(cx1_s, cy0_s),
                create_unique_node(cx1_s, cy1_s),
                create_unique_node(cx0_s, cy1_s),
            ]
            ns.append(ns[0])  # Close polygon
            if cy0 >= m(7):
                add_way(ns, {'landuse': 'farmland', 'crop': 'rice'})
            else:
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

# Town streets (Grid of 8x8 blocks, meaning 7 internal streets in each direction)
# Vertical streets
for i in range(1, 8):
    x = TOWN_X0 + i * (TOWN_X1 - TOWN_X0) / 8
    # Form street segments connected with intersections
    pts = [TOWN_Y0 + m(0.05)] + [TOWN_Y0 + j * (TOWN_Y1 - TOWN_Y0) / 8 for j in range(1, 8)] + [TOWN_Y1 - m(0.05)]
    ns = [get_node(x, y_val) for y_val in pts]
    add_way(ns, {'highway': 'residential'})

# Horizontal streets
for j in range(1, 8):
    y = TOWN_Y0 + j * (TOWN_Y1 - TOWN_Y0) / 8
    pts = [TOWN_X0 + m(0.05)] + [TOWN_X0 + i * (TOWN_X1 - TOWN_X0) / 8 for i in range(1, 8)] + [TOWN_X1 - m(0.05)]
    ns = [get_node(x_val, y) for x_val in pts]
    add_way(ns, {'highway': 'residential'})

# ================= 3. FORESTS =================

for (x0, y0, x1, y1) in forests:
    res_clips = [(RX0, RY0, RX1, RY1), (SRX0, SRY0, SRX1, SRY1)]
    clipped_forests = subtract_rects((x0, y0, x1, y1), res_clips)
    for (fx0, fy0, fx1, fy1) in clipped_forests:
        ns = [
            create_unique_node(fx0, fy0),
            create_unique_node(fx1, fy0),
            create_unique_node(fx1, fy1),
            create_unique_node(fx0, fy1),
        ]
        ns.append(ns[0])
        add_way(ns, {'landuse': 'forest'})

# Gallery Forest surrounding the northern river (landuse=forest)
gallery_forest_nodes = []
steps_f = 256
points_left_f = []
points_right_f = []
for i in range(steps_f + 1):
    x = i * (S / steps_f)
    y_c = m(0.35) + (m(0.1) * (x / S)) + 90 * math.sin(x * 2 * math.pi / 3200) + 25 * math.sin(x * 2 * math.pi / 900)
    w = 180 + 30 * math.sin(x * 2 * math.pi / 1000)
    
    eps = 1.0
    x_prev = max(0, x - eps)
    x_next = min(S, x + eps)
    y_prev = m(0.35) + (m(0.1) * (x_prev / S)) + 90 * math.sin(x_prev * 2 * math.pi / 3200) + 25 * math.sin(x_prev * 2 * math.pi / 900)
    y_next = m(0.35) + (m(0.1) * (x_next / S)) + 90 * math.sin(x_next * 2 * math.pi / 3200) + 25 * math.sin(x_next * 2 * math.pi / 900)
    
    dx_val = x_next - x_prev
    dy_val = y_next - y_prev
    length = math.sqrt(dx_val**2 + dy_val**2)
    nx = -dy_val / length
    ny = dx_val / length
    
    lx = x + nx * (w / 2)
    ly = y_c + ny * (w / 2)
    rx = x - nx * (w / 2)
    ry = y_c - ny * (w / 2)
    
    points_left_f.append((lx, ly))
    points_right_f.append((rx, ry))

for pt in points_left_f:
    gallery_forest_nodes.append(create_unique_node(pt[0], pt[1]))
for pt in reversed(points_right_f):
    gallery_forest_nodes.append(create_unique_node(pt[0], pt[1]))
gallery_forest_nodes.append(gallery_forest_nodes[0]) # Close loop

add_way(gallery_forest_nodes, {'landuse': 'forest', 'name': 'Bosque del Río'})

# Border forests (all around the edge of the map, width W_BORDER_FOREST px, with gaps for roads/waterways)
border_forests = []
# Top and bottom borders (unbroken)
border_forests.append((0, 0, S, W_BORDER_FOREST))
border_forests.append((0, S - W_BORDER_FOREST, S, S))

# Left border segments (gaps for river and roads)
left_segments = [
    (0, 340), (376, 1001), (1047, 2032), (2064, 3056), (3088, 4080),
    (4112, 5104), (5136, 6128), (6160, 7145), (7191, 8192)
]
for y0, y1 in left_segments:
    border_forests.append((0, y0, W_BORDER_FOREST, y1))

# Right border segments (gaps for river, roads, and south canal)
right_segments = [
    (0, 491), (526, 1001), (1047, 2032), (2064, 3056), (3088, 4080),
    (4112, 5104), (5136, 6128), (6160, 7145), (7191, 7655), (7705, 8192)
]
for y0, y1 in right_segments:
    border_forests.append((S - W_BORDER_FOREST, y0, S, y1))

for (x0, y0, x1, y1) in border_forests:
    ns = [
        create_unique_node(x0, y0),
        create_unique_node(x1, y0),
        create_unique_node(x1, y1),
        create_unique_node(x0, y1),
    ]
    ns.append(ns[0])
    add_way(ns, {'landuse': 'forest', 'name': 'Cortina Forestal Perimetral'})

# ================= 4. FARMYARDS =================

for (x0, y0, x1, y1) in yards:
    ns = [
        create_unique_node(x0, y0),
        create_unique_node(x1, y0),
        create_unique_node(x1, y1),
        create_unique_node(x0, y1),
    ]
    ns.append(ns[0])
    add_way(ns, {'landuse': 'farmyard'})

# ================= 5. INDUSTRIAL SPOTS =================

for (x0, y0, x1, y1) in ind_spots:
    ns = [
        create_unique_node(x0, y0),
        create_unique_node(x1, y0),
        create_unique_node(x1, y1),
        create_unique_node(x0, y1),
    ]
    ns.append(ns[0])
    add_way(ns, {'landuse': 'industrial'})
    
    # Internal street networks for industrial spots
    w = x1 - x0
    h = y1 - y0
    cols = int(round(w / m(0.1)))
    rows = int(round(h / m(0.1)))
    
    # Vertical internal streets
    for i in range(1, cols):
        cx = x0 + i * w / cols
        pts = [y0 + m(0.02)] + [y0 + j * h / rows for j in range(1, rows)] + [y1 - m(0.02)]
        ns_st = [get_node(cx, y_val) for y_val in pts]
        add_way(ns_st, {'highway': 'service'})
        
    # Horizontal internal streets
    for j in range(1, rows):
        cy = y0 + j * h / rows
        pts = [x0 + m(0.02)] + [x0 + i * w / cols for i in range(1, cols)] + [x1 - m(0.02)]
        ns_st = [get_node(x_val, cy) for x_val in pts]
        add_way(ns_st, {'highway': 'service'})

# ================= 6. GREENHOUSE FARMYARD =================

gh_nodes = [
    create_unique_node(gh_x0, gh_y0),
    create_unique_node(gh_x1, gh_y0),
    create_unique_node(gh_x1, gh_y1),
    create_unique_node(gh_x0, gh_y1),
]
gh_nodes.append(gh_nodes[0])
add_way(gh_nodes, {'landuse': 'farmyard'})

# 4 glassy greenhouses
for i in range(4):
    gy0 = gh_y0 + m(0.06) + i * m(0.08)
    gy1 = gy0 + m(0.04)
    gx0 = gh_x0 + m(0.08)
    gx1 = gh_x1 - m(0.08)
    ns = [
        create_unique_node(gx0, gy0),
        create_unique_node(gx1, gy0),
        create_unique_node(gx1, gy1),
        create_unique_node(gx0, gy1),
    ]
    ns.append(ns[0])
    add_way(ns, {'building': 'greenhouse'})

# ================= 7. WATER =================
# Reservoirs

# Main Reservoir (with channel connection node at x=2550, y=RY0)
res_nodes = [
    create_unique_node(RX0, RY0),
    get_node(2550, RY0),  # Shared node with connecting channel!
    create_unique_node(RX1, RY0),
    create_unique_node(RX1, RY1),
    create_unique_node(RX0, RY1),
]
res_nodes.append(res_nodes[0])
add_way(res_nodes, {'natural': 'water', 'water': 'reservoir'})

# South Reservoir for rice fields
s_res_nodes = [
    create_unique_node(SRX0, SRY0),
    create_unique_node(SRX1, SRY0),
    create_unique_node(SRX1, SRY1),
    create_unique_node(SRX0, SRY1),
]
s_res_nodes.append(s_res_nodes[0])
add_way(s_res_nodes, {'natural': 'water', 'water': 'reservoir'})

# Small Control Reservoir (Embalse de Control)
small_res_poly = [
    (2550, 180), (2610, 210), (2650, 278), (2610, 340), (2550, 370),
    (2490, 340), (2450, 278), (2490, 210)
]
small_res_nodes = [get_node(pt[0], pt[1]) for pt in small_res_poly]
small_res_nodes.append(small_res_nodes[0])
add_way(small_res_nodes, {
    'natural': 'water',
    'water': 'reservoir',
    'name': 'Embalse de Control'
})

# Connecting channel (Canal Alimentador) from small reservoir to main reservoir
channel_nodes = [
    get_node(2550, 370),  # Shared with small reservoir
    get_node(2550, RY0)   # Shared with main reservoir (RY0 = 1228.8)
]
add_way(channel_nodes, {
    'waterway': 'canal',
    'name': 'Canal Alimentador del Norte'
})

# Canals (waterway=canal)
CW = 26
off = TH_T/2 + CW/2 + GAP
# Vertical canal along x=3 (west of the road, side=-1)
vcanal_nodes = [
    get_node(m(3) - off, m(1.2)),
    get_node(m(3) - off, m(7.5))
]
add_way(vcanal_nodes, {'waterway': 'canal'})

# Horizontal canal along y=3 (south of the road, side=+1)
hcanal_nodes = [
    get_node(m(1) + TH_P/2 + GAP, m(3) + off),
    get_node(m(7) - TH_P/2 - GAP, m(3) + off)
]
add_way(hcanal_nodes, {'waterway': 'canal'})

# South canal along y=7.5 (no offset, side=0)
south_canal_nodes = [
    get_node(m(0.85), m(7.5)),
    get_node(m(8.0), m(7.5))
]
add_way(south_canal_nodes, {'waterway': 'canal'})

# ================= RIVER =================
# River centerline (waterway=river) running along the curve
river_center_nodes = []
steps_center = 256
for i in range(steps_center + 1):
    x = i * (S / steps_center)
    y_c = m(0.35) + (m(0.1) * (x / S)) + 90 * math.sin(x * 2 * math.pi / 3200) + 25 * math.sin(x * 2 * math.pi / 900)
    river_center_nodes.append(create_unique_node(x, y_c))
add_way(river_center_nodes, {
    'waterway': 'river',
    'name': 'Río del Norte',
    'flow_rate': '25',
    'flow_rate:min': '20',
    'flow_rate:max': '30',
    'description': 'River with simulated flow rate of 20-30 m3/s'
})

# River banks polygon (natural=water, water=river)
river_poly_nodes = []
points_left = []
points_right = []
for i in range(steps_center + 1):
    x = i * (S / steps_center)
    y_c = m(0.35) + (m(0.1) * (x / S)) + 90 * math.sin(x * 2 * math.pi / 3200) + 25 * math.sin(x * 2 * math.pi / 900)
    w = 32 + 6 * math.sin(x * 2 * math.pi / 1500)
    
    eps = 1.0
    x_prev = max(0, x - eps)
    x_next = min(S, x + eps)
    y_prev = m(0.35) + (m(0.1) * (x_prev / S)) + 90 * math.sin(x_prev * 2 * math.pi / 3200) + 25 * math.sin(x_prev * 2 * math.pi / 900)
    y_next = m(0.35) + (m(0.1) * (x_next / S)) + 90 * math.sin(x_next * 2 * math.pi / 3200) + 25 * math.sin(x_next * 2 * math.pi / 900)
    
    dx_val = x_next - x_prev
    dy_val = y_next - y_prev
    length = math.sqrt(dx_val**2 + dy_val**2)
    nx = -dy_val / length
    ny = dx_val / length
    
    lx = x + nx * (w / 2)
    ly = y_c + ny * (w / 2)
    rx = x - nx * (w / 2)
    ry = y_c - ny * (w / 2)
    
    points_left.append((lx, ly))
    points_right.append((rx, ry))

for pt in points_left:
    river_poly_nodes.append(create_unique_node(pt[0], pt[1]))
for pt in reversed(points_right):
    river_poly_nodes.append(create_unique_node(pt[0], pt[1]))
river_poly_nodes.append(river_poly_nodes[0]) # Close the loop

add_way(river_poly_nodes, {
    'natural': 'water',
    'water': 'river',
    'name': 'Río del Norte'
})

# ================= 8. ROADS =================
# Horizontal roads
for k in range(1, MILES):
    y = m(k)
    highway_tag = 'primary' if (k == 1 or k == 7) else 'track'
    if k in [2, 3, 4, 5, 6, 7]:
        # Cut by vertical canal at x_canal = 3015. Gap is [2990, 3040]
        ns1 = [get_node(m(i), y) for i in range(3)] + [get_node(2990, y)]
        if k == 7:
            ns2 = [get_node(3040, y), get_node(m(3), y), get_node(m(3.5), y)] + [get_node(m(i), y) for i in range(4, MILES+1)]
        else:
            ns2 = [get_node(3040, y)] + [get_node(m(i), y) for i in range(3, MILES+1)]
        add_way(ns1, {'highway': highway_tag})
        add_way(ns2, {'highway': highway_tag})
    else:
        ns = [get_node(m(i), y) for i in range(MILES+1)]
        add_way(ns, {'highway': highway_tag})

# Vertical roads
for k in range(1, MILES):
    x = m(k)
    highway_tag = 'primary' if k == 1 else 'track'
    if k in [2, 3, 4, 5, 6]:
        # Cut by horizontal canal at y = 3129. Gap is [3104, 3154]
        start_nodes = [get_node(x, 20)] if highway_tag == 'track' else []
        ns1 = start_nodes + [get_node(x, m(j)) for j in range(1, 4)] + [get_node(x, 3104)]
        ns2 = [get_node(x, 3154)] + [get_node(x, m(j)) for j in range(4, 8)]
        add_way(ns1, {'highway': highway_tag})
        add_way(ns2, {'highway': highway_tag})
    else:
        start_nodes = [get_node(x, 20)] if highway_tag == 'track' else []
        ns = start_nodes + [get_node(x, m(j)) for j in range(1, 8)]
        add_way(ns, {'highway': highway_tag})

# Connecting track road to greenhouse yard
greenhouse_conn = [
    get_node(m(3.5), gh_y1),
    get_node(m(3.5), m(7.0) - TH_P/2)
]
add_way(greenhouse_conn, {'highway': 'track'})

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
# Sort keys to make the XML deterministic
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

# Remove blank lines introduced by toprettyxml inside elements if any
cleaned_lines = [line for line in pretty_xml.split('\n') if line.strip() != ""]
cleaned_xml = '\n'.join(cleaned_lines)

output_file = "outputs/zoning_map.osm"
with open(output_file, "w", encoding="utf-8") as f:
    f.write(cleaned_xml)

print(f"OSM file successfully written to {output_file}")
print(f"Generated {len(node_coords)} nodes and {len(ways)} ways.")
