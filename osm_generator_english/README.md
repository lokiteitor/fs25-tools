# Generador de Mapas de Zonificación y OSM (Layout Inglés Orgánico - 4096px 1:1 metros)

Este subproyecto contiene un generador de mapas y datos vectoriales OpenStreetMap (OSM) para **Farming Simulator 25 (FS25)** configurado para generar un **diseño inglés (UK/European layout)**, caracterizado por parcelas agrícolas orgánicas e irregulares, caminos sinuosos y pueblos de trazado curvo.

## Características Principales (Diseño Inglés)

1. **Campos Irregulares y Orgánicos**:
   - Se reemplaza la cuadrícula rígida de estilo americano (PLSS) por una **cuadrícula de coordenadas perturbada aleatoriamente**.
   - Los campos de cultivo se generan como cuadriláteros irregulares divididos recursivamente según su cercanía al pueblo, emulando la distribución de parcelas de la campiña del Reino Unido.
   - **Sin campos circulares**: Todos los campos agrícolas respetan el diseño poligonal irregular.

2. **Caminos Sinuosos**:
   - Los caminos principales y pistas discurren siguiendo las distorsiones de la cuadrícula, serpenteando de forma natural por el mapa.
   - Las intersecciones comparten nodos exactos, garantizando la consistencia topológica en los datos vectoriales OSM.

3. **Pueblo (Town) y Granjas (`yards`)**:
   - El pueblo se genera en formato de "pueblo lineal" o lineal de carretera (estilo inglés *ribbon development*) a lo largo de un tramo de la vía principal sinuosa.
   - Las parcelas residenciales se organizan a ambos lados de la carretera principal con espacios intermedios y pequeñas calles sin salida (cul-de-sacs) que crean bifurcaciones con casas adicionales.
   - Las granjas (farmyards) y zonas industriales están integradas como subdivisiones de las celdas de la cuadrícula. Todos los campos de cultivo y bosques se recortan dinámicamente mediante un algoritmo vectorial de distancias para respetar la separación con los caminos y las parcelas del pueblo, previniendo solapamientos.

---

## Estructura del Directorio

| Script | Descripción | Salida |
| :--- | :--- | :--- |
| [`genmap.py`](file:///home/ddelgado/git/lab/fs25-tools/osm_generator_english/genmap.py) | Generador de Imagen PNG | Genera el mapa de zonificación de 4096x4096px en `outputs/zoning_map.png` |
| [`genosm.py`](file:///home/ddelgado/git/lab/fs25-tools/osm_generator_english/genosm.py) | Generador de XML OSM | Genera el archivo vectorial OpenStreetMap en `outputs/zoning_map.osm` |

---

## Requisitos y Uso

### Requisitos

Asegúrate de tener instalado Python 3 y Pillow:

```bash
pip install pillow
```

### Ejecución

Puedes ejecutar los scripts para generar los archivos de salida:

1. **Generar la imagen de zonificación (PNG)**:
   ```bash
   python3 genmap.py
   ```
2. **Generar los datos vectoriales (OSM)**:
   ```bash
   python3 genosm.py
   ```

Todos los resultados se guardarán automáticamente en el directorio `outputs/`.
