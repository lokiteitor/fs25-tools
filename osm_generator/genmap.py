import random
import math
from PIL import Image, ImageDraw

random.seed(20240605)

S = 8192                      # canvas px
MILES = 8                     # real miles across (PLSS scale)
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
C_IND    = (90,96,110)

# ---- configuration for road widths, borders and gaps ----
TH_P = 22                     # primary road thickness
TH_S = 16                     # secondary road thickness
TH_T = 8                      # track road thickness
W_FIELD_BORDER = 12           # Thicker black lines for fields (originally 1)
GAP = 40                      # Greater separation between polygons and roads (originally 5 for yards)
W_ROAD_BORDER = 12            # Black border/margin for roads
W_CANAL_BORDER = 12           # Black border/margin for canals


img = Image.new("RGB",(S,S),C_FARM)
d = ImageDraw.Draw(img)

def rect(x0,y0,x1,y1,fill,outline=None,width=0):
    d.rectangle([x0,y0,x1,y1],fill=fill,outline=outline,width=width)

# ================= FIELDS (Farmland Parcels) =================
# Subdivide sections into rectangular fields using PLSS binary subdivisions.
# Town block is skipped.
def in_town(cx, cy):
    return m(1) <= cx < m(2) and m(1) <= cy < m(2)

parcels = []
def split_block(x0, y0, x1, y1, depth, edge, near_town):
    w = x1 - x0
    h = y1 - y0
    
    maxdepth = 1
        
    # Introduce early stopping to create a mix of large and small fields
    if depth >= 1 and random.random() < 0.52:
        parcels.append((x0, y0, x1, y1))
        return
        
    if depth >= maxdepth or (w < m(0.15) or h < m(0.15)):
        parcels.append((x0, y0, x1, y1))
        return
        
    # Split using a random ratio to create diverse sizes (rectangular and square)
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
            continue  # Skip town block, drawn later
            
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
            continue  # Draw farmlands near town, along canals, or in the greenhouse block
            
        edge = (i == 0 or i == MILES - 1 or j == 0 or j == MILES - 1)
        split_block(x0, y0, x1, y1, 0, edge, near_town)

# Draw farmland and rice parcels with a simple single dividing line (no margins, W_FIELD_BORDER px border)
C_FARMB = (0,0,0)
C_RICE = (115, 165, 135)  # Flooded rice paddy color (blend of blue-green)

def draw_northern_winding_fields(x0, x1):
    x0_s, x1_s = get_shrunk_x(x0, x1)
    
    # 1. Top Field Polygon
    top_poly = [(x0_s, 20), (x1_s, 20), (x1_s, get_forest_top(x1_s))]
    for x_val in range(int(x1_s), int(x0_s) - 1, -16):
        top_poly.append((x_val, get_forest_top(x_val)))
    top_poly.append((x0_s, get_forest_top(x0_s)))
    
    d.polygon(top_poly, fill=C_FARM)
    d.line(top_poly + [top_poly[0]], fill=C_FARMB, width=W_FIELD_BORDER)
    
    # 2. Bottom Field Polygon(s)
    if x0_s < 2525 and x1_s > 2575:
        # Left Bottom
        left_poly = [(x0_s, get_forest_bottom(x0_s))]
        for x_val in range(int(x0_s), 2526, 16):
            left_poly.append((x_val, get_forest_bottom(x_val)))
        left_poly.extend([(2525, 1001), (x0_s, 1001)])
        
        d.polygon(left_poly, fill=C_FARM)
        d.line(left_poly + [left_poly[0]], fill=C_FARMB, width=W_FIELD_BORDER)
        
        # Right Bottom
        right_poly = [(2575, get_forest_bottom(2575))]
        for x_val in range(2575, int(x1_s) + 1, 16):
            right_poly.append((x_val, get_forest_bottom(x_val)))
        right_poly.extend([(x1_s, 1001), (2575, 1001)])
        
        d.polygon(right_poly, fill=C_FARM)
        d.line(right_poly + [right_poly[0]], fill=C_FARMB, width=W_FIELD_BORDER)
    else:
        bot_poly = [(x0_s, get_forest_bottom(x0_s))]
        for x_val in range(int(x0_s), int(x1_s) + 1, 16):
            bot_poly.append((x_val, get_forest_bottom(x_val)))
        bot_poly.extend([(x1_s, 1001), (x0_s, 1001)])
        
        d.polygon(bot_poly, fill=C_FARM)
        d.line(bot_poly + [bot_poly[0]], fill=C_FARMB, width=W_FIELD_BORDER)

for (x0, y0, x1, y1) in parcels:
    if y0 < m(1):
        draw_northern_winding_fields(x0, x1)
    else:
        fill_col = C_RICE if y0 >= m(7) else C_FARM
        rect(x0, y0, x1, y1, fill_col, outline=C_FARMB, width=W_FIELD_BORDER)

# Draw border forest (all around the edge of the map, width W_BORDER_FOREST px, with gaps for roads/waterways)
W_BORDER_FOREST = 20
# Top and bottom borders (unbroken)
rect(0, 0, S, W_BORDER_FOREST, C_FOREST)
rect(0, S - W_BORDER_FOREST, S, S, C_FOREST)

# Left border segments (gaps for river and roads)
left_segments = [
    (0, 340), (376, 1001), (1047, 2032), (2064, 3056), (3088, 4080),
    (4112, 5104), (5136, 6128), (6160, 7145), (7191, 8192)
]
for y0, y1 in left_segments:
    rect(0, y0, W_BORDER_FOREST, y1, C_FOREST)

# Right border segments (gaps for river, roads, and south canal)
right_segments = [
    (0, 491), (526, 1001), (1047, 2032), (2064, 3056), (3088, 4080),
    (4112, 5104), (5136, 6128), (6160, 7145), (7191, 7655), (7705, 8192)
]
for y0, y1 in right_segments:
    rect(S - W_BORDER_FOREST, y0, S, y1, C_FOREST)

# Merge a few adjacent parcels to create L-shaped fields by erasing their shared boundary
def draw_L():
    if len(parcels) < 2: return
    a = random.choice(parcels)
    cx = (a[0] + a[2]) / 2
    cy = (a[1] + a[3]) / 2
    if a[1] < m(1):
        return  # Keep northern fields rectangular and strictly under 15 hectares
    if not (cx < m(4) and cy < m(4)):
        return  # Only merge fields near the town to keep canal fields rectangular
    for b in parcels:
        if b is a: continue
        if b[1] < m(1): continue # Avoid merging with northern fields
        # Share vertical edge
        if abs(a[2] - b[0]) < 2:
            y_start = max(a[1], b[1])
            y_end = min(a[3], b[3])
            if y_start < y_end - 10:  # Valid overlap
                x_border = a[2]
                rect(x_border - W_FIELD_BORDER, y_start + 2, x_border + W_FIELD_BORDER, y_end - 2, C_FARM)
                return
        # Share horizontal edge
        if abs(a[3] - b[1]) < 2:
            x_start = max(a[0], b[0])
            x_end = min(a[2], b[2])
            if x_start < x_end - 10:  # Valid overlap
                y_border = a[3]
                rect(x_start + 2, y_border - W_FIELD_BORDER, x_end - 2, y_border + W_FIELD_BORDER, C_FARM)
                return

for _ in range(15):
    draw_L()

# Canals variables
CW = 26
CWB = 16
off = TH_T/2 + CW/2 + GAP

# ================= WATER (reservoir close to the town + canals) =================
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

gh_x0, gh_y0 = m(3.2), m(7.0) - TH_P/2 - m(0.7)
gh_x1, gh_y1 = m(3.8), m(7.0) - TH_P/2 - m(0.3)

def hcanal(ym, x0m, x1m, side, width=CW):
    y = m(ym) + side*off
    x0_px = m(x0m)
    if x0m == 1:
        x0_px += TH_P/2 + GAP
    elif x0m == 7:
        x0_px -= TH_P/2 + GAP
        
    x1_px = m(x1m)
    if x1m == 1:
        x1_px += TH_P/2 + GAP
    elif x1m == 7:
        x1_px -= TH_P/2 + GAP
        
    # Draw outline/margin first
    rect(min(x0_px, x1_px) - W_CANAL_BORDER, y-width/2 - W_CANAL_BORDER, max(x0_px, x1_px) + W_CANAL_BORDER, y+width/2 + W_CANAL_BORDER, C_FARMB)
    # Draw water fill
    rect(min(x0_px, x1_px), y-width/2, max(x0_px, x1_px), y+width/2, C_WATER)

def vcanal(xm, y0m, y1m, side, width=CW):
    x = m(xm) + side*off
    y0_px = m(y0m)
    if y0m == 1:
        y0_px += TH_P/2 + GAP
    elif y0m == 7:
        y0_px -= TH_P/2 + GAP
        
    y1_px = m(y1m)
    if y1m == 1:
        y1_px += TH_P/2 + GAP
    elif y1m == 7:
        y1_px -= TH_P/2 + GAP
        
    # Draw outline/margin first
    rect(x-width/2 - W_CANAL_BORDER, min(y0_px, y1_px) - W_CANAL_BORDER, x+width/2 + W_CANAL_BORDER, max(y0_px, y1_px) + W_CANAL_BORDER, C_FARMB)
    # Draw water fill
    rect(x-width/2, min(y0_px, y1_px), x+width/2, max(y0_px, y1_px), C_WATER)



# ================= ROAD WIDTHS AND HELPERS =================
# TH_P, TH_S, TH_T defined at the top of the file

def hline_outline(y,th):
    rect(0,y-th/2-W_ROAD_BORDER,S,y+th/2+W_ROAD_BORDER,C_FARMB)

def vline_outline(x,th):
    y_start = 20 if th == TH_T else m(1) - W_ROAD_BORDER
    rect(x-th/2-W_ROAD_BORDER,y_start-W_ROAD_BORDER,x+th/2+W_ROAD_BORDER,m(7)+W_ROAD_BORDER,C_FARMB)

def hline_fill(y,th,col):
    rect(0,y-th/2,S,y+th/2,col)

def vline_fill(x,th,col):
    y_start = 20 if th == TH_T else m(1)
    rect(x-th/2,y_start,x+th/2,m(7),col)

# Set up road coordinates
hlines = [m(i) for i in range(MILES+1)]
vlines = [m(i) for i in range(MILES+1)]
sec_v = set()  # No secondary vertical roads

# 1. Draw all road outlines/margins first
for k, y in enumerate(hlines):
    if k == 0 or k == MILES: continue  # No road on the outer borders
    elif k == 1 or k == 7: hline_outline(y, TH_P)
    else: hline_outline(y, TH_T)

for k, x in enumerate(vlines):
    if k == 0 or k == MILES: continue
    elif k == 1: vline_outline(x, TH_P)
    elif k in sec_v: vline_outline(x, TH_S)
    else: vline_outline(x, TH_T)

# Draw the connecting road outline
rect(m(3.5) - TH_T/2 - W_ROAD_BORDER, gh_y1 - W_ROAD_BORDER, m(3.5) + TH_T/2 + W_ROAD_BORDER, m(7.0) - TH_P/2 + W_ROAD_BORDER, C_FARMB)

# ================= TOWN (1x1 mile Section, touching intersection at (1,1)) =================
# Under the PLSS, a Section is 1x1 mile (640 acres).
# The town occupies exactly 1 Section (x ∈ [1, 2] miles, y ∈ [1, 2] miles).
TOWN_X0, TOWN_X1, TOWN_Y0, TOWN_Y1 = m(1), m(2), m(1), m(2)

rect(TOWN_X0, TOWN_Y0, TOWN_X1, TOWN_Y1, C_RES)

# PLSS subdivisions: 1 mile = 80 chains.
# Standard town blocks are subdivided into 10 chains x 10 chains (1/8 mile x 1/8 mile = 660 x 660 feet).
# This yields exactly 8x8 blocks, requiring 7 internal streets in each direction.
sw = 3
for i in range(1, 8):
    x = TOWN_X0 + i * (TOWN_X1 - TOWN_X0) / 8
    rect(x-sw/2, TOWN_Y0+m(0.05), x+sw/2, TOWN_Y1-m(0.05), C_RESST)
for i in range(1, 8):
    y = TOWN_Y0 + i * (TOWN_Y1 - TOWN_Y0) / 8
    rect(TOWN_X0+m(0.05), y-sw/2, TOWN_X1-m(0.05), y+sw/2, C_RESST)

# ================= FORESTS (3 large rectangles, occupying half a section pegged to roads) =================
# C_FOREST fill
# Forest 1: Northern half of section [5, 6] x [2, 3], pegged to y=2
rect(m(5.0), m(2.0), m(6.0), m(2.5), C_FOREST)
# Forest 2: Western half of section [2, 3] x [5, 6], pegged to x=2
rect(m(2.0), m(5.0), m(2.5), m(6.0), C_FOREST)
# Forest 3: Southern half of section [5, 6] x [5, 6], pegged to y=6
rect(m(5.0), m(5.5), m(6.0), m(6.0), C_FOREST)
# Forest 4: Surrounding the northern reservoir
rect(FNX0, FNY0, FNX1, FNY1, C_FOREST)
# Forest 5: Surrounding the southern reservoir
rect(FSX0, FSY0, FSX1, FSY1, C_FOREST)

# Gallery Forest surrounding the northern river (with natural geometry)
forest_poly = []
steps_f = 512
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

forest_poly = points_left_f + list(reversed(points_right_f))
d.polygon(forest_poly, fill=C_FOREST)

# ================= FARMYARDS (5 purple squares/rectangles on primary roads) =================
# C_YARD fill, C_YARDB outline
# Each yard is centered on its side of the grid block (section) it hugs.
# Coordinates remove the 5px offset to touch the road fills directly.
yards = [
    # (x0, y0, x1, y1)
    (m(4.375), m(1) + TH_P/2, m(4.625), m(1) + TH_P/2 + m(0.25)),                      # Yard 1: Square (0.25x0.25 mi), centered along y=1, block x ∈ [4, 5]
    (m(2.35), m(7) - TH_P/2 - m(0.3), m(2.65), m(7) - TH_P/2),                         # Yard 2: Square (0.3x0.3 mi), centered along y=7, block x ∈ [2, 3]
    (m(4.4), m(7) - TH_P/2 - m(0.2), m(4.6), m(7) - TH_P/2),                           # Yard 3: Square (0.2x0.2 mi), centered along y=7, block x ∈ [4, 5]
    (m(6.35), m(7) - TH_P/2 - m(0.3), m(6.65), m(7) - TH_P/2),                         # Yard 4: Square (0.3x0.3 mi), centered along y=7, block x ∈ [6, 7]
    (m(1) + TH_P/2, m(4.4), m(1) + TH_P/2 + m(0.2), m(4.6)),                           # Yard 5: Square (0.2x0.2 mi), centered along x=1, block y ∈ [4, 5]
]

for (x0, y0, x1, y1) in yards:
    rect(x0, y0, x1, y1, C_YARD, outline=C_YARDB, width=5)

# ================= INDUSTRIAL (2 grey rectangles, along primary roads on the other side) =================
# Coordinates remove the 5px offset to touch the road fills directly.
ind_spots = [
    (m(1) - TH_P/2 - m(0.4), m(6.2), m(1) - TH_P/2, m(6.8)),                           # Spot 1: 0.4 x 0.6 miles (west of x=1, southwest, block y ∈ [6, 7])
    (m(5.2), m(7.0) - TH_P/2 - m(0.4), m(5.8), m(7.0) - TH_P/2),                       # Spot 2: 0.6 x 0.4 miles (north of y=7, southeast, block x ∈ [5, 6])
]

for (x0, y0, x1, y1) in ind_spots:
    rect(x0, y0, x1, y1, C_IND, outline=C_FARMB, width=3)
    # Draw internal white streets (3px wide) forming a grid of 0.1 x 0.1 mile blocks
    w = x1 - x0
    h = y1 - y0
    cols = int(round(w / m(0.1)))
    rows = int(round(h / m(0.1)))
    
    # Vertical streets
    for i in range(1, cols):
        cx = x0 + i * w / cols
        rect(cx - 1.5, y0 + m(0.02), cx + 1.5, y1 - m(0.02), C_RESST)
        
    # Horizontal streets
    for j in range(1, rows):
        cy = y0 + j * h / rows
        rect(x0 + m(0.02), cy - 1.5, x1 - m(0.02), cy + 1.5, C_RESST)

# ================= GREENHOUSE FARMYARD (Light turquoise yard for greenhouses, in undivided north area) =================
C_GH_YARD = (170, 210, 205)
C_GH_YARDB = (100, 150, 145)

# Center it in block i=3, j=6 (x ∈ [3, 4] miles, y ∈ [6, 7] miles, north of y=7 road)
# Draw yard background and border
rect(gh_x0, gh_y0, gh_x1, gh_y1, C_GH_YARD, outline=C_GH_YARDB, width=5)

# Draw 4 parallel glassy greenhouses inside the yard
for i in range(4):
    gy0 = gh_y0 + m(0.06) + i * m(0.08)
    gy1 = gy0 + m(0.04)
    gx0 = gh_x0 + m(0.08)
    gx1 = gh_x1 - m(0.08)
    rect(gx0, gy0, gx1, gy1, fill=(235, 245, 250), outline=(255, 255, 255), width=2)

# ================= DRAW ROAD FILLS =================
# 2. Draw all road fills on top
for k, y in enumerate(hlines):
    if k == 0 or k == MILES: continue
    elif k == 1 or k == 7: hline_fill(y, TH_P, C_ROADP)
    else: hline_fill(y, TH_T, C_ROADT)

for k, x in enumerate(vlines):
    if k == 0 or k == MILES: continue
    elif k == 1: vline_fill(x, TH_P, C_ROADP)
    elif k in sec_v: vline_fill(x, TH_S, C_ROADS)
    else: vline_fill(x, TH_T, C_ROADT)

# Draw the vertical connecting road from the greenhouse yard to the primary road fill
rect(m(3.5) - TH_T/2, gh_y1, m(3.5) + TH_T/2, m(7.0) - TH_P/2, C_ROADT)

# Draw canals hugging roads further away from the town
vcanal(3, 1.2, 7.5, side=-1)  # Vertical canal along x=3 extended to y=7.5 to feed the south canal
hcanal(3, 1, 7, side=+1)    # Horizontal canal along y=3
hcanal(7.5, 0.85, 8, side=0) # South canal along y=7.5 (no offset) connecting reservoir to the east border

# ================= RIVER =================
# Winding river in the northern area (y ∈ [0, 1] mile)
# Flows from x=0 to x=S (8192px)
# Simulated flow: 20-30 m3/s (corresponds to ~16-26m real width, scaled to 26-38px for visual clarity)
river_poly = []
steps = 512
points_left = []
points_right = []
for i in range(steps + 1):
    x = i * (S / steps)
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

river_poly = points_left + list(reversed(points_right))

# Compute slightly smaller polygon for the water fill to leave a black outline
points_left_fill = []
points_right_fill = []
for i in range(steps + 1):
    x = i * (S / steps)
    y_c = m(0.35) + (m(0.1) * (x / S)) + 90 * math.sin(x * 2 * math.pi / 3200) + 25 * math.sin(x * 2 * math.pi / 900)
    w = 32 + 6 * math.sin(x * 2 * math.pi / 1500)
    w_fill = max(8.0, w - W_FIELD_BORDER) # Leave a W_FIELD_BORDER/2 black outline on each side
    
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
    
    lx = x + nx * (w_fill / 2)
    ly = y_c + ny * (w_fill / 2)
    rx = x - nx * (w_fill / 2)
    ry = y_c - ny * (w_fill / 2)
    
    points_left_fill.append((lx, ly))
    points_right_fill.append((rx, ry))

river_poly_fill = points_left_fill + list(reversed(points_right_fill))

# Draw the river
d.polygon(river_poly, fill=C_FARMB)

# Small reservoir (embalse) polygon - centered on the river path at y=278
small_res_poly = [
    (2550, 180), (2610, 210), (2650, 278), (2610, 340), (2550, 370),
    (2490, 340), (2450, 278), (2490, 210)
]

# Shrink the small reservoir for fill to leave a black outline
cx, cy = 2550, 278
small_res_poly_fill = []
for (x, y) in small_res_poly:
    xf = cx + (x - cx) * 0.90
    yf = cy + (y - cy) * 0.90
    small_res_poly_fill.append((xf, yf))

# Connecting channel (canal) dimensions
chan_x = 2550
chan_y0 = 350  # Overlap inside the small reservoir
chan_y1 = 1240 # Overlap inside the main reservoir

# Draw small reservoir and channel outlines
d.polygon(small_res_poly, fill=C_FARMB)
rect(chan_x - CW/2 - W_CANAL_BORDER, chan_y0, chan_x + CW/2 + W_CANAL_BORDER, chan_y1, C_FARMB)

# Draw fills
d.polygon(river_poly_fill, fill=C_WATER)
d.polygon(small_res_poly_fill, fill=C_WATER)
rect(chan_x - CW/2, chan_y0, chan_x + CW/2, chan_y1, C_WATER)

# Draw the reservoirs
rect(RX0, RY0, RX1, RY1, C_WATER)
rect(SRX0, SRY0, SRX1, SRY1, C_WATER)

# The reservoir now connects directly to the vertical canal at x=3, so no connector canal is needed.

img.save("outputs/zoning_map.png")
print("done: map generated with PLSS grid")

