# Generador de Mapas para FS25 y OSM (Variante 4096px 1:1 metros)

Este proyecto contiene una variante de las herramientas de generación de mapas diseñada para generar mapas de zonificación y datos vectoriales OpenStreetMap (OSM) para **Farming Simulator 25 (FS25)**, configurado a una resolución de **4096x4096 píxeles con una escala de 1:1 metros** (4096m x 4096m en total).

## Diferencias con la versión original

1. **Resolución y Escala**:
   - Escala de 4096 x 4096 píxeles.
   - Cada píxel equivale a 1 metro real (1:1).
   - El área se define como una cuadrícula PLSS de 4x4 millas (en comparación con las 8x8 de la original).

2. **Remoción de Sectores y Elementos**:
   - Se ha eliminado por completo el sector norte original (antigua fila `j = 0`).
   - Se eliminaron las vías del tren, el lago del norte, y todas las zonas industriales.
   - El pueblo (town) y el resto del mapa se han desplazado y ajustado hacia arriba para ocupar el espacio liberado en el norte.

3. **Optimización de Campos**:
   - Se ha reducido el número de campos (parcelas agrícolas y granjas) de forma proporcional para que quepan armoniosamente en el lienzo de 4096px sin congestionar el mapa.
   - El sector sur se ha reescalado a la nueva anchura, conservando campos circulares, cuadrados y campos en tiras en el este, pero con conteos reducidos.

---

## Estructura del Proyecto

| Script | Descripción | Salidas |
| :--- | :--- | :--- |
| [`genmap.py`](file:///home/ddelgado/git/lab/fs25-tools/osm_generator_4096/genmap.py) | Generador de Mapas | Imagen PNG de alta resolución (4096x4096 px) |
| [`genosm.py`](file:///home/ddelgado/git/lab/fs25-tools/osm_generator_4096/genosm.py) | Generador de Datos OSM | Archivo XML de OpenStreetMap (`.osm`) |

---

## Requisitos y Uso

### Requisitos

Asegúrate de tener instalado Python 3 y Pillow:

```bash
pip install pillow
```

### Ejecución

Puedes ejecutar los scripts para generar todos los mapas y datos:

1. **Generar la imagen de zonificación (Zoning Map)**:
   ```bash
   python3 genmap.py
   ```
2. **Generar los datos vectoriales OSM (OpenStreetMap XML)**:
   ```bash
   python3 genosm.py
   ```

Todos los resultados se guardarán automáticamente en el directorio [`outputs/`](file:///home/ddelgado/git/lab/fs25-tools/osm_generator_4096/outputs).

## Coordenadas de Referencia (OSM):
Center coordinates: (27.07991, -109.70707)
Distance from center: 2048.0 meters (Map Size: 4096x4096m)
Computed Bounding Box (W, S, E, N): (-109.7277558150625, 27.061491919529106, -109.6863841849375, 27.098328080470894)
