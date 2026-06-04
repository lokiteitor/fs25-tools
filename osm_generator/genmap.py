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
            continue  # Skip town block, drawn later

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
            continue  # Draw farmlands near town or along canals
            
        edge = (i == 0 or i == MILES - 1 or j == 0 or j == MILES - 1)
        split_block(x0, y0, x1, y1, 0, edge, near_town)

# Draw farmland and rice parcels with a simple single dividing line (no margins, W_FIELD_BORDER px border)
C_FARMB = (0,0,0)
C_RICE = (115, 165, 135)  # Flooded rice paddy color (blend of blue-green)

for (x0, y0, x1, y1) in parcels:
    cx0 = max(100, x0)
    cy0 = max(100, y0)
    cx1 = min(S - 100, x1)
    cy1 = min(S - 100, y1)
    if cx1 > cx0 and cy1 > cy0:
        fill_col = C_RICE if y0 >= m(7) else C_FARM
        rect(cx0, cy0, cx1, cy1, fill_col, outline=C_FARMB, width=W_FIELD_BORDER)

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
# Draw enclosing rectangular farmyard
rect(3850, 120, 6150, 965, C_YARD, outline=C_YARDB, width=5)

# Draw lake fill
d.polygon(lake_pts, fill=C_WATER)
# Draw lake outline (black)
d.line(lake_pts + [lake_pts[0]], fill=C_FARMB, width=12)


# ================= RAILWAY (Horizontal railway track crossing from east to west at y=980) =================
y_rail = 980
# 1. Draw ballast bed (light grey-brown)
rect(0, y_rail - 15, S, y_rail + 15, (170, 160, 150))
# 2. Draw sleepers/ties (vertical black bars spaced every 36 pixels)
for x in range(10, S, 36):
    rect(x - 3, y_rail - 12, x + 3, y_rail + 12, C_FARMB)
# 3. Draw two parallel steel rails (rust red/orange)
C_RAIL = (180, 60, 60)
rect(0, y_rail - 7, S, y_rail - 4, C_RAIL)
rect(0, y_rail + 4, S, y_rail + 7, C_RAIL)


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



# ================= ROAD WIDTHS AND HELPERS =================
# TH_P, TH_S, TH_T defined at the top of the file

def hline_outline(y,th):
    rect(0,y-th/2-W_ROAD_BORDER,S,y+th/2+W_ROAD_BORDER,C_FARMB)

def vline_outline(x,th):
    y_start = m(1) if th == TH_T else m(1) - W_ROAD_BORDER
    rect(x-th/2-W_ROAD_BORDER,y_start-W_ROAD_BORDER,x+th/2+W_ROAD_BORDER,m(7)+W_ROAD_BORDER,C_FARMB)

def hline_fill(y,th,col):
    rect(0,y-th/2,S,y+th/2,col)

def vline_fill(x,th,col):
    y_start = m(1) if th == TH_T else m(1)
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
    elif k in [1, 7]: vline_outline(x, TH_P)
    elif k in sec_v: vline_outline(x, TH_S)
    else: vline_outline(x, TH_T)


# ================= TOWN (1x1 mile Section, rectangular hugging the north-west) =================
# Under the PLSS, a Section is 1x1 mile (640 acres).
# The town occupies column 0..4 (x ∈ [1, 1.625] miles, y ∈ [1, 1.5] miles).
TOWN_X0, TOWN_X1, TOWN_Y0, TOWN_Y1 = m(1), m(2), m(1), m(2)

# Draw rectangular town hugging the north-west
rect(m(1.0), m(1.0), m(1.625), m(1.5), C_RES)

# Draw new farmyards in the 3 easternmost columns (5, 6, 7) of the town section
rect(m(1.625), m(1.0), m(2.0), m(1.5), C_YARD, outline=C_YARDB, width=5)

# PLSS subdivisions: 1 mile = 80 chains.
# Standard town blocks are subdivided into 10 chains x 10 chains (1/8 mile x 1/8 mile = 660 x 660 feet).
# This yields exactly 8x8 blocks, requiring 7 internal streets in each direction.
sw = 3
for i in range(1, 5):
    x = TOWN_X0 + i * (TOWN_X1 - TOWN_X0) / 8
    rect(x-sw/2, TOWN_Y0+m(0.05), x+sw/2, m(1.5), C_RESST)
for i in range(1, 4):
    y = TOWN_Y0 + i * (TOWN_Y1 - TOWN_Y0) / 8
    rect(TOWN_X0+m(0.05), y-sw/2, m(1.625), y+sw/2, C_RESST)

# ================= FORESTS (3 large rectangles, occupying half a section pegged to roads) =================
# C_FOREST fill
# Forest 1: Northern half of section [5, 6] x [2, 3], pegged to y=2
rect(m(5.0), m(2.0), m(6.0), m(2.5), C_FOREST)
# Forest 2: Western half of section [2, 3] x [1, 2], pegged to x=2 (next to town farmyard)
rect(m(2.0), m(1.0), m(2.5), m(2.0), C_FOREST)
# Forest 3: Southern half of section [5, 6] x [5, 6], pegged to y=6
rect(m(5.0), m(5.5), m(6.0), m(6.0), C_FOREST)

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
    (m(7) - TH_P/2 - m(0.5), m(4.25), m(7) - TH_P/2, m(4.75))                            # New Yard: Square (0.5x0.5 mi), centered along x=7 (East primary road), block y ∈ [4, 5]
]

for (x0, y0, x1, y1) in yards:
    rect(x0, y0, x1, y1, C_YARD, outline=C_YARDB, width=5)

# ================= INDUSTRIAL (2 grey rectangles, along primary roads on the other side) =================
# Coordinates remove the 5px offset to touch the road fills directly.
ind_spots = [
    (m(1) - TH_P/2 - m(0.4), m(6.2), m(1) - TH_P/2, m(6.8)),                           # Spot 1: 0.4 x 0.6 miles (west of x=1, southwest, block y ∈ [6, 7])
    (m(5.2), m(7.0) - TH_P/2 - m(0.4), m(5.8), m(7.0) - TH_P/2),                       # Spot 2: 0.6 x 0.4 miles (north of y=7, southeast, block x ∈ [5, 6])
    (m(1) + TH_P/2, 750, m(2) - TH_T/2, 950),                                          # Spot 3: 1000m x 200m thin strip (north of town, block x ∈ [1, 2], y ∈ [750, 950])
]

for (x0, y0, x1, y1) in ind_spots:
    rect(x0, y0, x1, y1, C_IND, outline=C_FARMB, width=3)


# ================= DRAW ROAD FILLS =================
# 2. Draw all road fills on top
for k, y in enumerate(hlines):
    if k == 0 or k == MILES: continue
    elif k == 1 or k == 7: hline_fill(y, TH_P, C_ROADP)
    else: hline_fill(y, TH_T, C_ROADT)

for k, x in enumerate(vlines):
    if k == 0 or k == MILES: continue
    elif k in [1, 7]: vline_fill(x, TH_P, C_ROADP)
    elif k in sec_v: vline_fill(x, TH_S, C_ROADS)
    else: vline_fill(x, TH_T, C_ROADT)


# Paint the 100m border solid black (unassigned area)
rect(0, 0, S, 100, (0, 0, 0))
rect(0, S - 100, S, S, (0, 0, 0))
rect(0, 0, 100, S, (0, 0, 0))
rect(S - 100, 0, S, S, (0, 0, 0))

# Canals, reservoirs, and river removed as per request

img.save("outputs/zoning_map.png")
print("done: map generated with PLSS grid")

