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
    y_upper = y_boundary - 350.0
    IRREGULAR_FOREST_PTS.append((float(round(x, 2)), float(round(y_upper, 2))))

# Lower edge of the forest (from east to west)
for x in reversed(x_steps):
    y_boundary = 2048.0 + 400.0 * math.sin(2.0 * math.pi * (x + 2048) / 8192.0) + 100.0 * math.cos(2.0 * math.pi * (x + 2048) / 4096.0)
    y_lower = y_boundary + 350.0
    IRREGULAR_FOREST_PTS.append((float(round(x, 2)), float(round(y_lower, 2))))
COL4_FIELDS = []
vlines = []
