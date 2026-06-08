import random
import math
from PIL import Image, ImageDraw

random.seed(20240605)

S = 4096                      # canvas px
MILES = 4                     # real miles across (PLSS scale)
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
W_FIELD_BORDER = 12           # Thicker black lines for fields (originally 1)
GAP = 40                      # Greater separation between polygons and roads (originally 5 for yards)
W_ROAD_BORDER = 12            # Black border/margin for roads

img = Image.new("RGB",(S,S),C_FARM)
d = ImageDraw.Draw(img)

def rect(x0,y0,x1,y1,fill,outline=None,width=0):
    d.rectangle([x0,y0,x1,y1],fill=fill,outline=outline,width=width)

# ================= FIELDS (Farmland Parcels) =================
# Subdivide sections into rectangular fields using PLSS binary subdivisions.
# Town block is skipped.
def in_town(cx, cy):
    return m(1) <= cx < m(2) and m(0.5) <= cy < m(1)

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
        continue
    split_block(x0, y0, x1, y1, 0, True, True)

# Row 2: [1024, 2048]
for i in range(MILES):
    x0, y0 = m(i), m(1.0)
    x1, y1 = m(i+1), m(2.0)
    if crosses_diagonal_forest(x0, y0, x1, y1):
        continue
    split_block(x0, y0, x1, y1, 0, True, True)

# Row 3: [2048, 3072]
for i in range(MILES):
    x0, y0 = m(i), m(2.0)
    x1, y1 = m(i+1), m(3.0)
    if crosses_diagonal_forest(x0, y0, x1, y1):
        continue
    split_block(x0, y0, x1, y1, 0, True, True)

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

# Draw farmland parcels with a simple single dividing line (no margins, W_FIELD_BORDER px border)
C_FARMB = (0,0,0)

for (x0, y0, x1, y1) in parcels:
    cx0 = max(20, x0)
    cy0 = max(20, y0)
    cx1 = min(S - 20, x1)
    cy1 = min(S - 20, y1)
    if cx1 - cx0 > 20 and cy1 - cy0 > 20:
        rect(cx0, cy0, cx1, cy1, C_FARM, outline=C_FARMB, width=W_FIELD_BORDER)

# Column 4 Row 2 Circular Field
cx = 3072 + 512
cy = 1024 + 512
R = 472
d.ellipse([cx - R, cy - R, cx + R, cy + R], fill=C_FARM, outline=C_FARMB, width=W_FIELD_BORDER)

# Southern zone fields removed


# Merge a few adjacent parcels to create L-shaped fields by erasing their shared boundary
def draw_L():
    if len(parcels) < 2: return
    a = random.choice(parcels)
    cx = (a[0] + a[2]) / 2
    cy = (a[1] + a[3]) / 2
    if a[1] < m(0.5) or a[3] > m(3.5): # Avoid merging fields in northern/southern farmland strips
        return
    if not (cx < m(2) and cy < m(2)):
        return
    for b in parcels:
        if b is a: continue
        if b[1] < m(0.5) or b[3] > m(3.5): continue
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

for _ in range(5):
    draw_L()


# ================= ROAD WIDTHS AND HELPERS =================

def hline_outline(y,th):
    rect(0,y-th/2-W_ROAD_BORDER,S,y+th/2+W_ROAD_BORDER,C_FARMB)

def vline_outline(x,th):
    rect(x-th/2-W_ROAD_BORDER,0,x+th/2+W_ROAD_BORDER,m(3.5)+W_ROAD_BORDER,C_FARMB)

def hline_fill(y,th,col):
    rect(0,y-th/2,S,y+th/2,col)

def vline_fill(x,th,col):
    rect(x-th/2,0,x+th/2,m(3.5),col)

# Set up road coordinates
hlines = [512, 1024, 2048, 3584]
vlines = [m(i) for i in range(MILES+1)]

# 1. Draw all road outlines/margins first
for y in hlines:
    if y == 512 or y == 3584: hline_outline(y, TH_P)
    else: hline_outline(y, TH_T)

for k, x in enumerate(vlines):
    if k == 0 or k == MILES: continue
    else: vline_outline(x, TH_T)

# Diagonal primary road outline (starts at y=512, ends at y=3584)
road_pts = []
for y_px in range(512, int(m(3.5)) + 1, 4):
    road_pts.append((get_road_x(y_px), y_px))

d.line(road_pts, fill=C_FARMB, width=TH_P + 2*W_ROAD_BORDER, joint="round")

# Draw southern vertical track road connecting horizontal road y=2048 to y=3584
d.line([(2445, 2048), (2445, 3584)], fill=C_FARMB, width=TH_T + 2*W_ROAD_BORDER, joint="round")


# ================= TOWN (1x1 mile Section, rectangular hugging the primary road) =================
TOWN_X0, TOWN_X1, TOWN_Y0, TOWN_Y1 = m(1), m(2), m(0.5), m(1)

# Draw rectangular town hugging the primary road at y=512
rect(m(1.0), m(0.5), m(1.625), m(1.0), C_RES)

# Town yard replaced by farmland

# Town streets: 100m x 100m blocks
sw = 3
for k in range(1, 7):
    x = TOWN_X0 + k * 100
    rect(x-sw/2, TOWN_Y0 + 10, x+sw/2, m(1.0), C_RESST)
for k in range(1, 5):
    y = TOWN_Y0 + k * 100
    rect(TOWN_X0 + 10, y-sw/2, m(1.625), y+sw/2, C_RESST)

# ================= FORESTS (pegged to roads) =================

# Forest surrounding diagonal road with 50m (32px) black margin and curved boundaries
margin_pts = []
forest_pts = []
for y_px in range(512, int(m(3.5)) + 1, 4):
    xc = get_road_x(y_px)
    margin_pts.append((min(S - 20.0, xc + 350.0), y_px))
    forest_pts.append((min(S - 20.0, xc + 318.0), y_px))

for y_px in range(int(m(3.5)), 511, -4):
    xc = get_road_x(y_px)
    margin_pts.append((max(20.0, xc - 350.0), y_px))
    forest_pts.append((max(20.0, xc - 318.0), y_px))

# Draw black margin first
d.polygon(margin_pts, fill=C_FARMB)
# Draw forest on top
d.polygon(forest_pts, fill=C_FOREST)

# Southern forest removed

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

for (x0, y0, x1, y1) in yards:
    rect(x0, y0, x1, y1, C_YARD, outline=C_YARDB, width=5)


# ================= DRAW ROAD FILLS =================
# 2. Draw all road fills on top
for y in hlines:
    if y == 512 or y == 3584: hline_fill(y, TH_P, C_ROADP)
    else: hline_fill(y, TH_T, C_ROADT)

for k, x in enumerate(vlines):
    if k == 0 or k == MILES: continue
    else: vline_fill(x, TH_T, C_ROADT)

# Draw diagonal primary road fill
d.line(road_pts, fill=C_ROADP, width=TH_P, joint="round")

# Draw southern vertical track road fill
d.line([(2445, 2048), (2445, 3584)], fill=C_ROADT, width=TH_T, joint="round")


# Paint the 20m border solid black (unassigned area)
rect(0, 0, S, 20, (0, 0, 0))
rect(0, S - 20, S, S, (0, 0, 0))
rect(0, 0, 20, S, (0, 0, 0))
rect(S - 20, 0, S, S, (0, 0, 0))

img.save("outputs/zoning_map.png")
print("done: map generated with PLSS grid")
