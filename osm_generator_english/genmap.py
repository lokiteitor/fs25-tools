import random
import math
from PIL import Image, ImageDraw
import os

random.seed(20240605)

S = 4096                      # canvas px
MILES = 4                     # real miles across
PPM = S / MILES               # px per mile = 1024
def m(x): return x * PPM      # helper for miles

# ---- palette ----
C_FARM   = (150,168,88)
C_FARMB  = (0,0,0)
C_ROADP  = (240,200,30)       # Amarillo para caminos principales
C_ROADS  = (175,95,40)
C_ROADT  = (120,120,124)
C_WATER  = (54,110,168)
C_FOREST = (38,74,44)
C_RES    = (170,78,70)
C_RESST  = (225,225,220)
C_YARD   = (110,80,120)
C_YARDB  = (60,42,72)

# ---- configuration for road widths, borders and gaps ----
TH_P = 22                     # primary road thickness
TH_S = 16                     # secondary road thickness
TH_T = 8                      # track road thickness
W_FIELD_BORDER = 12           # Thicker black lines for fields
GAP = 40                      # Greater separation between polygons and roads
W_ROAD_BORDER = 12            # Black border/margin for roads

img = Image.new("RGB", (S, S), C_FARM)
d = ImageDraw.Draw(img)

def rect(x0,y0,x1,y1,fill,outline=None,width=0):
    d.rectangle([x0,y0,x1,y1],fill=fill,outline=outline,width=width)

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

# Track roads: horizontal j=1, j=7 and vertical i=2, i=4, i=6
road_t_lines = [
    [(x_grid[i][1], y_grid[i][1]) for i in range(9)],
    [(x_grid[i][7], y_grid[i][7]) for i in range(9)],
    [(x_grid[2][j], y_grid[2][j]) for j in range(9)],
    [(x_grid[4][j], y_grid[4][j]) for j in range(9)],
    [(x_grid[6][j], y_grid[6][j]) for j in range(9)]
]

# Town is generated along segment 1 (6,1)-(5,2) and segment 2 (5,2)-(4,3)
TOWN_SEGS = [1, 2]

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
                            (ax + s_mid * ux + ss_start * nx + ss_d_start * ux, ay + s_mid * uy + ss_start * ny + ss_d_start * uy),
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
                
        if min_d_p < 155.0:
            if is_town_seg:
                # Adaptive: push field edge exactly to 155px from road (zone 140px + 15px gap)
                margin = max(0.0, 155.0 - min_d_p) + extra_margin
            elif min_d_p < 80.0:
                margin = 40.0 + extra_margin
            
        for p_junc, p_end in town_streets:
            d, _ = distance_to_segment(mid, p_junc, p_end)
            if d < 80.0:
                margin = 60.0 + extra_margin
                break
                
        margins.append(margin)
    return margins

# ================= POLYGON GATHERING =================

farmland_polys = []
forest_polys = []  # tuple of (outer, inner)
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
                outer_margins = get_edge_margins(geom, 'forest', 0.0)
                inner_margins = get_edge_margins(geom, 'forest', 32.0)
                outer = offset_polygon(geom, outer_margins)
                inner = offset_polygon(geom, inner_margins)
                forest_polys.append((outer, inner))
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

# ================= DRAWING HELPERS =================

def road_buffer_polygon(pts, width):
    """Create a wide buffer polygon around a polyline (for town zone clearing)."""
    n = len(pts)
    left_pts = []
    right_pts = []
    for k in range(n):
        normals = []
        if k > 0:
            dx = pts[k][0] - pts[k-1][0]
            dy = pts[k][1] - pts[k-1][1]
            L = math.sqrt(dx*dx + dy*dy)
            if L > 0:
                normals.append((-dy/L, dx/L))
        if k < n - 1:
            dx = pts[k+1][0] - pts[k][0]
            dy = pts[k+1][1] - pts[k][1]
            L = math.sqrt(dx*dx + dy*dy)
            if L > 0:
                normals.append((-dy/L, dx/L))
        if normals:
            nx = sum(v[0] for v in normals) / len(normals)
            ny = sum(v[1] for v in normals) / len(normals)
            nL = math.sqrt(nx*nx + ny*ny)
            if nL > 0:
                nx, ny = nx/nL, ny/nL
        else:
            nx, ny = 0.0, 1.0
        left_pts.append((pts[k][0] + width*nx, pts[k][1] + width*ny))
        right_pts.append((pts[k][0] - width*nx, pts[k][1] - width*ny))
    return left_pts + list(reversed(right_pts))

def sign_cross(A, B, P):
    """Sign of cross product of (B-A) x (P-A)."""
    return (B[0]-A[0])*(P[1]-A[1]) - (B[1]-A[1])*(P[0]-A[0])

def convex_hull(pts):
    """Jarvis march convex hull of a set of 2D points."""
    if len(pts) < 3:
        return pts
    pts = list(set(pts))
    n = len(pts)
    start = min(range(n), key=lambda i: (pts[i][0], pts[i][1]))
    hull = []
    current = start
    while True:
        hull.append(pts[current])
        nxt = (current + 1) % n
        for i in range(n):
            cp = sign_cross(pts[current], pts[nxt], pts[i])
            if cp < 0 or (cp == 0 and
                math.dist(pts[current], pts[i]) > math.dist(pts[current], pts[nxt])):
                nxt = i
        current = nxt
        if current == start:
            break
    return hull

# Separate town plots into left/right sides of road and compute zone polygons
town_road_pts = road_p_pts[1:4]  # road_p_pts[1], [2], [3]
left_pts_zone = []
right_pts_zone = []

for plot in town_res_polys:
    cx = sum(p[0] for p in plot) / len(plot)
    cy = sum(p[1] for p in plot) / len(plot)
    min_d = float('inf')
    side_cross = 0
    for k in range(len(town_road_pts) - 1):
        A = town_road_pts[k]
        B = town_road_pts[k + 1]
        dist_k, _ = distance_to_segment((cx, cy), A, B)
        if dist_k < min_d:
            min_d = dist_k
            side_cross = sign_cross(A, B, (cx, cy))
    if side_cross >= 0:
        left_pts_zone.extend(plot)
    else:
        right_pts_zone.extend(plot)

left_zone_poly  = convex_hull(left_pts_zone)  if len(left_pts_zone)  >= 3 else []
right_zone_poly = convex_hull(right_pts_zone) if len(right_pts_zone) >= 3 else []

# ================= DRAWING ELEMENTS =================

rect(0, 0, S, S, C_FARMB)

# 1. Farmland polygons
for poly in farmland_polys:
    if len(poly) >= 3:
        d.polygon(poly, fill=C_FARM, outline=C_FARMB, width=W_FIELD_BORDER)

# 2. Forest polygons
for outer, inner in forest_polys:
    d.polygon(outer, fill=C_FARMB)
    d.polygon(inner, fill=C_FOREST)

# 2b. Town zone background (150px) - erases any field/forest inside the gap zone
town_zone_pts = [road_p_pts[1], road_p_pts[2], road_p_pts[3]]
town_zone = road_buffer_polygon(town_zone_pts, 155)
d.polygon(town_zone, fill=C_FARMB)

# 3. Residential zones - two solid red polygons (one per side of primary road)
C_ZONE = (190, 60, 60)  # solid red for residential zone
if left_zone_poly and len(left_zone_poly) >= 3:
    d.polygon(left_zone_poly, fill=C_ZONE, outline=(150, 40, 40), width=5)
if right_zone_poly and len(right_zone_poly) >= 3:
    d.polygon(right_zone_poly, fill=C_ZONE, outline=(150, 40, 40), width=5)

# 3b. Town streets (drawn on top of zone polygons)
for p1, p2 in town_streets:
    d.line([p1, p2], fill=C_FARMB, width=6 + 2 * W_ROAD_BORDER, joint="round")
for p1, p2 in town_streets:
    d.line([p1, p2], fill=C_RESST, width=6, joint="round")

# 4. Yards
for poly in yard_polys:
    d.polygon(poly, fill=C_YARD, outline=C_YARDB, width=5)

road_p_lines = [
    road_p_pts_with_junctions
]

# Draw outlines first
for line in road_p_lines:
    d.line(line, fill=C_FARMB, width=TH_P + 2 * W_ROAD_BORDER, joint="round")
for line in road_t_lines:
    d.line(line, fill=C_FARMB, width=TH_T + 2 * W_ROAD_BORDER, joint="round")

# Draw fills
for line in road_p_lines:
    d.line(line, fill=C_ROADP, width=TH_P, joint="round")
for line in road_t_lines:
    d.line(line, fill=C_ROADT, width=TH_T, joint="round")

# 7. Unassigned 20m outer boundary border
rect(0, 0, S, 20, (0, 0, 0))
rect(0, S - 20, S, S, (0, 0, 0))
rect(0, 0, 20, S, (0, 0, 0))
rect(S - 20, 0, S, S, (0, 0, 0))

os.makedirs("outputs", exist_ok=True)
img.save("outputs/zoning_map.png")
print("done: English layout map generated with perturbed grid")
