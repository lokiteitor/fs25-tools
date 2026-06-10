<!-- app/pages/speed-calculator.vue -->
<template>
  <div class="calculator-container">
    
    <!-- Sección superior: Introducción -->
    <div class="intro-card glass-card">
      <div class="intro-content">
        <h2>⏱️ Estimador de Tiempo de Trabajo</h2>
        <p class="intro-text">
          Calcula el tiempo necesario para completar las tareas de tu granja utilizando una o varias herramientas de tu flota de forma simultánea. Selecciona las herramientas activas en el panel derecho para simular el trabajo coordinado.
        </p>
      </div>
    </div>

    <div class="grid-layout">
      <!-- PANEL IZQUIERDO: Parámetros del Campo -->
      <div class="left-panel">
        
        <!-- Tarjeta de Parámetros del Campo -->
        <div class="glass-card config-card">
          <h3 class="card-title">🌾 Datos del Campo</h3>
          
          <div class="form-group mb-16">
            <label for="field-selector">Seleccionar Campo Guardado</label>
            <select id="field-selector" v-model="selectedFieldId" class="select-premium" @change="onFieldSelect">
              <option :value="null">-- Usar tamaño personalizado --</option>
              <option v-for="field in savedFields" :key="field.id" :value="field.id">
                Campo {{ field.fieldNumber }} ({{ field.hectares }} ha)
              </option>
            </select>
          </div>

          <div class="form-group mb-16">
            <label for="field-area">Área a Trabajar (hectáreas)</label>
            <input 
              id="field-area" 
              type="number" 
              step="0.01" 
              min="0.01" 
              v-model.number="hectares" 
              class="input-premium"
              placeholder="Ej: 5.5"
              @input="onCustomAreaInput"
            />
          </div>

          <div class="form-group">
            <div class="label-with-value">
              <label for="efficiency-slider">Eficiencia de Trabajo</label>
              <span class="value-highlight">{{ efficiency }}%</span>
            </div>
            <input 
              id="efficiency-slider" 
              type="range" 
              min="50" 
              max="100" 
              step="5" 
              v-model.number="efficiency" 
              class="slider-premium"
              @input="saveCalculatorState"
            />
            <div class="efficiency-presets">
              <button class="btn-preset" :class="{ active: efficiency === 100 }" @click="setEfficiency(100)">100% (Teórico)</button>
              <button class="btn-preset" :class="{ active: efficiency === 90 }" @click="setEfficiency(90)">90% (Normal)</button>
              <button class="btn-preset" :class="{ active: efficiency === 75 }" @click="setEfficiency(75)">75% (Complejo)</button>
            </div>
            <span class="control-help mt-8">
              Afecta al tiempo debido a giros en cabeceras, maniobras de reversa y solapamiento de pasadas.
            </span>
          </div>
        </div>

        <!-- Atajo rápido a gestión de flota -->
        <div class="glass-card fleet-link-card mt-24">
          <h4 class="fleet-link-title">🚜 Gestión de tu Flota</h4>
          <p class="fleet-link-desc">¿Necesitas añadir nuevas sembradoras, tractores o cosechadoras con anchos y velocidades distintos?</p>
          <NuxtLink to="/machinery" class="btn-premium btn-secondary btn-sm full-width mt-12">
            Administrar Mi Maquinaria →
          </NuxtLink>
        </div>
      </div>

      <!-- PANEL DERECHO: Selección de Maquinaria y Resultados -->
      <div class="right-panel">
        
        <!-- Selección de Herramientas -->
        <div class="glass-card machinery-card">
          <h3 class="card-title">🛠️ Seleccionar Maquinaria Activa</h3>
          
          <div v-if="tools.length === 0" class="no-tools">
            <p>⚠️ No tienes ninguna herramienta registrada en tu flota.</p>
            <p class="sub-text">Primero debes dar de alta tus equipos para poder utilizarlos en el estimador.</p>
            <NuxtLink to="/machinery" class="btn-premium mt-16">
              Registrar Mi Maquinaria
            </NuxtLink>
          </div>

          <div v-else class="tools-grid-list">
            <div 
              v-for="(tool, index) in tools" 
              :key="index" 
              class="tool-selection-card" 
              :class="{ active: tool.active }"
              @click="toggleToolActive(tool)"
            >
              <div class="tool-checkbox-wrapper">
                <input 
                  type="checkbox" 
                  v-model="tool.active" 
                  @click.stop 
                  @change="saveCalculatorState"
                  class="checkbox-premium"
                />
              </div>
              
              <div class="tool-details-wrapper">
                <span class="tool-name">{{ tool.name }}</span>
                <div class="tool-specs">
                  <span class="spec-tag">Ancho: <strong>{{ tool.width }}m</strong></span>
                  <span class="spec-tag">Velocidad: <strong>{{ tool.speed }} km/h</strong></span>
                  <span class="spec-tag capacity">Capacidad: <strong>{{ getCapacity(tool).toFixed(2) }} ha/h</strong></span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Tarjeta de Resultados -->
        <div class="glass-card results-card" :class="{ 'results-active': activeToolsCount > 0 }">
          <h3 class="card-title text-accent">⏱️ Estimación de Tiempo</h3>
          
          <div v-if="activeToolsCount === 0" class="no-calculations">
            <p>⚠️ Selecciona al menos una máquina activa en el panel superior para estimar el tiempo.</p>
          </div>

          <div v-else class="results-layout">
            <div class="main-timer-display">
              <span class="timer-label">Tiempo Estimado de Trabajo</span>
              <span class="timer-value">{{ formattedTime }}</span>
              <span class="timer-sub">{{ decimalHours.toFixed(2) }} horas totales</span>
            </div>

            <div class="stats-summary-grid mt-24">
              <div class="stat-summary-box">
                <span class="box-label">Capacidad Teórica</span>
                <span class="box-value">{{ totalTheoreticalCapacity.toFixed(2) }} ha/h</span>
              </div>
              <div class="stat-summary-box">
                <span class="box-label">Capacidad Efectiva ({{ efficiency }}%)</span>
                <span class="box-value text-accent">{{ totalEffectiveCapacity.toFixed(2) }} ha/h</span>
              </div>
              <div class="stat-summary-box">
                <span class="box-label">Área del Campo</span>
                <span class="box-value">{{ hectares.toFixed(2) }} ha</span>
              </div>
            </div>

            <!-- Desglose por herramienta si hay más de una -->
            <div class="breakdown-section mt-24" v-if="activeToolsCount > 0">
              <h4 class="breakdown-title">🚜 Desglose Individual de Herramientas</h4>
              <p class="breakdown-desc">
                Rendimiento y contribución de cada equipo operando simultáneamente:
              </p>
              
              <div class="table-container">
                <table class="table-premium">
                  <thead>
                    <tr>
                      <th>Herramienta</th>
                      <th>Ancho × Vel</th>
                      <th>Rendimiento Efectivo</th>
                      <th>Tiempo Sola</th>
                      <th>Participación</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="(tool, index) in tools.filter(t => t.active)" :key="index">
                      <td><strong>{{ tool.name }}</strong></td>
                      <td>{{ tool.width }}m @ {{ tool.speed }} km/h</td>
                      <td>{{ getEffectiveCapacity(tool).toFixed(2) }} ha/h</td>
                      <td>{{ formatHours(hectares / getEffectiveCapacity(tool)) }}</td>
                      <td class="percentage-col">
                        <div class="progress-bar-wrapper">
                          <span class="percentage-val">{{ getWorkShare(tool).toFixed(1) }}%</span>
                          <div class="progress-bar-bg">
                            <div class="progress-bar-fill" :style="{ width: getWorkShare(tool) + '%' }"></div>
                          </div>
                        </div>
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>

          </div>
        </div>

      </div>
    </div>

  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useDB } from '~/composables/useDB'

definePageMeta({
  layout: 'default'
})

const db = useDB()

// Variables reactivas
const savedFields = ref([])
const selectedFieldId = ref(null)
const hectares = ref(2.5) // default
const efficiency = ref(90) // default 90%

// Listado de herramientas cargado desde maquinaria global
const tools = ref([])

// Cargar estado inicial al montar
onMounted(async () => {
  // Cargar campos para el selector
  savedFields.value = await db.getAllFields()

  // Cargar maquinaria registrada
  const registered = await db.getSetting('registered_machinery', [])
  
  // Cargar configuraciones guardadas de la calculadora
  const savedState = await db.getSetting('work_speed_calculator_data', null)
  
  if (savedState) {
    if (savedState.hectares) hectares.value = savedState.hectares
    if (savedState.selectedFieldId !== undefined) {
      selectedFieldId.value = savedState.selectedFieldId
      // Sincronizar hectáreas con el campo cargado por si cambiaron
      if (selectedFieldId.value) {
        const found = savedFields.value.find(f => f.id === selectedFieldId.value)
        if (found) {
          hectares.value = found.hectares
        }
      }
    }
    if (savedState.efficiency) efficiency.value = savedState.efficiency
  }

  // Mapear la maquinaria global agregando el estado de activo (active)
  const savedActiveNames = savedState?.activeToolNames || []
  tools.value = registered.map(item => {
    // Si ya había configuraciones, verificamos si estaba activa. Si no había, por defecto las activamos.
    const wasActive = savedState?.activeToolNames !== undefined
      ? savedActiveNames.includes(item.name)
      : true
      
    return {
      ...item,
      active: wasActive
    }
  })
})

// Guardar estado en IndexedDB/settings
const saveCalculatorState = async () => {
  const stateToSave = {
    hectares: hectares.value,
    selectedFieldId: selectedFieldId.value,
    efficiency: efficiency.value,
    activeToolNames: tools.value.filter(t => t.active).map(t => t.name)
  }
  await db.saveSetting('work_speed_calculator_data', stateToSave)
}

// Acción al seleccionar un campo
const onFieldSelect = () => {
  if (selectedFieldId.value) {
    const field = savedFields.value.find(f => f.id === selectedFieldId.value)
    if (field) {
      hectares.value = field.hectares
    }
  }
  saveCalculatorState()
}

// Acción al ingresar hectáreas manualmente
const onCustomAreaInput = () => {
  selectedFieldId.value = null
  saveCalculatorState()
}

// Cambiar eficiencia
const setEfficiency = (val) => {
  efficiency.value = val
  saveCalculatorState()
}

// Alternar activo de herramienta al hacer click en su tarjeta
const toggleToolActive = (tool) => {
  tool.active = !tool.active
  saveCalculatorState()
}

// --- Cálculos Matemáticos ---

// Cantidad de herramientas activas
const activeToolsCount = computed(() => {
  return tools.value.filter(t => t.active).length
})

// Capacidad individual teórica (ha/h) = (ancho * velocidad) / 10
const getCapacity = (tool) => {
  return (tool.width * tool.speed) / 10
}

// Capacidad individual efectiva (ha/h)
const getEffectiveCapacity = (tool) => {
  return getCapacity(tool) * (efficiency.value / 100)
}

// Capacidad teórica combinada (ha/h)
const totalTheoreticalCapacity = computed(() => {
  return tools.value
    .filter(t => t.active)
    .reduce((sum, t) => sum + getCapacity(t), 0)
})

// Capacidad efectiva combinada (ha/h)
const totalEffectiveCapacity = computed(() => {
  return totalTheoreticalCapacity.value * (efficiency.value / 100)
})

// Tiempo de trabajo en horas (decimal)
const decimalHours = computed(() => {
  if (totalEffectiveCapacity.value === 0) return 0
  return hectares.value / totalEffectiveCapacity.value
})

// Participación de trabajo por herramienta (porcentaje de la capacidad efectiva total)
const getWorkShare = (tool) => {
  if (totalTheoreticalCapacity.value === 0) return 0
  return (getCapacity(tool) / totalTheoreticalCapacity.value) * 100
}

// Formatear horas decimales en texto legible (ej: "2 horas y 15 minutos")
const formattedTime = computed(() => {
  return formatHours(decimalHours.value)
})

// Función helper para formatear horas a string
const formatHours = (hoursValue) => {
  if (hoursValue <= 0 || isNaN(hoursValue)) return '0 minutos'
  
  const totalMinutes = Math.round(hoursValue * 60)
  const hours = Math.floor(totalMinutes / 60)
  const minutes = totalMinutes % 60

  let result = ''
  if (hours > 0) {
    result += `${hours} ${hours === 1 ? 'hora' : 'horas'}`
  }
  if (minutes > 0) {
    if (hours > 0) {
      result += ' y '
    }
    result += `${minutes} ${minutes === 1 ? 'minuto' : 'minutos'}`
  }
  if (hours === 0 && minutes === 0) {
    return 'menos de un minuto'
  }
  
  return result
}
</script>

<style scoped>
.calculator-container {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.intro-card {
  background: linear-gradient(135deg, rgba(46, 213, 115, 0.1) 0%, rgba(18, 30, 25, 0.65) 100%);
  border-left: 4px solid var(--primary);
}

.intro-card h2 {
  font-size: 24px;
  font-weight: 800;
  margin-bottom: 12px;
  color: var(--text-primary);
}

.intro-text {
  font-size: 15px;
  line-height: 1.6;
  color: var(--text-secondary);
}

.grid-layout {
  display: grid;
  grid-template-columns: 350px 1fr;
  gap: 24px;
  align-items: start;
}

@media (max-width: 900px) {
  .grid-layout {
    grid-template-columns: 1fr;
  }
}

.card-title {
  font-size: 16px;
  font-weight: 700;
  color: var(--primary);
  margin-bottom: 20px;
}

.card-title.mb-0 {
  margin-bottom: 0;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.form-group label {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-primary);
}

.label-with-value {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.value-highlight {
  color: var(--primary);
  font-weight: 700;
  font-size: 14px;
}

.control-help {
  font-size: 11px;
  color: var(--text-muted);
  line-height: 1.4;
}

.mb-16 {
  margin-bottom: 16px;
}

.mt-8 {
  margin-top: 8px;
}

.mt-12 {
  margin-top: 12px;
}

.mt-24 {
  margin-top: 24px;
}

.full-width {
  width: 100%;
}

.slider-premium {
  -webkit-appearance: none;
  width: 100%;
  height: 6px;
  border-radius: 3px;
  background: rgba(255, 255, 255, 0.1);
  outline: none;
  margin: 10px 0;
  cursor: pointer;
}

.slider-premium::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: var(--primary);
  box-shadow: 0 0 10px var(--primary-glow);
  cursor: pointer;
  transition: transform 0.1s;
}

.slider-premium::-webkit-slider-thumb:hover {
  transform: scale(1.2);
}

.efficiency-presets {
  display: flex;
  gap: 8px;
  margin-top: 8px;
}

.btn-preset {
  flex: 1;
  background: rgba(0, 0, 0, 0.2);
  border: 1px solid var(--border-color);
  color: var(--text-secondary);
  font-size: 11px;
  padding: 6px 4px;
  border-radius: 6px;
  cursor: pointer;
  transition: var(--transition-smooth);
}

.btn-preset:hover {
  background: rgba(46, 213, 115, 0.08);
  border-color: rgba(46, 213, 115, 0.3);
  color: var(--text-primary);
}

.btn-preset.active {
  background: rgba(46, 213, 115, 0.15);
  border-color: var(--primary);
  color: var(--primary);
  font-weight: 600;
}

/* Fleet Link Card */
.fleet-link-title {
  font-size: 14px;
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: 6px;
}

.fleet-link-desc {
  font-size: 12px;
  color: var(--text-muted);
  line-height: 1.4;
}

/* Machinery Selection */
.no-tools {
  text-align: center;
  padding: 40px 16px;
  color: var(--text-secondary);
}

.no-tools .sub-text {
  font-size: 12px;
  color: var(--text-muted);
  margin-top: 8px;
  margin-bottom: 16px;
}

.tools-grid-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 16px;
}

.tool-selection-card {
  background: rgba(0, 0, 0, 0.25);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  padding: 16px;
  display: flex;
  gap: 16px;
  cursor: pointer;
  transition: var(--transition-smooth);
  user-select: none;
}

.tool-selection-card:hover {
  border-color: rgba(46, 213, 115, 0.35);
  background: rgba(46, 213, 115, 0.03);
}

.tool-selection-card.active {
  border-color: var(--primary);
  background: rgba(46, 213, 115, 0.08);
  box-shadow: 0 4px 15px rgba(46, 213, 115, 0.08);
}

.tool-checkbox-wrapper {
  display: flex;
  align-items: center;
}

.checkbox-premium {
  width: 18px;
  height: 18px;
  accent-color: var(--primary);
  cursor: pointer;
}

.tool-details-wrapper {
  display: flex;
  flex-direction: column;
  gap: 6px;
  flex-grow: 1;
}

.tool-name {
  font-weight: 700;
  font-size: 14px;
  color: var(--text-primary);
}

.tool-specs {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.spec-tag {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.08);
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 11px;
  color: var(--text-secondary);
}

.spec-tag strong {
  color: var(--text-primary);
}

.spec-tag.capacity {
  border-color: rgba(46, 213, 115, 0.2);
  color: var(--primary);
}

.spec-tag.capacity strong {
  color: var(--primary);
}

/* Resultados Estilo */
.results-card {
  border-left: 4px solid var(--border-color);
}

.results-card.results-active {
  border-left-color: var(--primary);
}

.no-calculations {
  text-align: center;
  padding: 40px;
  color: var(--text-muted);
  font-size: 14px;
}

.results-layout {
  animation: fadeIn 0.4s ease-in-out;
}

.main-timer-display {
  background: rgba(46, 213, 115, 0.05);
  border: 1px solid var(--border-color);
  border-radius: 16px;
  padding: 24px;
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
}

.timer-label {
  font-size: 13px;
  color: var(--text-secondary);
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 1px;
  margin-bottom: 8px;
}

.timer-value {
  font-size: 32px;
  font-weight: 800;
  color: var(--primary);
  text-shadow: 0 0 20px rgba(46, 213, 115, 0.2);
}

.timer-sub {
  font-size: 13px;
  color: var(--text-muted);
  margin-top: 4px;
}

.stats-summary-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
}

@media (max-width: 600px) {
  .stats-summary-grid {
    grid-template-columns: 1fr;
  }
}

.stat-summary-box {
  background: rgba(0, 0, 0, 0.25);
  border: 1px solid var(--border-color);
  border-radius: 10px;
  padding: 12px 16px;
  display: flex;
  flex-direction: column;
  gap: 6px;
  align-items: center;
  text-align: center;
}

.box-label {
  font-size: 12px;
  color: var(--text-muted);
  font-weight: 500;
}

.box-value {
  font-size: 16px;
  font-weight: 700;
}

/* Breakdown / Tabla Desglose */
.breakdown-title {
  font-size: 14px;
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: 6px;
}

.breakdown-desc {
  font-size: 12px;
  color: var(--text-secondary);
  margin-bottom: 12px;
}

.percentage-col {
  width: 150px;
}

.progress-bar-wrapper {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.percentage-val {
  font-size: 11px;
  font-weight: 600;
  color: var(--text-secondary);
  text-align: right;
}

.progress-bar-bg {
  width: 100%;
  height: 6px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 3px;
  overflow: hidden;
}

.progress-bar-fill {
  height: 100%;
  background: var(--primary);
  border-radius: 3px;
  box-shadow: 0 0 5px var(--primary-glow);
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(5px); }
  to { opacity: 1; transform: translateY(0); }
}
</style>
