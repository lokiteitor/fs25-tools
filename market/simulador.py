#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Simulador de Inversiones Monte Carlo
-----------------------------------
Este programa simula la evolución de una inversión a largo plazo utilizando
el método de simulación de Monte Carlo con retornos anuales normales.
Permite configurar el monto inicial, el horizonte temporal, el perfil de riesgo
y el número de iteraciones. Muestra resultados detallados año por año de ganancias
y pérdidas para los escenarios de peor caso (percentil 5%), caso base (percentil 50%)
y mejor caso (percentil 95%), además de renderizar un gráfico de la evolución
directamente en la terminal.
"""

import sys
import argparse
import shutil
import numpy as np
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt, FloatPrompt, IntPrompt
from rich.align import Align
from rich import box

# Inicializar consola Rich
console = Console()

# Definición de activos y sus parámetros históricos (retorno medio y volatilidad)
ASSETS = {
    'RV': {
        'name': 'Renta Variable (Acciones)',
        'mean': 0.10,  # 10%
        'vol': 0.15,   # 15%
        'color': 'cyan'
    },
    'RF': {
        'name': 'Renta Fija (Bonos)',
        'mean': 0.04,  # 4%
        'vol': 0.05,   # 5%
        'color': 'yellow'
    },
    'EF': {
        'name': 'Efectivo',
        'mean': 0.02,  # 2%
        'vol': 0.01,   # 1%
        'color': 'green'
    }
}

# Perfiles de riesgo y sus asignaciones de activos
PROFILES = {
    'conservador': {
        'name': 'Conservador',
        'weights': {'RV': 0.15, 'RF': 0.60, 'EF': 0.25},
        'description': 'Prioriza la preservación del capital y minimiza la volatilidad. Ideal para horizontes cortos o perfiles adversos al riesgo.'
    },
    'moderado': {
        'name': 'Moderado',
        'weights': {'RV': 0.50, 'RF': 0.40, 'EF': 0.10},
        'description': 'Busca un equilibrio entre el crecimiento del capital y la estabilidad. Adecuado para un horizonte a mediano/largo plazo.'
    },
    'agresivo': {
        'name': 'Agresivo',
        'weights': {'RV': 0.85, 'RF': 0.10, 'EF': 0.05},
        'description': 'Maximiza el potencial de crecimiento a largo plazo aceptando fluctuaciones severas del mercado.'
    }
}

def clear_terminal():
    """Limpia la pantalla de la terminal."""
    console.clear()

def display_welcome_banner():
    """Muestra un banner de bienvenida elegante."""
    banner_text = (
        "[bold gold1]📈 SIMULADOR DE INVERSIONES MONTE CARLO 📊[/bold gold1]\n"
        "[dim]Herramienta de simulación probabilística para planificación financiera[/dim]"
    )
    console.print(Panel(Align.center(banner_text), border_style="gold1", box=box.ROUNDED))

def display_profile_info(profile_name):
    """Muestra la asignación de activos del perfil seleccionado."""
    profile = PROFILES[profile_name]
    weights = profile['weights']
    
    table = Table(title=f"Asignación de Activos - Perfil {profile['name']}", box=box.SIMPLE_HEAD, title_style="bold cyan")
    table.add_column("Clase de Activo", style="bold")
    table.add_column("Peso (%)", justify="right")
    table.add_column("Retorno Medio Histórico", justify="right", style="dim")
    table.add_column("Volatilidad Histórica", justify="right", style="dim")
    
    for asset_code, weight in weights.items():
        asset = ASSETS[asset_code]
        table.add_row(
            asset['name'],
            f"{weight * 100:.1f}%",
            f"{asset['mean'] * 100:.1f}%",
            f"{asset['vol'] * 100:.1f}%"
        )
        
    console.print(table)
    console.print(f"[italic dim]* {profile['description']}[/italic dim]\n")

def run_monte_carlo(initial_amount, years, profile_name, num_simulations, seed=None):
    """
    Ejecuta la simulación de Monte Carlo.
    Retorna una matriz de dimensiones (num_simulations, years + 1) con los valores del portafolio.
    """
    weights = PROFILES[profile_name]['weights']
    
    # Crear generador local con la semilla provista
    rng = np.random.default_rng(seed)
    
    # Generar retornos anuales aleatorios para cada clase de activo
    # Distribución normal basada en retorno medio y desviación estándar (volatilidad)
    r_rv = rng.normal(ASSETS['RV']['mean'], ASSETS['RV']['vol'], (num_simulations, years))
    r_rf = rng.normal(ASSETS['RF']['mean'], ASSETS['RF']['vol'], (num_simulations, years))
    r_ef = rng.normal(ASSETS['EF']['mean'], ASSETS['EF']['vol'], (num_simulations, years))
    
    # Retorno combinado del portafolio año por año
    r_port = (
        weights['RV'] * r_rv +
        weights['RF'] * r_rf +
        weights['EF'] * r_ef
    )
    
    # Limitar pérdidas al -100% para evitar balances negativos irreales
    r_port = np.clip(r_port, -0.9999, None)
    
    # Crear matriz para almacenar el valor del portafolio a lo largo del tiempo
    # El año 0 inicia con el monto inicial
    factors = np.hstack([np.ones((num_simulations, 1)), 1 + r_port])
    value_paths = initial_amount * np.cumprod(factors, axis=1)
    
    return value_paths

def calculate_metrics(value_paths, initial_amount, years):
    """
    Calcula los percentiles y métricas de rendimiento final.
    """
    # Percentiles año a año
    p5_path = np.percentile(value_paths, 5, axis=0)
    p50_path = np.percentile(value_paths, 50, axis=0)
    p95_path = np.percentile(value_paths, 95, axis=0)
    mean_path = np.mean(value_paths, axis=0)
    
    metrics = {}
    for label, path in [('Peor Caso (5%)', p5_path), ('Caso Base (50%)', p50_path), ('Mejor Caso (95%)', p95_path)]:
        final_val = path[-1]
        total_return = ((final_val - initial_amount) / initial_amount) * 100
        # Evitar división por cero o raíces de números negativos
        if final_val > 0:
            cagr = ((final_val / initial_amount) ** (1 / years) - 1) * 100
        else:
            cagr = -100.0
            
        metrics[label] = {
            'final_value': final_val,
            'total_return': total_return,
            'cagr': cagr,
            'path': path
        }
        
    metrics['Promedio'] = {
        'final_value': mean_path[-1],
        'total_return': ((mean_path[-1] - initial_amount) / initial_amount) * 100,
        'cagr': ((mean_path[-1] / initial_amount) ** (1 / years) - 1) * 100 if mean_path[-1] > 0 else -100.0,
        'path': mean_path
    }
    
    return metrics

def display_summary_table(metrics, initial_amount):
    """Muestra una tabla resumen de los resultados finales."""
    table = Table(title="Resumen de Resultados Finales", box=box.DOUBLE_EDGE, title_style="bold gold1")
    table.add_column("Escenario / Métrica", style="bold")
    table.add_column("Monto Final Esperado", justify="right", style="bold")
    table.add_column("Rendimiento Total (%)", justify="right")
    table.add_column("Rendimiento Anualizado (CAGR)", justify="right")
    
    # Agregar las filas
    for label, color in [('Peor Caso (5%)', 'red'), ('Caso Base (50%)', 'cyan'), ('Mejor Caso (95%)', 'green'), ('Promedio', 'magenta')]:
        m = metrics[label]
        val_str = f"${m['final_value']:,.2f}"
        ret_str = f"{m['total_return']:+,.2f}%"
        cagr_str = f"{m['cagr']:.2f}%"
        
        # Dar formato de color según el escenario
        table.add_row(
            f"[{color}]{label}[/{color}]",
            f"[{color}]{val_str}[/{color}]",
            f"[{color}]{ret_str}[/{color}]",
            f"[{color}]{cagr_str}[/{color}]"
        )
        
    console.print(table)
    console.print()

def display_year_by_year_table(metrics):
    """Muestra la tabla de evolución año por año con ganancias y pérdidas detalladas."""
    p5_path = metrics['Peor Caso (5%)']['path']
    p50_path = metrics['Caso Base (5%)' if 'Caso Base (5%)' in metrics else 'Caso Base (50%)']['path']
    p95_path = metrics['Mejor Caso (95%)']['path']
    
    years = len(p50_path) - 1
    
    table = Table(
        title="Evolución Detallada Año por Año (Pérdidas y Ganancias)", 
        box=box.ROUNDED, 
        title_style="bold cyan",
        show_lines=True
    )
    table.add_column("Año", justify="center", style="bold dim")
    table.add_column("Peor Caso (Percentil 5%)\nBalance y Ganancia/Pérdida", justify="right")
    table.add_column("Caso Base (Percentil 50%)\nBalance y Ganancia/Pérdida", justify="right")
    table.add_column("Mejor Caso (Percentil 95%)\nBalance y Ganancia/Pérdida", justify="right")
    
    # Agregar el Año 0
    table.add_row(
        "0",
        f"${p5_path[0]:,.0f}\n[dim]Inicio[/dim]",
        f"${p50_path[0]:,.0f}\n[dim]Inicio[/dim]",
        f"${p95_path[0]:,.0f}\n[dim]Inicio[/dim]"
    )
    
    for t in range(1, years + 1):
        row_cells = [str(t)]
        
        for path in [p5_path, p50_path, p95_path]:
            val_prev = path[t-1]
            val_curr = path[t]
            diff = val_curr - val_prev
            pct_change = (diff / val_prev) * 100 if val_prev > 0 else 0
            
            # Formatear el cambio
            if diff >= 0:
                change_str = f"[green]+${diff:,.0f} (+{pct_change:.1f}%)[/green]"
            else:
                change_str = f"[red]-${abs(diff):,.0f} ({pct_change:.1f}%)[/red]"
                
            cell_content = f"${val_curr:,.0f}\n{change_str}"
            row_cells.append(cell_content)
            
        table.add_row(*row_cells)
        
    console.print(table)
    console.print()

def prompt_user_inputs():
    """Solicita de forma interactiva y amigable las entradas al usuario."""
    display_welcome_banner()
    
    console.print("[bold yellow]Ingrese los parámetros de simulación:[/bold yellow]")
    
    # 1. Monto inicial
    initial_amount = FloatPrompt.ask(
        "💵 Monto inicial de inversión ($)",
        default=10000.0,
        show_default=True
    )
    while initial_amount <= 0:
        console.print("[bold red]Error: El monto debe ser mayor que 0.[/bold red]")
        initial_amount = FloatPrompt.ask("💵 Monto inicial de inversión ($)")
        
    # 2. Horizonte temporal
    years = IntPrompt.ask(
        "📅 Horizonte temporal (años)",
        default=20,
        show_default=True
    )
    while years <= 0:
        console.print("[bold red]Error: Los años deben ser mayor que 0.[/bold red]")
        years = IntPrompt.ask("📅 Horizonte temporal (años)")
        
    # 3. Perfil de riesgo
    console.print("\n[bold]Seleccione el perfil de riesgo:[/bold]")
    console.print("1. [green]Conservador[/green] (Acciones: 15%, Bonos: 60%, Efectivo: 25%)")
    console.print("2. [cyan]Moderado[/cyan] (Acciones: 50%, Bonos: 40%, Efectivo: 10%)")
    console.print("3. [red]Agresivo[/red] (Acciones: 85%, Bonos: 10%, Efectivo: 5%)")
    
    profile_choice = Prompt.ask(
        "🧠 Perfil de riesgo (1, 2, 3 o nombre)",
        choices=["1", "2", "3", "conservador", "moderado", "agresivo"],
        default="2"
    )
    
    if profile_choice in ["1", "conservador"]:
        profile_name = "conservador"
    elif profile_choice in ["3", "agresivo"]:
        profile_name = "agresivo"
    else:
        profile_name = "moderado"
        
    # 4. Número de simulaciones
    num_simulations = IntPrompt.ask(
        "🔀 Número de simulaciones de Monte Carlo",
        default=1000,
        show_default=True
    )
    while num_simulations <= 0:
        console.print("[bold red]Error: El número de simulaciones debe ser mayor que 0.[/bold red]")
        num_simulations = IntPrompt.ask("🔀 Número de simulaciones de Monte Carlo")
        
    return initial_amount, years, profile_name, num_simulations

def save_markdown_report(filepath, metrics, initial_amount, years, profile_name, num_simulations, seed):
    """
    Genera y guarda un reporte detallado de la simulación en un archivo Markdown (.md).
    """
    from datetime import datetime
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    profile = PROFILES[profile_name]
    weights = profile['weights']
    
    # Encabezado y parámetros
    md_content = f"""# 📊 Reporte de Simulación de Inversiones (Monte Carlo)

Generado el: `{now_str}`

## ⚙️ Parámetros de la Simulación
- **Monto inicial de inversión:** `${initial_amount:,.2f} USD`
- **Horizonte temporal:** `{years} años`
- **Perfil de riesgo:** `{profile['name']}`
- **Número de simulaciones:** `{num_simulations:,}`
- **Semilla utilizada:** `{seed}`

### Asignación de Activos ({profile['name']})
| Clase de Activo | Peso (%) | Retorno Medio Histórico | Volatilidad Histórica |
| :--- | :---: | :---: | :---: |
"""
    for asset_code, weight in weights.items():
        asset = ASSETS[asset_code]
        md_content += f"| {asset['name']} | {weight * 100:.1f}% | {asset['mean'] * 100:.1f}% | {asset['vol'] * 100:.1f}% |\n"
        
    md_content += f"""
---

## 🏆 Resumen de Resultados Finales
| Escenario / Métrica | Monto Final Esperado | Rendimiento Total (%) | Rendimiento Anualizado (CAGR) |
| :--- | :---: | :---: | :---: |
"""
    for label in ['Peor Caso (5%)', 'Caso Base (50%)', 'Mejor Caso (95%)', 'Promedio']:
        m = metrics[label]
        val_str = f"${m['final_value']:,.2f}"
        ret_str = f"{m['total_return']:+,.2f}%"
        cagr_str = f"{m['cagr']:.2f}%"
        md_content += f"| **{label}** | {val_str} | {ret_str} | {cagr_str} |\n"
        
    md_content += f"""
---

## 📅 Evolución Detallada Año por Año (Pérdidas y Ganancias)
| Año | Peor Caso (Percentil 5%) | Caso Base (Percentil 50%) | Mejor Caso (Percentil 95%) |
| :---: | :--- | :--- | :--- |
"""
    
    p5_path = metrics['Peor Caso (5%)']['path']
    p50_path = metrics['Caso Base (50%)']['path']
    p95_path = metrics['Mejor Caso (95%)']['path']
    
    # Año 0
    md_content += f"| 0 | ${p5_path[0]:,.0f} (Inicio) | ${p50_path[0]:,.0f} (Inicio) | ${p95_path[0]:,.0f} (Inicio) |\n"
    
    for t in range(1, years + 1):
        row_parts = [f"**{t}**"]
        for path in [p5_path, p50_path, p95_path]:
            val_prev = path[t-1]
            val_curr = path[t]
            diff = val_curr - val_prev
            pct_change = (diff / val_prev) * 100 if val_prev > 0 else 0
            
            sign = "+" if diff >= 0 else "-"
            change_str = f"{sign}${abs(diff):,.0f} ({pct_change:+.1f}%)"
            row_parts.append(f"${val_curr:,.0f} <br/>`{change_str}`")
            
        md_content += f"| " + " | ".join(row_parts) + " |\n"
        
    md_content += f"""
---

## 🧠 Guía de Análisis e Interpretación
- **Peor Caso (Percentil 5%):** Existe un 95% de probabilidad de que el portafolio termine con un valor igual o mayor a `${metrics['Peor Caso (5%)']['final_value']:,.2f}`.
- **Caso Base (Percentil 50%):** El valor central esperado del portafolio es de `${metrics['Caso Base (50%)']['final_value']:,.2f}`. Representa el escenario más probable.
- **Mejor Caso (Percentil 95%):** Existe solo un 5% de probabilidad de superar un valor final de `${metrics['Mejor Caso (95%)']['final_value']:,.2f}`.

*Nota: Este reporte fue generado mediante una simulación probabilística de Monte Carlo con retornos anuales normales y rebalanceo anual constante del portafolio.*
"""
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(md_content)

def main():
    parser = argparse.ArgumentParser(description="Simulador de Inversiones Monte Carlo.")
    parser.add_argument("--monto", type=float, help="Monto inicial de inversión.")
    parser.add_argument("--anos", type=int, help="Horizonte temporal en años.")
    parser.add_argument("--perfil", type=str, choices=["conservador", "moderado", "agresivo"], help="Perfil de riesgo.")
    parser.add_argument("--simulaciones", type=int, help="Número de iteraciones de Monte Carlo.")
    parser.add_argument("--seed", type=int, help="Semilla para el generador de números aleatorios (para reproducibilidad).")
    parser.add_argument("--reporte", type=str, default="reporte_simulacion.md", help="Ruta del archivo Markdown donde guardar el reporte final.")
    parser.add_argument("--no-interactivo", action="store_true", help="Desactiva la interfaz interactiva.")
    
    args = parser.parse_args()
    
    # Determinar si ejecutar en modo interactivo o no
    if args.no_interactivo or any(v is not None for v in [args.monto, args.anos, args.perfil, args.simulaciones]):
        # Modo no interactivo (tomar valores pasados o sus valores por defecto)
        initial_amount = args.monto if args.monto is not None else 10000.0
        years = args.anos if args.anos is not None else 20
        profile_name = args.perfil if args.perfil is not None else "moderado"
        num_simulations = args.simulaciones if args.simulaciones is not None else 1000
        
        if initial_amount <= 0 or years <= 0 or num_simulations <= 0:
            console.print("[bold red]Error: Los valores de monto, años y simulaciones deben ser mayores a 0.[/bold red]")
            sys.exit(1)
            
        display_welcome_banner()
    else:
        # Modo interactivo
        clear_terminal()
        initial_amount, years, profile_name, num_simulations = prompt_user_inputs()
        
    clear_terminal()
    display_welcome_banner()
    
    # Mostrar la asignación de activos correspondiente
    display_profile_info(profile_name)
    
    # Definir o generar semilla aleatoria para cada ejecución
    seed = args.seed
    if seed is None:
        seed = int(np.random.default_rng().integers(low=1, high=2**31 - 1))

    # Ejecutar la simulación con indicador de carga
    with console.status("[bold green]Generando caminos de simulación y calculando retornos probabilísticos...[/bold green]"):
        value_paths = run_monte_carlo(initial_amount, years, profile_name, num_simulations, seed=seed)
        metrics = calculate_metrics(value_paths, initial_amount, years)
        
    # Mostrar tablas de resultados
    display_summary_table(metrics, initial_amount)
    display_year_by_year_table(metrics)
    
    # Notas informativas
    console.print(Panel(
        f"[bold cyan]Interpretación de Escenarios:[/bold cyan]\n"
        f"• [bold red]Peor Caso (Percentil 5%):[/bold red] Existe un 95% de probabilidad de que el portafolio termine con un valor [bold]igual o mayor[/bold] a [bold red]${metrics['Peor Caso (5%)']['final_value']:,.2f}[/bold red] al cabo de {years} años.\n"
        f"• [bold cyan]Caso Base (Percentil 50% / Mediana):[/bold cyan] El valor central esperado del portafolio es de [bold cyan]${metrics['Caso Base (50%)']['final_value']:,.2f}[/bold cyan]. Representa el escenario más probable.\n"
        f"• [bold green]Mejor Caso (Percentil 95%):[/bold green] Existe solo un 5% de probabilidad de superar un valor final de [bold green]${metrics['Mejor Caso (95%)']['final_value']:,.2f}[/bold green].\n\n"
        f"[dim]Nota: Los retornos pasados no garantizan rendimientos futuros. Esta simulación asume retornos distribuidos normalmente con rebalanceo anual constante.\n"
        f"Semilla de simulación utilizada (diferente en cada corrida por defecto): {seed}[/dim]",
        title="[bold yellow]Guía de Análisis[/bold yellow]",
        border_style="yellow",
        box=box.ROUNDED
    ))
    
    # Guardar reporte
    save_markdown_report(args.reporte, metrics, initial_amount, years, profile_name, num_simulations, seed)
    console.print(f"\n[bold green]✓ Reporte guardado exitosamente en: {args.reporte}[/bold green]\n")

if __name__ == "__main__":
    main()
