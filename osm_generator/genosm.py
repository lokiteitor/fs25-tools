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
        x0_s = 100
    elif x0 == 1024:
        x0_s = 1024 + 23
    else:
        x0_s = x0 + 16
        
    if x1 == 8192:
        x1_s = 8192 - 100
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

for i in range(MILES):
    for j in range(MILES):
        x0, y0 = m(i), m(j)
        x1, y1 = m(i+1), m(j+1)
        cx, cy = (x0+x1)/2, (y0+y1)/2
        
        is_north = (j == 0)
        if is_north:
            edge = (i == 0 or i == MILES - 1 or j == 0 or j == MILES - 1)
            split_block(x0, y0, x1, y1, 0, edge, False)
            continue
            
        if i == 1 and j == 1:
            # Divide the southern half of the town section into 4 equal-sized fields (2x2 grid)
            parcels.append((m(1.0), m(1.5), m(1.5), m(1.75)))
            parcels.append((m(1.5), m(1.5), m(2.0), m(1.75)))
            parcels.append((m(1.0), m(1.75), m(1.5), m(2.0)))
            parcels.append((m(1.5), m(1.75), m(2.0), m(2.0)))
            continue
            
        if in_town(cx, cy):
            continue

        near_town = (abs(i - 1.5) <= 1.5 and abs(j - 1.5) <= 1.5 and j > 0)
        along_canal = (i == 2 and (1 <= j <= 6)) or (j == 2 and (1 <= i <= 6))
        is_south = (j == MILES - 1)
        
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
            
        if not (near_town or along_canal):
            parcels.append((x0, y0, x1, y1))
            continue
            
        edge = (i == 0 or i == MILES - 1 or j == 0 or j == MILES - 1)
        split_block(x0, y0, x1, y1, 0, edge, near_town)

# --- Geometries with GAP adjustments ---
TOWN_X0, TOWN_X1, TOWN_Y0, TOWN_Y1 = m(1), m(2), m(1), m(2)

forests = [
    (m(5.0), m(2.0), m(6.0), m(2.5)),
    (m(2.0), m(1.0), m(2.5), m(2.0)),
    (m(5.0), m(5.5), m(6.0), m(6.0))
]

yards = [
    (m(4.375), m(1) + TH_P/2, m(4.625), m(1) + TH_P/2 + m(0.25)),
    (m(2.35), m(7) - TH_P/2 - m(0.3), m(2.65), m(7) - TH_P/2),
    (m(4.4), m(7) - TH_P/2 - m(0.2), m(4.6), m(7) - TH_P/2),
    (m(6.35), m(7) - TH_P/2 - m(0.3), m(6.65), m(7) - TH_P/2),
    (m(1) + TH_P/2, m(4.4), m(1) + TH_P/2 + m(0.2), m(4.6)),
    (m(1.625), m(1.0), m(2.0), m(1.5)),
    (m(7) - TH_P/2 - m(0.5), m(4.25), m(7) - TH_P/2, m(4.75)),
    (3850, 120, 6150, 965) # Lake enclosing farmyard (surrounds the northern lake)
]

ind_spots = [
    (m(1) - TH_P/2 - m(0.4), m(6.2), m(1) - TH_P/2, m(6.8)),
    (m(5.2), m(7.0) - TH_P/2 - m(0.4), m(5.8), m(7.0) - TH_P/2),
    (m(1) + TH_P/2, 750, m(2) - TH_T/2, 950)
]

# --- Farmland Clipping Geometry ---
clips = []
# 100m unassigned border clip
clips.append((0, 0, S, 100))
clips.append((0, S - 100, S, S))
clips.append((0, 0, 100, S))
clips.append((S - 100, 0, S, S))

clips.append((m(1.0), m(1.0), m(1.625), m(1.5))) # Top-west of town
for f in forests:
    clips.append(f)
for y in yards:
    clips.append(y)
for ind in ind_spots:
    clips.append(ind)

# Add road footprints to clips to separate farmlands from roads
for k in range(1, MILES):
    y = m(k)
    hw = TH_P/2 + W_ROAD_BORDER if (k == 1 or k == 7) else TH_T/2 + W_ROAD_BORDER
    clips.append((0, y - hw, S, y + hw))

for k in range(1, MILES):
    x = m(k)
    hw = TH_P/2 + W_ROAD_BORDER if k in [1, 7] else TH_T/2 + W_ROAD_BORDER
    # Vertical track roads (k not in [1, 7]) start at y=m(1). Primary roads start at m(1)-W_ROAD_BORDER.
    y_start = m(1) if k not in [1, 7] else m(1) - W_ROAD_BORDER
    clips.append((x - hw, y_start, x + hw, m(7) + W_ROAD_BORDER))



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

# Add parcels as ways, clipping them with other area elements first
for p in parcels:
    x0, y0, x1, y1 = p
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
    create_unique_node(m(1.0), m(1.0)),
    create_unique_node(m(1.625), m(1.0)),
    create_unique_node(m(1.625), m(1.5)),
    create_unique_node(m(1.0), m(1.5)),
]
town_nodes.append(town_nodes[0])
add_way(town_nodes, {'landuse': 'residential'})

# Town streets (Grid of 8x8 blocks, meaning 7 internal streets in each direction)
# Vertical streets
for i in range(1, 5):
    x = TOWN_X0 + i * (TOWN_X1 - TOWN_X0) / 8
    # Form street segments connected with intersections
    pts = [TOWN_Y0 + m(0.05)] + [TOWN_Y0 + j * (TOWN_Y1 - TOWN_Y0) / 8 for j in range(1, 4)] + [m(1.5)]
    ns = [get_node(x, y_val) for y_val in pts]
    add_way(ns, {'highway': 'residential'})

# Horizontal streets
for j in range(1, 4):
    y = TOWN_Y0 + j * (TOWN_Y1 - TOWN_Y0) / 8
    pts = [TOWN_X0 + m(0.05)] + [TOWN_X0 + i * (TOWN_X1 - TOWN_X0) / 8 for i in range(1, 5)] + [m(1.625)]
    ns = [get_node(x_val, y) for x_val in pts]
    add_way(ns, {'highway': 'residential'})

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

# ================= LAKE (200 hectares irregular lake in the north) =================
def generate_lake_polygon(cx, cy, target_area):
    n_points = 200
    points = []
    # Base ellipse with a:b ratio of 2.8:1 to fit horizontally in the north
    a_base = 2.8
    b_base = 1.0
    for i in range(n_points):
        theta = i * 2 * math.pi / n_points
        # Irregular noise using multiple sine/cosine waves
        r_noise = 1.0 + 0.18 * math.sin(4 * theta) + 0.08 * math.cos(7 * theta) + 0.04 * math.sin(12 * theta)
        x = a_base * r_noise * math.cos(theta)
        y = b_base * r_noise * math.sin(theta)
        points.append((x, y))
        
    # Calculate base area with Shoelace formula
    current_area = 0.0
    for i in range(n_points):
        x1, y1 = points[i]
        x2, y2 = points[(i + 1) % n_points]
        current_area += (x1 * y2 - x2 * y1)
    current_area = abs(current_area) / 2.0
    
    scale = math.sqrt(target_area / current_area)
    
    # Scale and translate to center
    final_points = []
    for (x, y) in points:
        fx = cx + x * scale
        fy = cy + y * scale
        final_points.append((fx, fy))
    return final_points

lake_pts = generate_lake_polygon(5000, 500, 800000)
lake_nodes = [create_unique_node(x, y) for (x, y) in lake_pts]
lake_nodes.append(lake_nodes[0]) # Close polygon
add_way(lake_nodes, {'natural': 'water', 'water': 'lake', 'name': 'Lago del Norte'})


# ================= RAILWAY (Horizontal railway track crossing from east to west at y=980) =================
rail_nodes = [
    create_unique_node(0, 980),
    create_unique_node(S, 980)
]
add_way(rail_nodes, {'railway': 'rail', 'name': 'Línea Ferroviaria del Norte'})

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



# Canals, reservoirs, and river removed as per request

# ================= 8. ROADS =================
# Horizontal roads
for k in range(1, MILES):
    y = m(k)
    highway_tag = 'primary' if (k == 1 or k == 7) else 'track'
    ns = [get_node(m(i), y) for i in range(MILES+1)]
    add_way(ns, {'highway': highway_tag})

# Vertical roads
for k in range(1, MILES):
    x = m(k)
    highway_tag = 'primary' if k in [1, 7] else 'track'
    ns = [get_node(x, m(j)) for j in range(1, 8)]
    add_way(ns, {'highway': highway_tag})



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
