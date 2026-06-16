"""Geometría y layout compartidos por los generadores del mapa 4096px de FS25.

`genmap.py` (imagen PNG) y `genosm.py` (datos vectoriales OSM) construyen el
mismo mapa estilo PLSS de 4096x4096 px / 4x4 millas (escala 1:1 m). Este módulo
reúne la geometría y el layout que deben permanecer idénticos entre ambos para
que la imagen raster y los datos vectoriales queden perfectamente alineados.

Las divergencias deliberadas (p. ej. cómo trata cada script las parcelas que
cruzan el bosque diagonal) se mantienen en cada script, no aquí.
"""
import math

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

# Margen perimetral sin asignar (px). El contenido del mapa (campos, bosque,
# carreteras) se mantiene dentro de [BORDER, S-BORDER]. Antes el borde eran 35
# px (10 de bosque + 25 negros); ahora son 25 px vacios, sin anillo de bosque.
BORDER = 25

# Posiciones (px) de las carreteras horizontales
hlines = [512, 1024, 2048, 3584]


def get_road_x(y):
    """X (px) de la carretera principal diagonal/curva para una y (px) dada."""
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
    """True si el bloque (x0,y0,x1,y1) choca con el bosque de la diagonal."""
    if y1 <= m(0.5) or y0 >= m(3.5):
        return False
    y_start = max(y0, m(0.5))
    y_end = min(y1, m(3.5))
    for y in [y_start, (y_start + y_end) / 2, y_end]:
        rx = get_road_x(y)
        if x0 - 350 <= rx <= x1 + 350:
            return True
    return False


def find_intersection_y(target_x):
    """Y (px) donde la carretera diagonal alcanza target_x (px)."""
    low = m(0.5)
    high = m(3.5)
    mid = (low + high) / 2
    for _ in range(20):
        mid = (low + high) / 2
        x = get_road_x(mid)
        if x > target_x:
            low = mid
        else:
            high = mid
    return mid


def in_town(cx, cy):
    """True si el centro (cx,cy) cae dentro de la seccion del pueblo."""
    return m(1) <= cx < m(2) and m(0.5) <= cy < m(1)


def split_block(parcels, x0, y0, x1, y1, depth, edge, near_town):
    """Subdivision recursiva tipo PLSS que va anyadiendo parcelas a `parcels`.

    Consume numeros aleatorios via `random`; el orden de consumo es relevante
    para reproducir la salida, asi que NO cambiar la logica sin re-validar.
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


def build_northern_strip(parcels):
    """Tira norte (fila 0): [0, 512] - campos medianos. No usa aleatoriedad."""
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
    """Tira sur: [3584, 4096] - campos medianos. No usa aleatoriedad."""
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


# --- Pueblo: bloque residencial pegado a la carretera principal (y=512 px) ---
# Ancho reducido a la mitad respecto al original (640 -> 320 px); alto sin
# cambios (512 px). El espacio liberado a la derecha pasa a ser cultivo.
TOWN_X0 = m(1.0)
TOWN_Y0 = m(0.5)
TOWN_Y1 = m(1.0)
TOWN_WIDTH = 320
TOWN_X1 = TOWN_X0 + TOWN_WIDTH
TOWN_STREET_SPACING = 100
# Calles internas (una cada TOWN_STREET_SPACING px).
TOWN_VSTREETS = int(TOWN_WIDTH // TOWN_STREET_SPACING)   # verticales (a lo ancho)
TOWN_HSTREETS = 4                                         # horizontales (fijo)


# --- Campos de la columna 4, fila 2 ---
# Sustituyen al antiguo campo circular por dos campos que rellenan toda la
# celda de la cuadricula (x [m(3), m(4)], y [m(1), m(2)]). El lado
# oeste lo recorta el bosque diagonal (el pipeline de clipping genera la
# curva), por lo que no son rectangulos perfectos. (x0, y0, x1, y1) en px.
COL4_FIELDS = [
    (m(3), m(1.0), m(4), m(1.5)),   # campo norte (mitad superior de la celda)
    (m(3), m(1.5), m(4), m(2.0)),   # campo sur   (mitad inferior de la celda)
]


# --- Granjas / zonas industriales (rectangulos px) ---
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

# --- Bosque Irregular (Columna 1, Fila 3, cerca del ecuador - representa una colina con bosque) ---
IRREGULAR_FOREST_PTS = [
    (25, 2080),
    (200, 2060),
    (400, 2120),
    (450, 2250),
    (460, 2400),
    (420, 2600),
    (350, 2750),
    (200, 2820),
    (25, 2780)
]
