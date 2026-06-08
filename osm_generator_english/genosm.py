import random
import math
import xml.etree.ElementTree as ET
from xml.dom import minidom
import os

random.seed(20240605)

S = 4096                      # canvas px
MILES = 4                     # real miles across
PPM = S / MILES               # px per mile = 1024
def m(x): return x * PPM      # helper for miles

# ---- configuration for road widths, borders and gaps ----
TH_P = 22                     # primary road thickness
TH_S = 16                     # secondary road thickness
TH_T = 8                      # track road thickness
W_FIELD_BORDER = 12           # Thicker black lines for fields
GAP = 40                      # Greater separation between polygons and roads
W_ROAD_BORDER = 12            # Black border/margin for roads

# --- Georeferencing ---
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

# ================= HELPER GEOMETRY FUNCTIONS =================

def interpolate(p1, p2, t):
    return (p1[0] * (1 - t) + p2[0] * t, p1[1] * (1 - t) + p2[1] * t)

def get_centroid(pts):
    unique = pts[:-1] if (len(pts) > 2 and pts[0] == pts[-1]) else pts
    xs = [p[0] for p in unique]
    ys = [p[1] for p in unique]
    return (sum(xs) / len(xs), sum(ys) / len(xs))

def shrink_poly(pts, margin):
    unique = list(pts)
    is_closed = False
    if len(pts) > 2 and pts[0] == pts[-1]:
        is_closed = True
        unique = pts[:-1]
        
    cx, cy = get_centroid(unique)
    
    shrunken = []
    for p in unique:
        dx = cx - p[0]
        dy = cy - p[1]
        dist = math.sqrt(dx*dx + dy*dy)
        if dist > margin:
            shrunken.append((p[0] + (dx / dist) * margin, p[1] + (dy / dist) * margin))
        else:
            shrunken.append((cx, cy))
            
    if is_closed and shrunken:
        shrunken.append(shrunken[0])
    return shrunken

def split_quad(quad, depth, max_depth=1):
    if depth >= max_depth:
        return [quad]
    
    if depth > 0 and random.random() < 0.25:
        return [quad]
        
    p0, p1, p2, p3 = quad
    w = math.sqrt((p1[0]-p0[0])**2 + (p1[1]-p0[1])**2)
    h = math.sqrt((p3[0]-p0[0])**2 + (p3[1]-p0[1])**2)
    
    t1 = random.uniform(0.35, 0.65)
    t2 = random.uniform(0.35, 0.65)
    
    if w >= h:
        # Vertical split
        a = interpolate(p0, p1, t1)
        b = interpolate(p3, p2, t2)
        q1 = [p0, a, b, p3]
        q2 = [a, p1, p2, b]
    else:
        # Horizontal split
        a = interpolate(p0, p3, t1)
        b = interpolate(p1, p2, t2)
        q1 = [p0, p1, b, a]
        q2 = [a, b, p2, p3]
        
    return split_quad(q1, depth + 1, max_depth) + split_quad(q2, depth + 1, max_depth)

def split_quad_2x2(quad):
    p0, p1, p2, p3 = quad
    sub_nodes = [[(0.0, 0.0) for _ in range(3)] for _ in range(3)]
    for u in range(3):
        t_u = u / 2
        pt_top = interpolate(p0, p1, t_u)
        pt_bot = interpolate(p3, p2, t_u)
        for v in range(3):
            t_v = v / 2
            sub_nodes[u][v] = interpolate(pt_top, pt_bot, t_v)
            
    Q = [
        [ [sub_nodes[0][0], sub_nodes[1][0], sub_nodes[1][1], sub_nodes[0][1]],
          [sub_nodes[0][1], sub_nodes[1][1], sub_nodes[1][2], sub_nodes[0][2]] ],
        [ [sub_nodes[1][0], sub_nodes[2][0], sub_nodes[2][1], sub_nodes[1][1]],
          [sub_nodes[1][1], sub_nodes[2][1], sub_nodes[2][2], sub_nodes[1][2]] ]
    ]
    return Q

def line_intersection(p1, v1, p2, v2):
    cross = v1[0] * v2[1] - v1[1] * v2[0]
    if abs(cross) < 1e-6:
        return ((p1[0] + p2[0]) / 2.0, (p1[1] + p2[1]) / 2.0)
    dx = p2[0] - p1[0]
    dy = p2[1] - p1[1]
    t = (dx * v2[1] - dy * v2[0]) / cross
    return (p1[0] + t * v1[0], p1[1] + t * v1[1])

def offset_polygon(vertices, margins):
    n = len(vertices)
    if n < 3:
        return vertices
    area = 0.0
    for i in range(n):
        x1, y1 = vertices[i]
        x2, y2 = vertices[(i + 1) % n]
        area += x1 * y2 - x2 * y1
    is_ccw = area > 0
    offset_lines = []
    for i in range(n):
        p1 = vertices[i]
        p2 = vertices[(i + 1) % n]
        dx = p2[0] - p1[0]
        dy = p2[1] - p1[1]
        length = math.sqrt(dx*dx + dy*dy)
        if length < 1e-6:
            ux, uy = 1.0, 0.0
        else:
            ux = dx / length
            uy = dy / length
        if is_ccw:
            nx = -uy
            ny = ux
        else:
            nx = uy
            ny = -ux
        margin = margins[i]
        mid_x = (p1[0] + p2[0]) / 2.0 + nx * margin
        mid_y = (p1[1] + p2[1]) / 2.0 + ny * margin
        offset_lines.append(((mid_x, mid_y), (ux, uy)))
    new_vertices = []
    for i in range(n):
        p_prev, v_prev = offset_lines[(i - 1) % n]
        p_curr, v_curr = offset_lines[i]
        junc = line_intersection(p_prev, v_prev, p_curr, v_curr)
        new_vertices.append(junc)
    return new_vertices

# ================= GRID SETUP & PERTURBATION =================

N_x = 8
N_y = 8
perturb_max = 110.0

x_grid = [[0.0 for _ in range(N_y + 1)] for _ in range(N_x + 1)]
y_grid = [[0.0 for _ in range(N_y + 1)] for _ in range(N_x + 1)]

for i in range(N_x + 1):
    for j in range(N_y + 1):
        x_base = (i / N_x) * S
        y_base = (j / N_y) * S
        dx = random.uniform(-perturb_max, perturb_max) if 0 < i < N_x else 0.0
        dy = random.uniform(-perturb_max, perturb_max) if 0 < j < N_y else 0.0
        x_grid[i][j] = x_base + dx
        y_grid[i][j] = y_base + dy

# Get quadrilateral cells
def get_quad(i, j):
    return [
        (x_grid[i][j], y_grid[i][j]),
        (x_grid[i+1][j], y_grid[i+1][j]),
        (x_grid[i+1][j+1], y_grid[i+1][j+1]),
        (x_grid[i][j+1], y_grid[i][j+1])
    ]

# ================= CELL TYPE ASSIGNMENT =================

cell_type = {}
for i in range(N_x):
    for j in range(N_y):
        cell_type[(i, j)] = 'farmland'

# Diagonal forest belt cells
diagonal_forest_cells = [(4, 2), (3, 3), (2, 4), (1, 5), (1, 6)]
for c in diagonal_forest_cells:
    cell_type[c] = 'forest'

# Forest patches
cell_type[(0, 3)] = 'forest'
cell_type[(7, 4)] = 'forest'

# Farmyards and Industrial zones
cell_type[(1, 0)] = 'farmyard_nw'
cell_type[(6, 7)] = 'farmyard_se'
cell_type[(3, 0)] = 'yard_n1'
cell_type[(5, 0)] = 'yard_n2'
cell_type[(1, 7)] = 'yard_s1'
cell_type[(3, 7)] = 'yard_s2'
cell_type[(5, 7)] = 'yard_s3'

# ================= TOWN GENERATION =================
road_p_pts = [
    (x_grid[6][0], y_grid[6][0]),
    (x_grid[6][1], y_grid[6][1]),
    (x_grid[5][2], y_grid[5][2]),
    (x_grid[4][3], y_grid[4][3]),
    (x_grid[3][4], y_grid[3][4]),
    (x_grid[2][5], y_grid[2][5]),
    (x_grid[2][6], y_grid[2][6]),
    (x_grid[2][7], y_grid[2][7]),
    (x_grid[2][8], y_grid[2][8])
]

# Town is generated along segment 1 (6,1)-(5,2) and segment 2 (5,2)-(4,3)
TOWN_SEGS = [1, 2]

# Track roads: horizontal j=1, j=7 and vertical i=2, i=4, i=6
road_t_lines = [
    [(x_grid[i][1], y_grid[i][1]) for i in range(9)],
    [(x_grid[i][7], y_grid[i][7]) for i in range(9)],
    [(x_grid[2][j], y_grid[2][j]) for j in range(9)],
    [(x_grid[4][j], y_grid[4][j]) for j in range(9)],
    [(x_grid[6][j], y_grid[6][j]) for j in range(9)]
]

def distance_to_segment(P, A, B):
    ax, ay = A
    bx, by = B
    px, py = P
    dx = bx - ax
    dy = by - ay
    lensq = dx*dx + dy*dy
    if lensq == 0:
        return math.sqrt((px-ax)**2 + (py-ay)**2), A
    t = ((px - ax) * dx + (py - ay) * dy) / lensq
    t = max(0.0, min(1.0, t))
    cx = ax + t * dx
    cy = ay + t * dy
    dist = math.sqrt((px - cx)**2 + (py - cy)**2)
    return dist, (cx, cy)

def is_plot_overlapping(plot, track_roads):
    points_to_check = list(plot)
    cx = sum(p[0] for p in plot) / len(plot)
    cy = sum(p[1] for p in plot) / len(plot)
    points_to_check.append((cx, cy))
    
    for P in points_to_check:
        # Check map borders (S = 4096)
        if P[0] < 45.0 or P[0] > 4051.0 or P[1] < 45.0 or P[1] > 4051.0:
            return True
            
        # Check track roads
        for line in track_roads:
            for i in range(len(line) - 1):
                d, _ = distance_to_segment(P, line[i], line[i+1])
                if d < 55.0:
                    return True
                    
        # Check non-town primary road segments
        for i in range(len(road_p_pts) - 1):
            if i not in TOWN_SEGS:
                d, _ = distance_to_segment(P, road_p_pts[i], road_p_pts[i+1])
                if d < 55.0:
                    return True
    return False

def is_street_valid(p_junc, p_end, track_roads):
    px1 = p_junc[0] + 0.8 * (p_end[0] - p_junc[0])
    py1 = p_junc[1] + 0.8 * (p_end[1] - p_junc[1])
    px2 = p_end[0]
    py2 = p_end[1]
    
    for P in [(px1, py1), (px2, py2)]:
        if P[0] < 45.0 or P[0] > 4051.0 or P[1] < 45.0 or P[1] > 4051.0:
            return False
            
        # Check track roads
        for line in track_roads:
            for i in range(len(line) - 1):
                d, _ = distance_to_segment(P, line[i], line[i+1])
                if d < 38.0:
                    return False
                    
        # Check non-town primary road segments
        for i in range(len(road_p_pts) - 1):
            if i not in TOWN_SEGS:
                d, _ = distance_to_segment(P, road_p_pts[i], road_p_pts[i+1])
                if d < 45.0:
                    return False
    return True

def push_away_from_segment(P, A, B, clearance):
    px, py = P
    d, c = distance_to_segment(P, A, B)
    if d < clearance:
        cx, cy = c
        dx = px - cx
        dy = py - cy
        dist = math.sqrt(dx*dx + dy*dy)
        if dist > 0.1:
            px = cx + (dx / dist) * clearance
            py = cy + (dy / dist) * clearance
        else:
            ax, ay = A
            bx, by = B
            ux = bx - ax
            uy = by - ay
            L = math.sqrt(ux*ux + uy*uy)
            if L > 0:
                nx = -uy / L
                ny = ux / L
                px = cx + nx * clearance
                py = cy + ny * clearance
    return (px, py)

town_res_polys = []
global_town_streets = []
road_p_pts_with_junctions = []

def generate_roadside_town(road_points, segments_indices, d_start=24.0, d_depth=55.0, plot_width=42.0, plot_gap=8.0):
    global town_res_polys, global_town_streets, road_p_pts_with_junctions
    plot_count = 0
    
    for i in range(len(road_points) - 1):
        A = road_points[i]
        B = road_points[i+1]
        
        road_p_pts_with_junctions.append(A)
        
        if i in segments_indices:
            ax, ay = A
            bx, by = B
            dx = bx - ax
            dy = by - ay
            L = math.sqrt(dx*dx + dy*dy)
            if L == 0:
                continue
            ux = dx / L
            uy = dy / L
            nx = -uy
            ny = ux
            
            margin_end = 15.0
            current_s = margin_end
            junctions_this_segment = []
            
            while current_s + plot_width <= L - margin_end:
                is_side_street = (plot_count % 4 == 0) and (plot_count > 0)
                
                if is_side_street:
                    s_mid = current_s + plot_width / 2.0
                    p_junc = (ax + s_mid * ux, ay + s_mid * uy)
                    p_end = (ax + s_mid * ux + 120.0 * nx, ay + s_mid * uy + 120.0 * ny)
                    
                    if is_street_valid(p_junc, p_end, road_t_lines):
                        junctions_this_segment.append((s_mid, p_junc))
                        global_town_streets.append((p_junc, p_end))
                        
                        ss_start = 45.0
                        ss_end = 85.0
                        ss_d_start = 15.0
                        ss_d_depth = 35.0
                        
                        ssp = [
                            (ax + s_mid * ux + ss_start * nx - ss_d_start * ux, ay + s_mid * uy + ss_start * ny - ss_d_start * uy),
                            (ax + s_mid * ux + ss_end * nx - ss_d_start * ux, ay + s_mid * uy + ss_end * ny - ss_d_start * uy),
                            (ax + s_mid * ux + ss_end * nx - (ss_d_start + ss_d_depth) * ux, ay + s_mid * uy + ss_end * ny - (ss_d_start + ss_d_depth) * ux),
                            (ax + s_mid * ux + ss_start * nx - (ss_d_start + ss_d_depth) * ux, ay + s_mid * uy + ss_start * ny - (ss_d_start + ss_d_depth) * ux)
                        ]
                        if not is_plot_overlapping(ssp, road_t_lines):
                            town_res_polys.append(ssp)
                            
                        ssq = [
                            (ax + s_mid * ux + ss_start * nx + ss_d_start * ux, ay + s_mid * uy + ss_start * ny + ss_d_start * ux),
                            (ax + s_mid * ux + ss_end * nx + ss_d_start * ux, ay + s_mid * uy + ss_end * ny + ss_d_start * ux),
                            (ax + s_mid * ux + ss_end * nx + (ss_d_start + ss_d_depth) * ux, ay + s_mid * uy + ss_end * ny + (ss_d_start + ss_d_depth) * ux),
                            (ax + s_mid * ux + ss_start * nx + (ss_d_start + ss_d_depth) * ux, ay + s_mid * uy + ss_start * ny + (ss_d_start + ss_d_depth) * ux)
                        ]
                        if not is_plot_overlapping(ssq, road_t_lines):
                            town_res_polys.append(ssq)
                            
                        q = [
                            (ax + current_s * ux - d_start * nx, ay + current_s * uy - d_start * ny),
                            (ax + (current_s + plot_width) * ux - d_start * nx, ay + (current_s + plot_width) * uy - d_start * ny),
                            (ax + (current_s + plot_width) * ux - (d_start + d_depth) * nx, ay + (current_s + plot_width) * uy - (d_start + d_depth) * ny),
                            (ax + current_s * ux - (d_start + d_depth) * nx, ay + current_s * uy - (d_start + d_depth) * ny)
                        ]
                        if not is_plot_overlapping(q, road_t_lines):
                            town_res_polys.append(q)
                else:
                    p = [
                        (ax + current_s * ux + d_start * nx, ay + current_s * uy + d_start * ny),
                        (ax + (current_s + plot_width) * ux + d_start * nx, ay + (current_s + plot_width) * uy + d_start * ny),
                        (ax + (current_s + plot_width) * ux + (d_start + d_depth) * nx, ay + (current_s + plot_width) * uy + (d_start + d_depth) * ny),
                        (ax + current_s * ux + (d_start + d_depth) * nx, ay + current_s * uy + (d_start + d_depth) * ny)
                    ]
                    if not is_plot_overlapping(p, road_t_lines):
                        town_res_polys.append(p)
                        
                    q = [
                        (ax + current_s * ux - d_start * nx, ay + current_s * uy - d_start * ny),
                        (ax + (current_s + plot_width) * ux - d_start * nx, ay + (current_s + plot_width) * uy - d_start * ny),
                        (ax + (current_s + plot_width) * ux - (d_start + d_depth) * nx, ay + (current_s + plot_width) * uy - (d_start + d_depth) * ny),
                        (ax + current_s * ux - (d_start + d_depth) * nx, ay + current_s * uy - (d_start + d_depth) * ny)
                    ]
                    if not is_plot_overlapping(q, road_t_lines):
                        town_res_polys.append(q)
                
                plot_count += 1
                current_s += plot_width + plot_gap
            
            junctions_this_segment.sort(key=lambda x: x[0])
            for s, pt in junctions_this_segment:
                road_p_pts_with_junctions.append(pt)
                
    road_p_pts_with_junctions.append(road_points[-1])

generate_roadside_town(road_p_pts, TOWN_SEGS)
town_streets = global_town_streets

def get_edge_margins(poly, cell_type_str, extra_margin=0.0):
    margins = []
    n = len(poly)
    for k in range(n):
        A = poly[k]
        B = poly[(k + 1) % n]
        
        mid_x = (A[0] + B[0]) / 2.0
        mid_y = (A[1] + B[1]) / 2.0
        mid = (mid_x, mid_y)
        
        if cell_type_str == 'forest':
            base_margin = 0.0
        elif cell_type_str.startswith('yard') or cell_type_str.startswith('farmyard'):
            base_margin = 10.0
        else:
            base_margin = 15.0
            
        margin = base_margin + extra_margin
        
        min_d_p = float('inf')
        is_town_seg = False
        for j in range(len(road_p_pts) - 1):
            d, _ = distance_to_segment(mid, road_p_pts[j], road_p_pts[j+1])
            if d < min_d_p:
                min_d_p = d
                is_town_seg = (j in TOWN_SEGS)
                
        if min_d_p < 15.0:
            margin = 110.0 + extra_margin if is_town_seg else 40.0 + extra_margin
            
        for p_junc, p_end in town_streets:
            d, _ = distance_to_segment(mid, p_junc, p_end)
            if d < 15.0:
                margin = 60.0 + extra_margin
                break
                
        margins.append(margin)
    return margins

# ================= POLYGON GATHERING =================

farmland_polys = []
forest_polys = []  # shrunken forest polygons
yard_polys = []

# Process all cells
for i in range(N_x):
    for j in range(N_y):
        t = cell_type[(i, j)]
        quad = get_quad(i, j)
        
        if (i, j) in [(5, 1), (4, 2), (3, 3), (2, 4)]:
            tri1 = [quad[0], quad[3], quad[1]]
            tri2 = [quad[2], quad[1], quad[3]]
            sub_cells = [(tri1, t), (tri2, t)]
        else:
            sub_cells = [(quad, t)]
            
        for geom, cell_t in sub_cells:
            if cell_t == 'forest':
                shrunken_margins = get_edge_margins(geom, 'forest', 32.0)
                clipped = offset_polygon(geom, shrunken_margins)
                forest_polys.append(clipped)
            elif cell_t.startswith('yard_') or cell_t.startswith('farmyard_'):
                Q = split_quad_2x2(geom)
                if cell_t == 'farmyard_nw':
                    uy, vy = 1, 1
                    conn_node = (2, 1)
                elif cell_t == 'farmyard_se':
                    uy, vy = 0, 0
                    conn_node = (6, 7)
                elif cell_t == 'yard_n1':
                    uy, vy = 1, 1
                    conn_node = (4, 1)
                elif cell_t == 'yard_n2':
                    uy, vy = 0, 1
                    conn_node = (6, 1)
                elif cell_t == 'yard_s1':
                    uy, vy = 1, 0
                    conn_node = (2, 7)
                elif cell_t == 'yard_s2':
                    uy, vy = 0, 0
                    conn_node = (4, 7)
                elif cell_t == 'yard_s3':
                    uy, vy = 0, 0
                    conn_node = (6, 7)
                    
                for ux in range(2):
                    for vy_val in range(2):
                        sub_q = Q[ux][vy_val]
                        if ux == uy and vy_val == vy:
                             margins = get_edge_margins(sub_q, 'yard')
                             clipped = offset_polygon(sub_q, margins)
                             yard_polys.append(clipped)
                        else:
                             margins = get_edge_margins(sub_q, 'farmland')
                             clipped = offset_polygon(sub_q, margins)
                             farmland_polys.append(clipped)
            else:
                dist_to_town = math.sqrt((i - 2.5)**2 + (j - 1.0)**2)
                if dist_to_town < 2.0:
                    max_depth = 1 if random.random() < 0.5 else 0
                else:
                    max_depth = 0
                    
                sub_fields = split_quad(geom, 0, max_depth)
                for sf in sub_fields:
                    margins = get_edge_margins(sf, 'farmland')
                    clipped = offset_polygon(sf, margins)
                    farmland_polys.append(clipped)

# ================= REGISTER OSM ELEMENTS =================

# 1. Farmland ways
for poly in farmland_polys:
    if len(poly) >= 3:
        ns = [create_unique_node(x, y) for (x, y) in poly]
        if ns[0] != ns[-1]:
            ns.append(ns[0])
        add_way(ns, {'landuse': 'farmland'})

# 2. Forest ways
for poly in forest_polys:
    if len(poly) >= 3:
        ns = [create_unique_node(x, y) for (x, y) in poly]
        if ns[0] != ns[-1]:
            ns.append(ns[0])
        add_way(ns, {'natural': 'wood', 'name': 'Diagonal Forest'})

# 3. Town residential blocks
for poly in town_res_polys:
    if len(poly) >= 3:
        ns = [create_unique_node(x, y) for (x, y) in poly]
        if ns[0] != ns[-1]:
            ns.append(ns[0])
        add_way(ns, {'landuse': 'residential'})

# 4. Town streets
for p1, p2 in town_streets:
    ns = [get_node(p1[0], p1[1]), get_node(p2[0], p2[1])]
    add_way(ns, {'highway': 'residential'})

# 5. Yards
for poly in yard_polys:
    if len(poly) >= 3:
        ns = [create_unique_node(x, y) for (x, y) in poly]
        if ns[0] != ns[-1]:
            ns.append(ns[0])
        add_way(ns, {'landuse': 'farmyard', 'building': 'industrial'})

# 7. Main Winding Roads (topologically connected)
road_p_lines = [
    (road_p_pts_with_junctions, "Diagonal Road")
]
road_t_lines = [
    ([(x_grid[i][1], y_grid[i][1]) for i in range(9)], "North Winding Track"),
    ([(x_grid[i][7], y_grid[i][7]) for i in range(9)], "South Winding Track"),
    ([(x_grid[2][j], y_grid[2][j]) for j in range(9)], "West Winding Track"),
    ([(x_grid[4][j], y_grid[4][j]) for j in range(9)], "Central Winding Track"),
    ([(x_grid[6][j], y_grid[6][j]) for j in range(9)], "East Winding Track")
]

for line, name in road_p_lines:
    ns = [get_node(x, y) for (x, y) in line]
    add_way(ns, {'highway': 'primary', 'name': name})

for line, name in road_t_lines:
    ns = [get_node(x, y) for (x, y) in line]
    add_way(ns, {'highway': 'track', 'name': name})

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
