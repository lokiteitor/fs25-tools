# 📊 Simulador de Inversiones de Monte Carlo

Este es un programa interactivo en Python que simula la evolución de un portafolio de inversión a largo plazo utilizando el método de **Simulación de Monte Carlo**. Genera caminos de rendimiento basados en la distribución normal y permite analizar la evolución detallada año por año para tres perfiles de riesgo y diferentes escenarios de probabilidad.

## 🚀 Características
- **Interactividad Total:** Permite configurar de forma interactiva el monto de inversión, el horizonte temporal (años), el perfil de riesgo y el número de iteraciones.
- **Soporte de CLI:** También puede ejecutarse directamente desde la terminal pasando parámetros.
- **Asignación de Activos Reales:** Utiliza tres clases de activos (Acciones, Bonos y Efectivo) rebalanceados anualmente según el perfil seleccionado.
- **Evolución Año por Año (P&G):** Muestra detalladamente los balances anuales junto con las ganancias o pérdidas en dólares y porcentaje para los tres escenarios principales.
- **Salida Elegante:** Utiliza la librería `rich` para tablas con colores legibles, bordes limpios y paneles informativos.


---

## 🛠️ Requisitos e Instalación

El programa requiere **Python 3.9 o superior**. Para instalar las dependencias necesarias:

1. **Crear e inicializar un entorno virtual (opcional pero recomendado):**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

2. **Instalar las dependencias:**
   ```bash
   pip install -r requirements.txt
   ```

---

## 💻 Cómo Usar

### 1. Modo Interactivo
Simplemente ejecuta el script sin parámetros. La interfaz te guiará con indicaciones paso a paso y valores sugeridos por defecto:
```bash
python3 simulador.py
```

### 2. Modo Directo (CLI)
Si prefieres saltarte los prompts interactivos, puedes pasar los argumentos directamente. Por ejemplo:
```bash
python3 simulador.py --monto 15000 --anos 25 --perfil agresivo --simulaciones 5000 --no-interactivo
```

**Parámetros aceptados:**
- `--monto`: Monto inicial de inversión en dólares (ej. `10000`).
- `--anos`: Horizonte temporal de simulación en años (ej. `20`).
- `--perfil`: Perfil de riesgo: `conservador`, `moderado` o `agresivo`.
- `--simulaciones`: Cantidad de caminos simulados (ej. `1000`).
- `--no-interactivo`: Bandera para ejecutar directamente sin preguntar.

---

## 📈 Parámetros del Motor Matemático
El simulador modela el retorno de cada año utilizando la fórmula:
$$\text{Retorno Anual} = \text{Retorno Medio} + (\text{Volatilidad} \times Z)$$
Donde $Z \sim \mathcal{N}(0, 1)$ es un número aleatorio normal estándar.

### Parámetros Históricos por Activo:
1. **Renta Variable (Acciones):** Retorno Medio = $10\%$, Volatilidad = $15\%$.
2. **Renta Fija (Bonos):** Retorno Medio = $4\%$, Volatilidad = $5\%$.
3. **Efectivo:** Retorno Medio = $2\%$, Volatilidad = $1\%$.

### Perfiles de Riesgo:
- **Conservador:** $15\%$ Acciones / $60\%$ Bonos / $25\%$ Efectivo.
- **Moderado:** $50\%$ Acciones / $40\%$ Bonos / $10\%$ Efectivo.
- **Agresivo:** $85\%$ Acciones / $10\%$ Bonos / $5\%$ Efectivo.

---

## 📊 Escenarios Analizados
Los resultados muestran tres percentiles clave:
- **Peor Caso (Percentil 5%):** El portafolio tiene un $95\%$ de probabilidad de superar este valor (escenario de mercado muy bajista).
- **Caso Base (Percentil 50% / Mediana):** El punto medio de los resultados, representando la trayectoria central esperada.
- **Mejor Caso (Percentil 95%):** Existe solo un $5\%$ de probabilidad de superar este valor (escenario de mercado muy alcista).
