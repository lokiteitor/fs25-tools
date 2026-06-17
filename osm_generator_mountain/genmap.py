import random
from PIL import Image, ImageDraw

from common import (
    S, MILES, PPM, m,
    TH_P, TH_S, TH_T, W_FIELD_BORDER, W_ROAD_BORDER, GAP, BORDER,
    hlines, yards,
    build_northern_strip, build_southern_strip,
    TOWN_X0, TOWN_X1, TOWN_Y0, TOWN_Y1, TOWN_STREET_SPACING,
    TOWN_VSTREETS, TOWN_HSTREETS, COL4_FIELDS,
    IRREGULAR_FOREST_PTS, get_forest_edge_y,
    NORTH_DIRT_ROADS_X, SOUTH_DIRT_ROADS_X,
    NORTH_DIRT_ROAD_Y, SOUTH_DIRT_ROAD_Y,
    build_middle_fields,
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
parcels = []

# 1. Northern strip (Row 0): [0, 512] - Medium farmlands
build_northern_strip(parcels)

# 2. Middle grid fields (bounded by roads and contours)
build_middle_fields(parcels)

# 3. Southern strip: [3584, 4096] - Medium farmlands
build_southern_strip(parcels)

# Draw farmland parcels (handles both rectangular and polygon parcels)
for p in parcels:
    if isinstance(p, list) or (isinstance(p, tuple) and len(p) > 4):
        # It's a polygon!
        d.polygon(p, fill=C_FARM)
        d.line(p + [p[0]], fill=C_FARMB, width=W_FIELD_BORDER, joint="round")
    else:
        # It's a rectangle!
        x0, y0, x1, y1 = p
        cx0 = max(BORDER, x0)
        cy0 = max(BORDER, y0)
        cx1 = min(S - BORDER, x1)
        cy1 = min(S - BORDER, y1)
        if cx1 - cx0 > 20 and cy1 - cy0 > 20:
            rect(cx0, cy0, cx1, cy1, C_FARM, outline=C_FARMB, width=W_FIELD_BORDER)

# ================= FOREST =================
if len(IRREGULAR_FOREST_PTS) > 0:
    d.line(IRREGULAR_FOREST_PTS + [IRREGULAR_FOREST_PTS[0]], fill=C_FARMB, width=24, joint="round")
    d.polygon(IRREGULAR_FOREST_PTS, fill=C_FOREST)

# ================= ROAD WIDTHS AND HELPERS =================

def hline_outline(y,th):
    rect(0,y-th/2-W_ROAD_BORDER,S,y+th/2+W_ROAD_BORDER,C_FARMB)

def hline_fill(y,th,col):
    rect(0,y-th/2,S,y+th/2,col)

# 1. Draw road outlines first (only horizontal roads y=512 and y=3584)
for y in hlines:
    hline_outline(y, TH_P)

# Generate winding mountain road coordinates (relative coordinates scaled from 8K DEM)
from scipy.interpolate import CubicSpline
import numpy as np
y_control = np.array([1152, 1552, 1952, 2352, 2752], dtype=np.float32)
x_control = np.array([1452, 2352, 1952, 3152, 3752], dtype=np.float32)
cs = CubicSpline(y_control, x_control, bc_type='clamped')

# 1. North connection (straight vertical from y=512 to y=1152)
road_pts = [(1452.0, y) for y in np.linspace(512, 1152, 200)]

# 2. Middle winding road (spline from y=1152 to y=2752)
Y_mid = np.linspace(1152, 2752, 1000, dtype=np.float32)
X_mid = cs(Y_mid).astype(np.float32)
road_pts.extend([(x, y) for x, y in zip(X_mid, Y_mid)])

# 3. South connection (straight vertical from y=2752 to y=3584)
road_pts.extend([(3752.0, y) for y in np.linspace(2752, 3584, 200)])

# Draw winding road outline
d.line(road_pts, fill=C_FARMB, width=TH_P + 2*W_ROAD_BORDER, joint="round")

# Draw dirt road outlines (thickness TH_T + 2*W_ROAD_BORDER)
for x in NORTH_DIRT_ROADS_X:
    y_end = get_forest_edge_y(x, 'upper')
    d.line([(x, 512), (x, y_end)], fill=C_FARMB, width=TH_T + 2*W_ROAD_BORDER, joint="round")
for x in SOUTH_DIRT_ROADS_X:
    y_end = get_forest_edge_y(x, 'lower')
    d.line([(x, 3584), (x, y_end)], fill=C_FARMB, width=TH_T + 2*W_ROAD_BORDER, joint="round")

# Draw horizontal dirt road outlines
d.line([(BORDER, NORTH_DIRT_ROAD_Y), (S - BORDER, NORTH_DIRT_ROAD_Y)], fill=C_FARMB, width=TH_T + 2*W_ROAD_BORDER, joint="round")
d.line([(BORDER, SOUTH_DIRT_ROAD_Y), (S - BORDER, SOUTH_DIRT_ROAD_Y)], fill=C_FARMB, width=TH_T + 2*W_ROAD_BORDER, joint="round")

# ================= TOWN =================
# Draw residential block
rect(TOWN_X0, TOWN_Y0, TOWN_X1, TOWN_Y1, C_RES)

# Town streets: 100m x 100m blocks
sw = 3
for k in range(1, TOWN_VSTREETS + 1):
    x = TOWN_X0 + k * TOWN_STREET_SPACING
    rect(x-sw/2, TOWN_Y0 + 10, x+sw/2, TOWN_Y1, C_RESST)
for k in range(1, TOWN_HSTREETS + 1):
    y = TOWN_Y0 + k * TOWN_STREET_SPACING
    rect(TOWN_X0 + 10, y-sw/2, TOWN_X1, y+sw/2, C_RESST)

# ================= YARDS =================
for (x0, y0, x1, y1) in yards:
    rect(x0, y0, x1, y1, C_YARD, outline=C_YARDB, width=5)

# ================= DRAW ROAD FILLS =================
# Draw road fills on top
for y in hlines:
    hline_fill(y, TH_P, C_ROADP)

# Draw winding road fill
d.line(road_pts, fill=C_ROADP, width=TH_P, joint="round")

# Draw dirt road fills (color C_ROADT, thickness TH_T)
for x in NORTH_DIRT_ROADS_X:
    y_end = get_forest_edge_y(x, 'upper')
    d.line([(x, 512), (x, y_end)], fill=C_ROADT, width=TH_T, joint="round")
for x in SOUTH_DIRT_ROADS_X:
    y_end = get_forest_edge_y(x, 'lower')
    d.line([(x, 3584), (x, y_end)], fill=C_ROADT, width=TH_T, joint="round")

# Draw horizontal dirt road fills
d.line([(BORDER, NORTH_DIRT_ROAD_Y), (S - BORDER, NORTH_DIRT_ROAD_Y)], fill=C_ROADT, width=TH_T, joint="round")
d.line([(BORDER, SOUTH_DIRT_ROAD_Y), (S - BORDER, SOUTH_DIRT_ROAD_Y)], fill=C_ROADT, width=TH_T, joint="round")

# Paint the 25m border solid black
rect(0, 0, S, BORDER, (0, 0, 0))
rect(0, S - BORDER, S, S, (0, 0, 0))
rect(0, 0, BORDER, S, (0, 0, 0))
rect(S - BORDER, 0, S, S, (0, 0, 0))

img.save("outputs/zoning_map.png")
print("done: map generated with PLSS grid (simplified)")
