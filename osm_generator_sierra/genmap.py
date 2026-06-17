import random
from PIL import Image, ImageDraw

from common import (
    S, MILES, PPM, m,
    TH_P, TH_S, TH_T, W_FIELD_BORDER, W_ROAD_BORDER, GAP, BORDER,
    hlines, yards,
    get_road_x, crosses_diagonal_forest, in_town, split_block,
    build_northern_strip, build_southern_strip,
    TOWN_X0, TOWN_X1, TOWN_Y0, TOWN_Y1, TOWN_STREET_SPACING,
    TOWN_VSTREETS, TOWN_HSTREETS, COL4_FIELDS,
    IRREGULAR_FOREST_PTS,
)

random.seed(20240605)

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

img = Image.new("RGB",(S,S),C_FARM)
d = ImageDraw.Draw(img)

def rect(x0,y0,x1,y1,fill,outline=None,width=0):
    d.rectangle([x0,y0,x1,y1],fill=fill,outline=outline,width=width)

# ================= FIELDS (Farmland Parcels) =================
# Subdivide sections into rectangular fields using PLSS binary subdivisions.
# Town block is skipped.
parcels = []

# 1. Northern strip (Row 0): [0, 512] - Medium farmlands
build_northern_strip(parcels)

# 2. Main grid rows:
# Row 1: [512, 1024]
for i in range(MILES):
    if i == 1:
        # Town section: town itself is at [TOWN_X0, TOWN_X1], the rest is farmland
        split_block(parcels, TOWN_X1, m(0.5), m(2.0), m(1.0), 0, True, True)
        continue
    x0, y0 = m(i), m(0.5)
    x1, y1 = m(i+1), m(1.0)
    if crosses_diagonal_forest(x0, y0, x1, y1):
        continue
    split_block(parcels, x0, y0, x1, y1, 0, True, True)

# Row 2: [1024, 2048]
for i in range(MILES):
    x0, y0 = m(i), m(1.0)
    x1, y1 = m(i+1), m(2.0)
    if i == 3:
        # Columna 4: dos campos que rellenan toda la celda (el bosque recorta el oeste)
        parcels.extend(COL4_FIELDS)
        continue
    if crosses_diagonal_forest(x0, y0, x1, y1):
        continue
    split_block(parcels, x0, y0, x1, y1, 0, True, True)

# Row 3: [2048, 3072]
for i in range(MILES):
    x0, y0 = m(i), m(2.0)
    x1, y1 = m(i+1), m(3.0)
    if crosses_diagonal_forest(x0, y0, x1, y1):
        continue
    split_block(parcels, x0, y0, x1, y1, 0, True, True)

# 3. Southern strip: [3584, 4096] - Medium farmlands
build_southern_strip(parcels)

# Draw farmland parcels with a simple single dividing line (no margins, W_FIELD_BORDER px border)
C_FARMB = (0,0,0)

for (x0, y0, x1, y1) in parcels:
    cx0 = max(BORDER, x0)
    cy0 = max(BORDER, y0)
    cx1 = min(S - BORDER, x1)
    cy1 = min(S - BORDER, y1)
    if cx1 - cx0 > 20 and cy1 - cy0 > 20:
        rect(cx0, cy0, cx1, cy1, C_FARM, outline=C_FARMB, width=W_FIELD_BORDER)

# Column 4 Row 2 fields are generated with the parcels above (clipped by the forest)

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

# Draw new western vertical track road connecting horizontal road y=2048 to y=3584
d.line([(512, 2048), (512, 3584)], fill=C_FARMB, width=TH_T + 2*W_ROAD_BORDER, joint="round")


# ================= TOWN (rectangular block hugging the primary road) =================
# Draw rectangular town hugging the primary road at y=512
rect(TOWN_X0, TOWN_Y0, TOWN_X1, TOWN_Y1, C_RES)

# Town yard replaced by farmland

# Town streets: 100m x 100m blocks
sw = 3
for k in range(1, TOWN_VSTREETS + 1):
    x = TOWN_X0 + k * TOWN_STREET_SPACING
    rect(x-sw/2, TOWN_Y0 + 10, x+sw/2, TOWN_Y1, C_RESST)
for k in range(1, TOWN_HSTREETS + 1):
    y = TOWN_Y0 + k * TOWN_STREET_SPACING
    rect(TOWN_X0 + 10, y-sw/2, TOWN_X1, y+sw/2, C_RESST)

# ================= FORESTS (pegged to roads) =================

# Forest surrounding diagonal road with 50m (32px) black margin and curved boundaries
margin_pts = []
forest_pts = []
for y_px in range(512, int(m(3.5)) + 1, 4):
    xc = get_road_x(y_px)
    margin_pts.append((min(S - BORDER, xc + 350.0), y_px))
    forest_pts.append((min(S - BORDER, xc + 318.0), y_px))

for y_px in range(int(m(3.5)), 511, -4):
    xc = get_road_x(y_px)
    margin_pts.append((max(BORDER, xc - 350.0), y_px))
    forest_pts.append((max(BORDER, xc - 318.0), y_px))

# Draw black margin first
d.polygon(margin_pts, fill=C_FARMB)
# Draw forest on top
d.polygon(forest_pts, fill=C_FOREST)

# Southern forest removed

# Perimeter forest border removed: the edge is now a plain 25m margin (see below)

# Draw new irregular forest in Column 1 Row 3 near the equator
# Draw the black outline of the forest first
d.line(IRREGULAR_FOREST_PTS + [IRREGULAR_FOREST_PTS[0]], fill=C_FARMB, width=24, joint="round")
# Draw the forest polygon on top
d.polygon(IRREGULAR_FOREST_PTS, fill=C_FOREST)

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

# Draw new western vertical track road fill
d.line([(512, 2048), (512, 3584)], fill=C_ROADT, width=TH_T, joint="round")


# Paint the 25m border solid black (unassigned area, from edge: 0 to BORDER)
rect(0, 0, S, BORDER, (0, 0, 0))
rect(0, S - BORDER, S, S, (0, 0, 0))
rect(0, 0, BORDER, S, (0, 0, 0))
rect(S - BORDER, 0, S, S, (0, 0, 0))

img.save("outputs/zoning_map.png")
print("done: map generated with PLSS grid")
