# 📊 Reporte de Simulación de Inversiones (Monte Carlo)

Generado el: `2026-06-04 12:24:00`

## ⚙️ Parámetros de la Simulación
- **Monto inicial de inversión:** `$10,000.00 USD`
- **Horizonte temporal:** `20 años`
- **Perfil de riesgo:** `Moderado`
- **Número de simulaciones:** `100`
- **Semilla utilizada:** `900717724`

### Asignación de Activos (Moderado)
| Clase de Activo | Peso (%) | Retorno Medio Histórico | Volatilidad Histórica |
| :--- | :---: | :---: | :---: |
| Renta Variable (Acciones) | 50.0% | 10.0% | 15.0% |
| Renta Fija (Bonos) | 40.0% | 4.0% | 5.0% |
| Efectivo | 10.0% | 2.0% | 1.0% |

---

## 🏆 Resumen de Resultados Finales
| Escenario / Métrica | Monto Final Esperado | Rendimiento Total (%) | Rendimiento Anualizado (CAGR) |
| :--- | :---: | :---: | :---: |
| **Peor Caso (5%)** | $20,471.38 | +104.71% | 3.65% |
| **Caso Base (50%)** | $32,624.89 | +226.25% | 6.09% |
| **Mejor Caso (95%)** | $57,901.17 | +479.01% | 9.18% |
| **Promedio** | $35,419.68 | +254.20% | 6.53% |

---

## 📅 Evolución Detallada Año por Año (Pérdidas y Ganancias)
| Año | Peor Caso (Percentil 5%) | Caso Base (Percentil 50%) | Mejor Caso (Percentil 95%) |
| :---: | :--- | :--- | :--- |
| 0 | $10,000 (Inicio) | $10,000 (Inicio) | $10,000 (Inicio) |
| **1** | $9,607 <br/>`-$393 (-3.9%)` | $10,663 <br/>`+$663 (+6.6%)` | $11,619 <br/>`+$1,619 (+16.2%)` |
| **2** | $9,447 <br/>`-$160 (-1.7%)` | $11,351 <br/>`+$689 (+6.5%)` | $12,963 <br/>`+$1,344 (+11.6%)` |
| **3** | $9,944 <br/>`+$497 (+5.3%)` | $11,993 <br/>`+$641 (+5.6%)` | $14,298 <br/>`+$1,335 (+10.3%)` |
| **4** | $10,221 <br/>`+$276 (+2.8%)` | $12,820 <br/>`+$827 (+6.9%)` | $16,129 <br/>`+$1,831 (+12.8%)` |
| **5** | $10,115 <br/>`-$106 (-1.0%)` | $13,513 <br/>`+$693 (+5.4%)` | $17,250 <br/>`+$1,122 (+7.0%)` |
| **6** | $10,597 <br/>`+$482 (+4.8%)` | $14,252 <br/>`+$739 (+5.5%)` | $18,230 <br/>`+$980 (+5.7%)` |
| **7** | $10,754 <br/>`+$158 (+1.5%)` | $15,245 <br/>`+$993 (+7.0%)` | $20,510 <br/>`+$2,279 (+12.5%)` |
| **8** | $11,417 <br/>`+$663 (+6.2%)` | $15,872 <br/>`+$627 (+4.1%)` | $21,324 <br/>`+$814 (+4.0%)` |
| **9** | $11,637 <br/>`+$220 (+1.9%)` | $17,247 <br/>`+$1,375 (+8.7%)` | $23,428 <br/>`+$2,104 (+9.9%)` |
| **10** | $13,163 <br/>`+$1,526 (+13.1%)` | $18,718 <br/>`+$1,471 (+8.5%)` | $24,321 <br/>`+$893 (+3.8%)` |
| **11** | $13,279 <br/>`+$116 (+0.9%)` | $18,808 <br/>`+$90 (+0.5%)` | $28,593 <br/>`+$4,272 (+17.6%)` |
| **12** | $13,585 <br/>`+$306 (+2.3%)` | $20,354 <br/>`+$1,545 (+8.2%)` | $30,710 <br/>`+$2,118 (+7.4%)` |
| **13** | $14,988 <br/>`+$1,403 (+10.3%)` | $22,151 <br/>`+$1,798 (+8.8%)` | $34,382 <br/>`+$3,672 (+12.0%)` |
| **14** | $15,617 <br/>`+$629 (+4.2%)` | $23,140 <br/>`+$989 (+4.5%)` | $35,620 <br/>`+$1,238 (+3.6%)` |
| **15** | $15,572 <br/>`-$46 (-0.3%)` | $23,581 <br/>`+$441 (+1.9%)` | $40,684 <br/>`+$5,064 (+14.2%)` |
| **16** | $16,227 <br/>`+$655 (+4.2%)` | $25,238 <br/>`+$1,657 (+7.0%)` | $43,586 <br/>`+$2,902 (+7.1%)` |
| **17** | $16,341 <br/>`+$114 (+0.7%)` | $26,642 <br/>`+$1,405 (+5.6%)` | $45,854 <br/>`+$2,268 (+5.2%)` |
| **18** | $17,059 <br/>`+$718 (+4.4%)` | $29,483 <br/>`+$2,840 (+10.7%)` | $50,795 <br/>`+$4,941 (+10.8%)` |
| **19** | $18,500 <br/>`+$1,442 (+8.5%)` | $30,971 <br/>`+$1,488 (+5.0%)` | $56,179 <br/>`+$5,385 (+10.6%)` |
| **20** | $20,471 <br/>`+$1,971 (+10.7%)` | $32,625 <br/>`+$1,654 (+5.3%)` | $57,901 <br/>`+$1,722 (+3.1%)` |

---

## 🧠 Guía de Análisis e Interpretación
- **Peor Caso (Percentil 5%):** Existe un 95% de probabilidad de que el portafolio termine con un valor igual o mayor a `$20,471.38`.
- **Caso Base (Percentil 50%):** El valor central esperado del portafolio es de `$32,624.89`. Representa el escenario más probable.
- **Mejor Caso (Percentil 95%):** Existe solo un 5% de probabilidad de superar un valor final de `$57,901.17`.

*Nota: Este reporte fue generado mediante una simulación probabilística de Monte Carlo con retornos anuales normales y rebalanceo anual constante del portafolio.*
