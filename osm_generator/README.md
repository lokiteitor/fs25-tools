# Generador de Mapas y Terrenos para FS25 y OSM

Este proyecto contiene una suite de herramientas en Python diseñadas para generar mapas de zonificación, datos vectoriales OpenStreetMap (OSM) y mapas de elevación digital (DEM) para **Farming Simulator 25 (FS25)**, utilizando un sistema de cuadrícula PLSS (Public Land Survey System) de 8x8 millas.

## Estructura del Proyecto

El proyecto se compone de tres herramientas principales:

| Script | Descripción | Entradas / Características | Salidas |
| :--- | :--- | :--- | :--- |
| [`gendem.py`](file:///home/ddelgado/git/osm_generator/gendem.py) | Generador de Terrenos | Ruido fractal de múltiples octavas + pendiente macro de NE a SO | Mapas de elevación en 16 bits y vista previa de 8 bits |
| [`genmap.py`](file:///home/ddelgado/git/osm_generator/genmap.py) | Generador de Mapas | Subdivisión PLSS recursiva de parcelas agrícolas, red de caminos, canales, zonas urbanas e industriales | Imagen PNG de alta resolución (8192x8192 px) |
| [`genosm.py`](file:///home/ddelgado/git/osm_generator/genosm.py) | Generador de Datos OSM | Exportación de la misma topología a formato XML de OpenStreetMap (.osm) georreferenciado | Archivo XML de OpenStreetMap (.osm) |

---

## Detalle de las Herramientas

### 1. Generador de Terrenos (`gendem.py`)

Este script genera mapas de altura de 16 bits (DEM) requeridos por el motor GIANTS Engine de **Farming Simulator 25**, utilizando una resolución exacta de $8193 \times 8193$ píxeles ($(8192 \text{ px de mapa} + 1)$).

* **Algoritmo**: Genera una pendiente macro desde el Noreste (alto) hacia el Suroeste (bajo) combinada con un ruido fractal multi-octava (6 octavas de ruido interpoladas mediante coseno para formas suaves y detalladas).
* **Salidas generadas**:
  * [`outputs/dem.png`](file:///home/ddelgado/git/osm_generator/outputs/dem.png): Mapa de elevación escalado directamente para alturas entre 200m y 220m (asumiendo `heightScale="220"` en la configuración del mapa).
  * [`outputs/dem_full_range.png`](file:///home/ddelgado/git/osm_generator/outputs/dem_full_range.png): Mapa de elevación a rango completo (0-65535). Requiere configurar `heightScale="20"` y una traslación vertical de 200m en GIANTS Editor.
  * [`outputs/dem_view.png`](file:///home/ddelgado/git/osm_generator/outputs/dem_view.png): Una versión de 8 bits (L) para previsualización rápida en visualizadores estándar de imágenes.

### 2. Generador de Mapas (`genmap.py`)

Visualiza y renderiza el diseño catastral y de zonificación en una imagen PNG de alta resolución ($8192 \times 8192$ píxeles).

* **Estructura de Cuadrícula (PLSS)**: Define un área de 8x8 millas (secciones de 1x1 milla cada una).
* **Características**:
  * **Parcelas Agrícolas**: Subdivisión binaria recursiva de secciones en parcelas rectangulares. Los bloques cercanos al pueblo tienen más subdivisiones (campos pequeños) y los bordes tienen menos (campos grandes). Algunos campos adyacentes se fusionan aleatoriamente para crear formas en "L".
  * **Cuerpo de Agua y Canales**: Incluye un embalse artificial en el este del pueblo y canales de agua de 26 píxeles de ancho a lo largo de las carreteras principales.
  * **Pueblo (Town)**: Ocupa una sección completa de 1x1 milla, con una cuadrícula urbana interna de 8x8 bloques (7 calles internas en cada dirección).
  * **Bosques**: 3 grandes bosques rectangulares integrados en la cuadrícula de caminos.
  * **Granjas y Zonas Industriales**: 5 granjas (farmyards) ubicadas estratégicamente a lo largo de carreteras primarias y 2 zonas industriales con calles internas de servicio.
  * **Invernaderos**: Un sector especializado al noreste con 4 invernaderos de cristal detallados.
* **Salida generada**:
  * [`outputs/zoning_map.png`](file:///home/ddelgado/git/osm_generator/outputs/zoning_map.png)

### 3. Generador de Datos OSM (`genosm.py`)

Convierte y exporta la misma distribución espacial y topología definida en el generador de mapas directamente a un formato vectorial XML estándar de OpenStreetMap (`.osm`).

* **Georreferenciación**: Centrado en coordenadas GPS reales `(27.07991, -109.70707)` (Sonora, México).
* **Características**:
  * **Recorte Geométrico Limpio**: Implementa un algoritmo de sustracción rectangular recursivo (`subtract_rects`) para recortar las parcelas de cultivo donde se solapan con otros elementos (pueblos, bosques, embalses, granjas, etc.), garantizando que no haya geometrías duplicadas o superpuestas.
  * **Conectividad Topológica**: Los caminos horizontales y verticales están conectados correctamente mediante nodos compartidos en las intersecciones.
  * **Etiquetado OSM Estándar**: Cada elemento exportado incluye sus etiquetas semánticas (`landuse=farmland`, `highway=primary`, `waterway=canal`, `building=greenhouse`, etc.).
* **Salida generada**:
  * [`outputs/zoning_map.osm`](file:///home/ddelgado/git/osm_generator/outputs/zoning_map.osm)

---

## Requisitos y Uso

### Requisitos

Asegúrate de tener instalado Python 3 y las siguientes dependencias:

```bash
pip install pillow numpy
```

### Ejecución

Puedes ejecutar los scripts en orden para generar todos los mapas y datos:

1. **Generar los mapas de elevación (DEM)**:
   ```bash
   python gendem.py
   ```
2. **Generar la imagen de zonificación (Zoning Map)**:
   ```bash
   python genmap.py
   ```
3. **Generar los datos vectoriales OSM (OpenStreetMap XML)**:
   ```bash
   python genosm.py
   ```

Todos los resultados se guardarán automáticamente en el directorio [`outputs/`](file:///home/ddelgado/git/osm_generator/outputs).


## DEM parameters:
Center coordinates: (27.07991, -109.70707)
Distance from center: 4096.0 meters (Map Size: 8192x8192m)
Computed Bounding Box (W, S, E, N): (-109.748441630125, 27.043073839058213, -109.665698369875, 27.11674616094179)

