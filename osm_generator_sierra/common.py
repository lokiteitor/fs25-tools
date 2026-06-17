"""Geometría y layout compartidos por los generadores del mapa 4096px de FS25.

Este módulo reúne la geometría y el layout simplificado para el nuevo mapa.
"""
# --- Lienzo / escala ---
S = 4096                      # canvas px
MILES = 4                     # millas reales de ancho (escala PLSS)
PPM = S / MILES               # px por milla = 1024


def m(x):
    """Millas -> pixeles (1 milla = 1024 px = 1024 m)."""
    return x * PPM


# --- Anchuras de carretera, bordes y separaciones (px) ---
TH_P = 22                     # grosor carretera principal
TH_S = 16                     # grosor carretera secundaria
TH_T = 8                      # grosor pista/track
W_FIELD_BORDER = 12           # borde negro de los campos
W_ROAD_BORDER = 12            # borde/margen negro de las carreteras
GAP = 40                      # separacion entre poligonos y carreteras

# Margen perimetral sin asignar (px).
BORDER = 25

# Posiciones (px) de las carreteras horizontales principales
hlines = [512, 3584]


def crosses_diagonal_forest(x0, y0, x1, y1):
    """No hay bosque diagonal en este layout."""
    return False


def build_northern_strip(parcels):
    """Tira norte (fila 0): [0, 512] - campos medianos."""
    for i in range(MILES):
        x0, y0 = m(i), 0
        x1, y1 = m(i + 1), m(0.5)
        if i == 0:
            # Sector 0: mitad izq = rectangulos 2x1; mitad der = cuadrados
            parcels.append((x0, y0, x0 + 512, y0 + 256))
            parcels.append((x0, y0 + 256, x0 + 512, y1))
            parcels.append((x0 + 512, y0, x0 + 768, y0 + 256))
            parcels.append((x0 + 512, y0 + 256, x0 + 768, y1))
        else:
            # Sectores 1-3: mitad izq = rect 2x1 + cuadrado 1x1
            parcels.append((x0, y0, x0 + 512, y0 + 256))
            parcels.append((x0, y0 + 256, x0 + 256, y1))
            # Mitad der = cuatro cuadrados 256x256
            parcels.append((x0 + 512, y0, x0 + 768, y0 + 256))
            parcels.append((x0 + 512, y0 + 256, x0 + 768, y1))
            parcels.append((x0 + 768, y0, x1, y0 + 256))
            parcels.append((x0 + 768, y0 + 256, x1, y1))


def build_southern_strip(parcels):
    """Tira sur: [3584, 4096] - campos medianos."""
    for i in range(MILES):
        x0, y0 = m(i), m(3.5)
        x1, y1 = m(i + 1), 4096
        if i == 3:
            # Sector 3: mitad izq = dos cuadrados 1x1
            parcels.append((x0 + 256, y0, x0 + 512, y0 + 256))
            parcels.append((x0 + 256, y0 + 256, x0 + 512, y1))
            # mitad der = dos rectangulos 2x1
            parcels.append((x0 + 512, y0, x1, y0 + 256))
            parcels.append((x0 + 512, y0 + 256, x1, y1))
        else:
            # Sectores 0-2: mitad izq = cuadrado 1x1 + rectangulo 2x1
            parcels.append((x0, y0, x0 + 256, y0 + 256))
            parcels.append((x0, y0 + 256, x0 + 512, y1))
            # Mitad der = cuatro cuadrados 256x256
            parcels.append((x0 + 512, y0, x0 + 768, y0 + 256))
            parcels.append((x0 + 512, y0 + 256, x0 + 768, y1))
            parcels.append((x0 + 768, y0, x1, y0 + 256))
            parcels.append((x0 + 768, y0 + 256, x1, y1))


# --- Pueblo ---
TOWN_X0 = m(1.0)
TOWN_Y0 = m(0.5)
TOWN_Y1 = m(1.0)
TOWN_WIDTH = 320
TOWN_X1 = TOWN_X0 + TOWN_WIDTH
TOWN_STREET_SPACING = 100
TOWN_VSTREETS = int(TOWN_WIDTH // TOWN_STREET_SPACING)   # verticales
TOWN_HSTREETS = 4                                         # horizontales

# Lista de granjas y áreas industriales (yards)
yards = [
    # Granja principal (Sureste)
    (3088, 3607, 3316, 4076),
    # Granja principal (Noroeste)
    (780, 24, 1008, 489),
    # Zonas industriales carretera norte (Oeste, Centro-Oeste, Centro-Este)
    (1292, 268, 1524, 489),
    (2316, 268, 2548, 489),
    (3340, 268, 3572, 489),
    # Zonas industriales carretera sur (Oeste, Centro-Oeste, Centro-Este)
    (268, 3607, 500, 3828),
    (1292, 3607, 1524, 3828),
    (2316, 3607, 2548, 3828),
]

import math

# Generate winding forest points along the plateau transition slope
IRREGULAR_FOREST_PTS = []
x_steps = list(range(50, 4047, 100))
if x_steps[-1] < 4046:
    x_steps.append(4046)

# Upper edge of the forest (from west to east)
for x in x_steps:
    y_boundary = 2048.0 + 400.0 * math.sin(2.0 * math.pi * (x + 2048) / 8192.0) + 100.0 * math.cos(2.0 * math.pi * (x + 2048) / 4096.0)
    y_upper = y_boundary - 400.0
    IRREGULAR_FOREST_PTS.append((float(round(x, 2)), float(round(y_upper, 2))))

# Lower edge of the forest (from east to west)
for x in reversed(x_steps):
    y_boundary = 2048.0 + 400.0 * math.sin(2.0 * math.pi * (x + 2048) / 8192.0) + 100.0 * math.cos(2.0 * math.pi * (x + 2048) / 4096.0)
    y_lower = y_boundary + 400.0
    IRREGULAR_FOREST_PTS.append((float(round(x, 2)), float(round(y_lower, 2))))

def get_forest_edge_y(x, side):
    """Calcula la coordenada Y del borde superior o inferior del bosque winding."""
    y_boundary = 2048.0 + 400.0 * math.sin(2.0 * math.pi * (x + 2048) / 8192.0) + 100.0 * math.cos(2.0 * math.pi * (x + 2048) / 4096.0)
    if side == 'upper':
        return y_boundary - 400.0
    else:
        return y_boundary + 400.0

# Posiciones de caminos de terraceria (de norte a sur) que van de caminos principales al bosque
NORTH_DIRT_ROADS_X = [600.0, 2700.0, 3500.0]
SOUTH_DIRT_ROADS_X = [800.0, 1800.0, 2600.0]

# Posiciones de caminos de terraceria horizontales (este-oeste)
NORTH_DIRT_ROAD_Y = 1050.0
SOUTH_DIRT_ROAD_Y = 3200.0

def build_middle_fields(parcels):
    """Crea los campos en las rejillas formadas por las terracerias y contornos usando poligonos."""
    import numpy as np
    from scipy.interpolate import CubicSpline

    # Re-create winding road path coordinates for calculating intersections
    y_control = np.array([752, 952, 1552, 2340, 2802, 3252, 3452], dtype=np.float32)
    x_control = np.array([3752, 3752, 2252, 852, 1452, 352, 352], dtype=np.float32)
    cs = CubicSpline(y_control, x_control, bc_type='natural')

    road_pts = []
    # 1. North connection (straight vertical from y=512 to y=752 at x=3752)
    for y_val in np.linspace(512, 752, 15):
        road_pts.append((3752.0, float(y_val)))

    # 2. Middle winding road (spline from y=752 to y=3452, skipping the first node because it's (3752, 752))
    for y_val in np.linspace(752, 3452, 150)[1:]:
        x_val = float(cs(y_val))
        road_pts.append((x_val, float(y_val)))

    # 3. South connection (straight vertical from y=3452 to y=3584 at x=352, skipping first)
    for y_val in np.linspace(3452, 3584, 15)[1:]:
        road_pts.append((352.0, float(y_val)))

    # --- SECTOR NORTE (y: 512 a bosque) ---
    # Fila superior (y: 512 a 1050) - rectangulos y poligonos con margenes
    parcels.append([(31.0, 535.0), (584.0, 535.0), (584.0, 1034.0), (31.0, 1034.0)])
    parcels.append([(616.0, 535.0), (1018.0, 535.0), (1018.0, 1034.0), (616.0, 1034.0)])
    parcels.append([(1350.0, 535.0), (2684.0, 535.0), (2684.0, 1034.0), (1350.0, 1034.0)])
    parcels.append([(2716.0, 535.0), (3484.0, 535.0), (3484.0, 1034.0), (2716.0, 1034.0)])

    # N5 (Between x=3500 and winding road)
    west_edge_pts = [(rx - 23.0, ry) for (rx, ry) in road_pts if ry >= 535.0 and ry <= 1034.0]
    parcels.append([(3516.0, 535.0)] + west_edge_pts + [(3516.0, 1034.0)])

    # N6 (Between winding road and east border)
    east_edge_pts = [(rx + 23.0, ry) for (rx, ry) in road_pts if ry >= 535.0 and ry <= 1034.0]
    parcels.append([(4065.0, 535.0), (4065.0, 1034.0)] + list(reversed(east_edge_pts)))

    # Fila inferior (y: 1050 al bosque)
    # N7 (Oeste)
    x_steps = np.linspace(584.0, 31.0, 5)
    bottom_n7 = [(x, get_forest_edge_y(x, 'upper') - 12) for x in x_steps]
    parcels.append([(31.0, 1066.0), (584.0, 1066.0)] + bottom_n7)

    # N8 (West of winding road, slice x in [616, 2684])
    west_road = [(rx - 23.0, ry) for (rx, ry) in road_pts if ry >= 1417.62 and ry <= 1979.12]
    x_steps_n8 = np.linspace(1020.83, 616.0, 5)
    bottom_n8 = [(x, get_forest_edge_y(x, 'upper') - 12) for x in x_steps_n8]
    parcels.append([(616.0, 1066.0), (2684.0, 1066.0), (2684.0, 1417.62)] + west_road + bottom_n8)

    # N9 (East of winding road, slice x in [616, 2684])
    east_road = [(rx + 23.0, ry) for (rx, ry) in road_pts if ry >= 1417.62 and ry <= 1979.12]
    x_steps_n9 = np.linspace(2716.0, 1066.83, 5)
    bottom_n9 = [(x, get_forest_edge_y(x, 'upper') - 12) for x in x_steps_n9]
    parcels.append([(2716.0, 1417.62)] + bottom_n9 + list(reversed(east_road)))

    # N10A (Above winding road, slice x in [2716, 3484])
    west_road_n10 = [(rx - 23.0, ry) for (rx, ry) in road_pts if ry >= 1130.85 and ry <= 1417.62]
    parcels.append([(2716.0, 1066.0), (3484.0, 1066.0), (3484.0, 1130.85)] + west_road_n10)

    # N10B (Below winding road, slice x in [2716, 3484])
    east_road_n10 = [(rx + 23.0, ry) for (rx, ry) in road_pts if ry >= 1130.85 and ry <= 1417.62]
    x_steps_n10 = np.linspace(3484.0, 2716.0, 5)
    bottom_n10 = [(x, get_forest_edge_y(x, 'upper') - 12) for x in x_steps_n10]
    parcels.append([(2716.0, 1417.62)] + list(reversed(east_road_n10)) + [(3484.0, 1130.85)] + bottom_n10)

    # N11A (West of winding road, slice x in [3516, 4065])
    west_road_n11 = [(rx - 23.0, ry) for (rx, ry) in road_pts if ry >= 1066.0 and ry <= 1130.85]
    parcels.append([(3516.0, 1066.0), (3598.0, 1066.0)] + west_road_n11)

    # N11B (East of winding road, slice x in [3516, 4065])
    east_road_n11 = [(rx + 23.0, ry) for (rx, ry) in road_pts if ry >= 1066.0 and ry <= 1130.85]
    x_steps_n11 = np.linspace(4065.0, 3516.0, 5)
    bottom_n11 = [(x, get_forest_edge_y(x, 'upper') - 12) for x in x_steps_n11]
    parcels.append([(3644.0, 1066.0), (4065.0, 1066.0)] + bottom_n11 + [(3516.0, 1130.85)] + list(reversed(east_road_n11)))


    # --- SECTOR SUR (y: bosque a 3584) ---
    # Fila superior (y: bosque a 3200)
    # S6A (West of winding road, slice x in [31, 784])
    west_road_s6 = [(rx - 23.0, ry) for (rx, ry) in road_pts if ry >= 3065.22 and ry <= 3184.0]
    x_steps_s6a = np.linspace(31.0, 784.0, 5)
    top_s6a = [(x, get_forest_edge_y(x, 'lower') + 12) for x in x_steps_s6a]
    parcels.append(top_s6a + [(784.0, 3065.22)] + west_road_s6 + [(31.0, 3184.0)])

    # S6B (East of winding road, slice x in [31, 784])
    east_road_s6 = [(rx + 23.0, ry) for (rx, ry) in road_pts if ry >= 3065.22 and ry <= 3184.0]
    parcels.append([(784.0, 3065.22), (784.0, 3184.0)] + list(reversed(east_road_s6)))

    # S7A (East of winding road, slice x in [816, 1784])
    east_road_s7 = [(rx + 23.0, ry) for (rx, ry) in road_pts if ry >= 2644.28 and ry <= 3065.22]
    x_steps_s7a = np.linspace(1412.91, 1784.0, 5)
    top_s7a = [(x, get_forest_edge_y(x, 'lower') + 12) for x in x_steps_s7a]
    parcels.append(top_s7a + [(1784.0, 3184.0), (816.0, 3184.0), (816.0, 3065.22)] + list(reversed(east_road_s7)))

    # S7B (West of winding road, slice x in [816, 1784])
    west_road_s7 = [(rx - 23.0, ry) for (rx, ry) in road_pts if ry >= 2644.28 and ry <= 3065.22]
    x_steps_s7b = np.linspace(816.0, 1366.91, 5)
    top_s7b = [(x, get_forest_edge_y(x, 'lower') + 12) for x in x_steps_s7b]
    parcels.append(top_s7b + west_road_s7 + [(816.0, 3065.22)])

    # S8 (Between x=1800 and x=2600)
    x_steps_s8 = np.linspace(1816.0, 2584.0, 5)
    top_s8 = [(x, get_forest_edge_y(x, 'lower') + 12) for x in x_steps_s8]
    parcels.append(top_s8 + [(2584.0, 3184.0), (1816.0, 3184.0)])

    # S9 (Between x=2600 and east border)
    x_steps_s9 = np.linspace(2616.0, 4065.0, 5)
    top_s9 = [(x, get_forest_edge_y(x, 'lower') + 12) for x in x_steps_s9]
    parcels.append(top_s9 + [(4065.0, 3184.0), (2616.0, 3184.0)])

    # Fila inferior (y: 3200 a 3584) - rectangulos con margenes
    # S11 (West of winding road, slice x in [31, 800])
    west_road_s11 = [(rx - 23.0, ry) for (rx, ry) in road_pts if ry >= 3216.0 and ry <= 3561.0]
    parcels.append([(31.0, 3216.0)] + west_road_s11 + [(31.0, 3561.0)])

    # S12 (East of winding road, slice x in [31, 800])
    east_road_s12 = [(rx + 23.0, ry) for (rx, ry) in road_pts if ry >= 3216.0 and ry <= 3561.0]
    parcels.append([(784.0, 3216.0), (784.0, 3561.0)] + list(reversed(east_road_s12)))

    # S13 (Between x=800 and x=1800)
    parcels.append([(816.0, 3216.0), (1784.0, 3216.0), (1784.0, 3561.0), (816.0, 3561.0)])

    # S14 (Between x=1800 and x=2600)
    parcels.append([(1816.0, 3216.0), (2584.0, 3216.0), (2584.0, 3561.0), (1816.0, 3561.0)])

    # S15 (Between x=2600 and east border)
    parcels.append([(2616.0, 3216.0), (4065.0, 3216.0), (4065.0, 3561.0), (2616.0, 3561.0)])

def split_block(parcels, x0, y0, x1, y1, depth, edge, near_town):
    """Subdivision recursiva tipo PLSS que va anyadiendo parcelas a `parcels`.
    
    Consume numeros aleatorios via `random`.
    """
    import random
    w = x1 - x0
    h = y1 - y0

    maxdepth = 1

    # Parada temprana para mezclar campos grandes y pequenyos
    if depth >= 1 and random.random() < 0.52:
        parcels.append((x0, y0, x1, y1))
        return

    if depth >= maxdepth or (w < m(0.15) or h < m(0.15)):
        parcels.append((x0, y0, x1, y1))
        return

    # Corte con ratio aleatorio para crear tamanyos diversos
    r = random.uniform(0.3, 0.7)
    if w >= h:
        xm = x0 + w * r
        split_block(parcels, x0, y0, xm, y1, depth + 1, edge, near_town)
        split_block(parcels, xm, y0, x1, y1, depth + 1, edge, near_town)
    else:
        ym = y0 + h * r
        split_block(parcels, x0, y0, x1, ym, depth + 1, edge, near_town)
        split_block(parcels, x0, ym, x1, y1, depth + 1, edge, near_town)

COL4_FIELDS = []
vlines = []

