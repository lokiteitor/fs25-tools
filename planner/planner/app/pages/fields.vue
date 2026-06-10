<!-- app/pages/fields.vue -->
<template>
  <div class="fields-container">
    
    <!-- Controles Globales (Guardados en IndexedDB) -->
    <div class="glass-card controls-card">
      <h3 class="card-title">⚙️ Ajustes Económicos Globales</h3>
      <div class="controls-grid">
        <!-- Dificultad Económica (Movido al menú lateral) -->

        <!-- Sell Price Tipo -->
        <div class="control-item">
          <label for="sell-price-select">Precio de Venta</label>
          <select id="sell-price-select" v-model="sellPriceType" class="select-premium" @change="saveGlobalSettings">
            <option value="Baseline">Línea Base (Baseline)</option>
            <option value="MaxSeasonal">Precio Máximo Estacional</option>
          </select>
          <span class="control-help">Baseline (precio promedio), Máximo (mejor mes del año)</span>
        </div>
      </div>
    </div>

    <!-- Agregar Campo y Resumen Global -->
    <div class="grid-two-columns">
      <!-- Formulario Agregar Campo -->
      <div class="glass-card form-card">
        <h3 class="card-title">➕ Añadir Nuevo Campo</h3>
        <form @submit.prevent="addField" class="field-form">
          <div class="form-grid-fields">
            <div class="form-group">
              <label for="field-number">Nº Campo</label>
              <input 
                id="field-number" 
                type="number" 
                v-model.number="newFieldNumber" 
                required 
                min="1" 
                class="input-premium" 
                placeholder="Ej: 14"
              />
            </div>
            
            <div class="form-group">
              <label for="field-hectares">Hectáreas (ha)</label>
              <input 
                id="field-hectares" 
                type="number" 
                step="0.01" 
                v-model.number="newFieldHectares" 
                required 
                min="0.01" 
                class="input-premium" 
                placeholder="Ej: 2.5"
              />
            </div>

            <div class="form-group">
              <label for="field-bonus">Yield Bonus (%)</label>
              <div class="yield-input-wrapper">
                <input 
                  id="field-bonus" 
                  type="number" 
                  step="0.1"
                  v-model.number="newFieldYieldBonus" 
                  required 
                  min="0" 
                  max="200" 
                  class="input-premium" 
                  placeholder="Ej: 42.5"
                />
                <span class="pct-symbol">%</span>
              </div>
            </div>

            <div class="form-group">
              <label for="field-price">Precio Compra ($)</label>
              <input 
                id="field-price" 
                type="number" 
                min="0" 
                v-model.number="newFieldPurchasePrice" 
                class="input-premium" 
                placeholder="Ej: 150000"
              />
            </div>
          </div>

          <button type="submit" class="btn-premium btn-add-field mt-16">
            <span>🌾</span> Agregar Campo
          </button>
        </form>
      </div>

      <!-- Resumen Global de la Granja -->
      <div class="glass-card summary-card">
        <h3 class="card-title">📊 Resumen de Explotación</h3>
        <div class="summary-stats">
          <div class="stats-row-split">
            <div class="stat-box flex-1">
              <span class="stat-label">Campos Totales</span>
              <span class="stat-value">{{ fields.length }}</span>
            </div>
            <div class="stat-box flex-1">
              <span class="stat-label">Hectáreas Totales</span>
              <span class="stat-value">{{ totalHectares.toFixed(2) }} ha</span>
            </div>
          </div>
          <div class="stat-box">
            <span class="stat-label">Inversión en Tierras</span>
            <span class="stat-value text-warning">${{ totalLandInvestment.toLocaleString('es-ES', { maximumFractionDigits: 0 }) }}</span>
          </div>
          <div class="stat-box">
            <span class="stat-label">Ingresos Totales Sembrados</span>
            <span class="stat-value text-accent">${{ totalRevenue.toLocaleString('es-ES', { maximumFractionDigits: 0 }) }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Lista de Campos y Comparativa de Cultivos -->
    <div class="fields-list-section">
      <h2 class="section-title">🚜 Tus Campos Registrados</h2>
      
      <div v-if="fields.length === 0" class="no-fields glass-card">
        <p>No tienes campos registrados todavía. Utiliza el formulario superior para añadir tu primer campo.</p>
      </div>

      <div v-else class="fields-grid-list">
        <div 
          v-for="field in fields" 
          :key="field.id" 
          class="field-card glass-card"
          :class="{ 'field-card-selected': selectedFieldId === field.id }"
        >
          <div class="field-card-header">
            <div class="field-info-title">
              <span class="field-avatar">Campo {{ field.fieldNumber }}</span>
              <span class="field-size">{{ field.hectares }} ha</span>
              
              <!-- Input para editar Yield Bonus por campo -->
              <div class="field-bonus-edit-container">
                <label :for="'field-bonus-' + field.id" class="bonus-label">Yield Bonus:</label>
                <div class="bonus-input-wrapper">
                  <input 
                    :id="'field-bonus-' + field.id"
                    type="number" 
                    step="0.1"
                    min="0"
                    max="200"
                    :value="(field.yieldBonus !== undefined ? field.yieldBonus * 100 : 42.5).toFixed(1)"
                    @change="updateFieldYieldBonus(field, $event.target.value)"
                    class="input-premium bonus-inline-input"
                  />
                  <span class="pct-symbol-inline">%</span>
                </div>
              </div>

              <!-- Input para editar Precio de Compra por campo -->
              <div class="field-price-edit-container">
                <label :for="'field-price-' + field.id" class="price-label">Precio Compra:</label>
                <div class="price-input-wrapper">
                  <input 
                    :id="'field-price-' + field.id"
                    type="number" 
                    min="0"
                    :value="field.purchasePrice !== undefined ? field.purchasePrice : 0"
                    @change="updateFieldPurchasePrice(field, $event.target.value)"
                    class="input-premium price-inline-input"
                  />
                  <span class="price-symbol-inline">$</span>
                </div>
              </div>
            </div>
            
            <div class="field-actions">
              <button 
                class="btn-premium btn-secondary btn-sm" 
                @click.stop="toggleFieldDetails(field.id)"
              >
                {{ selectedFieldId === field.id ? 'Cerrar Comparativa' : 'Ver Comparativa' }}
              </button>
              <button 
                class="btn-premium btn-danger btn-sm" 
                @click.stop="deleteField(field.id)"
              >
                ✕
              </button>
            </div>
          </div>

          <!-- Si tiene cultivo asignado, mostrar resumen del cultivo -->
          <div class="field-assigned-crop-info">
            <div v-if="field.selectedCrop" class="assigned-crop-container">
              <div class="assigned-crop-details">
                <span class="badge badge-primary">Cultivado: {{ field.selectedCrop }}</span>
                <span class="badge badge-accent">${{ getAssignedCropIncome(field).toLocaleString('es-ES', { maximumFractionDigits: 0 }) }}</span>
              </div>
              <div class="assigned-crop-yields">
                <span>Rendimiento: <strong>{{ (getAssignedCropYieldM3(field) * 1000).toLocaleString('es-ES', { maximumFractionDigits: 0 }) }} L</strong></span>
                <span>(<strong>{{ getAssignedCropYieldTons(field).toFixed(2) }} Tons</strong>)</span>
              </div>
            </div>
            <div v-else class="assigned-crop-container no-crop">
              <span class="badge">⚠️ Sin cultivo seleccionado</span>
              <p class="no-crop-text">Haz click en "Ver Comparativa" para evaluar rendimientos y sembrar un cultivo.</p>
            </div>
          </div>

          <!-- Sección Detallada de Comparativa de Cultivos (Desplegable) -->
          <div v-if="selectedFieldId === field.id" class="crop-comparative-container">
            <h4 class="comparative-title">Comparativa de Cultivos para Campo {{ field.fieldNumber }} ({{ field.hectares }} ha con {{ ((field.yieldBonus !== undefined ? field.yieldBonus : 0.425) * 100).toFixed(1) }}% Yield Bonus)</h4>
            <p class="comparative-subtitle">Haz clic en "Sembrar" para guardar la decisión de siembra en este campo.</p>
            
            <div class="table-container">
              <table class="table-premium">
                <thead>
                  <tr>
                    <th>Cultivo</th>
                    <th>Rendimiento (L)</th>
                    <th>Rendimiento (Tons)</th>
                    <th>Semillas requeridas</th>
                    <th>Ingresos Estimados</th>
                    <th>Acción</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="cropCalculated in getCropComparisonForField(field)" :key="cropCalculated.name">
                    <td>
                      <strong>{{ cropCalculated.name }}</strong>
                    </td>
                    <td>{{ (cropCalculated.yieldM3 * 1000).toLocaleString('es-ES', { maximumFractionDigits: 0 }) }} L</td>
                    <td>{{ cropCalculated.yieldTons.toFixed(2) }} t</td>
                    <td>{{ cropCalculated.seedVolume.toFixed(0) }} L</td>
                    <td class="text-accent font-bold">${{ cropCalculated.income.toLocaleString('es-ES', { maximumFractionDigits: 2 }) }}</td>
                    <td>
                      <button 
                        class="btn-premium btn-sm"
                        :class="{ 'btn-secondary': field.selectedCrop === cropCalculated.name }"
                        @click="assignCropToField(field, cropCalculated.name)"
                      >
                        {{ field.selectedCrop === cropCalculated.name ? 'Sembrado ✓' : 'Sembrar' }}
                      </button>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

        </div>
      </div>
    </div>

    <!-- TABLA DE RENDIMIENTO TOTAL ACUMULADO POR CULTIVO SELECCIONADO (TODA LA GRANJA) -->
    <div class="accumulated-crops-section glass-card mt-24">
      <h3 class="card-title text-accent">📊 Total de Cosecha Planificada (Granja Consolidada)</h3>
      <p class="section-desc">
        Esta tabla muestra la **suma total consolidada** de los rendimientos e ingresos de tu granja **agrupados por los cultivos que has asignado** a tus campos registrados.
      </p>
      
      <div v-if="getAccumulatedComparison.length === 0" class="no-accumulated-data mt-16">
        <p>⚠️ No hay cultivos sembrados. Asigna un cultivo a tus campos para ver la producción consolidada de la temporada.</p>
      </div>

      <div v-else class="table-container">
        <table class="table-premium">
          <thead>
            <tr>
              <th>Cultivo</th>
              <th>Campos Sembrados</th>
              <th>Hectáreas Totales</th>
              <th>Producción Total (L)</th>
              <th>Producción Total (Tons)</th>
              <th>Semilla Total Requerida</th>
              <th>Ingresos Consolidados</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="accumulated in getAccumulatedComparison" :key="accumulated.name">
              <td>
                <strong>{{ accumulated.name }}</strong>
              </td>
              <td>{{ accumulated.fieldsCount }} {{ accumulated.fieldsCount === 1 ? 'campo' : 'campos' }}</td>
              <td>{{ accumulated.hectares.toFixed(2) }} ha</td>
              <td>{{ (accumulated.yieldM3 * 1000).toLocaleString('es-ES', { maximumFractionDigits: 0 }) }} L</td>
              <td>{{ accumulated.yieldTons.toFixed(2) }} t</td>
              <td>{{ accumulated.seedVolume.toFixed(0) }} L</td>
              <td class="text-accent font-bold">${{ accumulated.income.toLocaleString('es-ES', { maximumFractionDigits: 2 }) }}</td>
            </tr>
            <!-- Fila de Gran Total -->
            <tr class="grand-total-row">
              <td><strong>GRAN TOTAL</strong></td>
              <td>{{ fields.filter(f => f.selectedCrop).length }} campos</td>
              <td>{{ totalSembradoHectares.toFixed(2) }} ha</td>
              <td>{{ (totalSembradoM3 * 1000).toLocaleString('es-ES', { maximumFractionDigits: 0 }) }} L</td>
              <td>{{ totalSembradoTons.toFixed(2) }} t</td>
              <td>{{ totalSembradoSeed.toFixed(0) }} L</td>
              <td class="text-accent font-bold">${{ totalRevenue.toLocaleString('es-ES', { maximumFractionDigits: 2 }) }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useDB } from '~/composables/useDB'
import { crops } from '~/utils/cropData'
import { calculateYieldM3, calculateYieldTons } from '~/utils/cropCalculations'
import { useGlobalSettings } from '~/composables/useGlobalSettings'

definePageMeta({
  layout: 'default'
})

const db = useDB()

// Variables reactivas
const fields = ref([])
const newFieldNumber = ref(null)
const newFieldHectares = ref(null)
const newFieldYieldBonus = ref(42.5) // Default 42.5%
const newFieldPurchasePrice = ref(null)

const { difficulty } = useGlobalSettings()
const sellPriceType = ref('Baseline') // Default

const selectedFieldId = ref(null)

// Cargar configuraciones y campos al montar
onMounted(async () => {
  // Configuración global
  const savedSettings = await db.getSetting('global_settings', {
    difficulty: 'Normal',
    sellPrice: 'Baseline'
  })
  
  // difficulty is handled globally, sellPrice still here for now
  sellPriceType.value = savedSettings.sellPrice

  // Campos
  await loadFields()
})

// Cargar campos de IndexedDB
const loadFields = async () => {
  fields.value = await db.getAllFields()
}

// Guardar configuraciones globales
const saveGlobalSettings = async () => {
  const settingsToSave = {
    sellPrice: sellPriceType.value
  }
  await db.saveSetting('global_settings', settingsToSave)
}

// Agregar campo
const addField = async () => {
  if (!newFieldNumber.value || !newFieldHectares.value || newFieldYieldBonus.value === null) return

  const newField = {
    fieldNumber: newFieldNumber.value,
    hectares: newFieldHectares.value,
    yieldBonus: newFieldYieldBonus.value / 100, // guardar como decimal
    selectedCrop: '',
    purchasePrice: newFieldPurchasePrice.value || 0
  }

  await db.saveFieldItem(newField)
  newFieldNumber.value = null
  newFieldHectares.value = null
  newFieldYieldBonus.value = 42.5 // reset a default
  newFieldPurchasePrice.value = null
  
  await loadFields()
}

// Actualizar Yield Bonus de un campo existente
const updateFieldYieldBonus = async (field, percentValue) => {
  const parsedValue = parseFloat(percentValue)
  if (isNaN(parsedValue) || parsedValue < 0) return
  
  field.yieldBonus = parsedValue / 100
  await db.saveFieldItem(field)
  await loadFields()
}

// Actualizar Precio de Compra de un campo existente
const updateFieldPurchasePrice = async (field, priceValue) => {
  const parsedValue = parseFloat(priceValue)
  if (isNaN(parsedValue) || parsedValue < 0) return
  
  field.purchasePrice = parsedValue
  await db.saveFieldItem(field)
  await loadFields()
}

// Eliminar campo
const deleteField = async (id) => {
  if (confirm('¿Estás seguro de que deseas eliminar este campo?')) {
    await db.deleteFieldItem(id)
    if (selectedFieldId.value === id) {
      selectedFieldId.value = null
    }
    await loadFields()
  }
}

// Toggle desplegable de comparativa
const toggleFieldDetails = (fieldId) => {
  if (selectedFieldId.value === fieldId) {
    selectedFieldId.value = null
  } else {
    selectedFieldId.value = fieldId
  }
}

// Asignar cultivo a campo
const assignCropToField = async (field, cropName) => {
  field.selectedCrop = cropName
  await db.saveFieldItem(field)
  await loadFields()
}

// --- Cálculos de la Comparativa de Cultivos Individuales ---
const getCropComparisonForField = (field) => {
  const fieldBonus = field.yieldBonus !== undefined ? field.yieldBonus : 0.425
  const bonusScalar = 1 + fieldBonus
  const diffScalar = difficulty.value === 'Easy' ? 3.0 : difficulty.value === 'Normal' ? 1.8 : 1.0

  return crops.map(c => {
    const yieldM3 = calculateYieldM3(c.yield, field.hectares, bonusScalar)
    const yieldTons = calculateYieldTons(yieldM3, c.weight)
    
    const priceFactor = sellPriceType.value === 'MaxSeasonal' ? c.maxPrice : 1.0
    const finalPricePerLiter = c.price * priceFactor * diffScalar
    const liters = yieldM3 * 1000
    const income = liters * finalPricePerLiter
    const seedVolume = c.seed * field.hectares * 10000

    return {
      name: c.name,
      yieldM3,
      yieldTons,
      seedVolume,
      income
    }
  }).sort((a, b) => b.income - a.income)
}

// --- Getters auxiliares para cultivo asignado ---
const getAssignedCropIncome = (field) => {
  if (!field.selectedCrop) return 0
  const comparison = getCropComparisonForField(field)
  const found = comparison.find(c => c.name === field.selectedCrop)
  return found ? found.income : 0
}

const getAssignedCropYieldM3 = (field) => {
  if (!field.selectedCrop) return 0
  const comparison = getCropComparisonForField(field)
  const found = comparison.find(c => c.name === field.selectedCrop)
  return found ? found.yieldM3 : 0
}

const getAssignedCropYieldTons = (field) => {
  if (!field.selectedCrop) return 0
  const comparison = getCropComparisonForField(field)
  const found = comparison.find(c => c.name === field.selectedCrop)
  return found ? found.yieldTons : 0
}

const getAssignedCropSeed = (field) => {
  if (!field.selectedCrop) return 0
  const comparison = getCropComparisonForField(field)
  const found = comparison.find(c => c.name === field.selectedCrop)
  return found ? found.seedVolume : 0
}

// --- TABLA DE RENDIMIENTO TOTAL ACUMULADO POR CULTIVOS SELECCIONADOS REALES ---
const getAccumulatedComparison = computed(() => {
  const diffScalar = difficulty.value === 'Easy' ? 3.0 : difficulty.value === 'Normal' ? 1.8 : 1.0
  const accumulatedMap = {}

  fields.value.forEach(field => {
    if (!field.selectedCrop) return // Omitir campos sin cultivar asignado

    const cropName = field.selectedCrop
    const c = crops.find(item => item.name === cropName)
    if (!c) return

    const fieldBonus = field.yieldBonus !== undefined ? field.yieldBonus : 0.425
    const bonusScalar = 1 + fieldBonus
    
    const yieldM3 = calculateYieldM3(c.yield, field.hectares, bonusScalar)
    const yieldTons = calculateYieldTons(yieldM3, c.weight)
    
    const priceFactor = sellPriceType.value === 'MaxSeasonal' ? c.maxPrice : 1.0
    const finalPricePerLiter = c.price * priceFactor * diffScalar
    const liters = yieldM3 * 1000
    const income = liters * finalPricePerLiter
    const seedVolume = c.seed * field.hectares * 10000

    if (!accumulatedMap[cropName]) {
      accumulatedMap[cropName] = {
        name: cropName,
        fieldsCount: 0,
        hectares: 0,
        yieldM3: 0,
        yieldTons: 0,
        seedVolume: 0,
        income: 0
      }
    }

    accumulatedMap[cropName].fieldsCount += 1
    accumulatedMap[cropName].hectares += field.hectares
    accumulatedMap[cropName].yieldM3 += yieldM3
    accumulatedMap[cropName].yieldTons += yieldTons
    accumulatedMap[cropName].seedVolume += seedVolume
    accumulatedMap[cropName].income += income
  })

  return Object.values(accumulatedMap).sort((a, b) => b.income - a.income)
})

// --- Totales Consolidados Sembrados ---
const totalSembradoHectares = computed(() => {
  return fields.value.reduce((sum, f) => sum + (f.selectedCrop ? f.hectares : 0), 0)
})

const totalSembradoM3 = computed(() => {
  return fields.value.reduce((sum, f) => sum + getAssignedCropYieldM3(f), 0)
})

const totalSembradoTons = computed(() => {
  return fields.value.reduce((sum, f) => sum + getAssignedCropYieldTons(f), 0)
})

const totalSembradoSeed = computed(() => {
  return fields.value.reduce((sum, f) => sum + getAssignedCropSeed(f), 0)
})

const totalHectares = computed(() => {
  return fields.value.reduce((sum, f) => sum + f.hectares, 0)
})

const totalRevenue = computed(() => {
  return fields.value.reduce((sum, f) => sum + getAssignedCropIncome(f), 0)
})

// Inversión total en tierras
const totalLandInvestment = computed(() => {
  return fields.value.reduce((sum, f) => sum + (f.purchasePrice || 0), 0)
})
</script>

<style scoped>
.fields-container {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.card-title {
  font-size: 16px;
  font-weight: 700;
  color: var(--primary);
  margin-bottom: 16px;
}

.card-title.mb-0 {
  margin-bottom: 0;
}

.controls-card {
  background: linear-gradient(135deg, rgba(18, 30, 25, 0.8) 0%, rgba(0, 0, 0, 0.4) 100%);
}

.controls-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 20px;
}

.control-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.control-item label {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-primary);
}

.control-help {
  font-size: 11px;
  color: var(--text-muted);
}

.grid-two-columns {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
  gap: 24px;
  align-items: start;
}

.form-card {
  border-left: 4px solid var(--primary);
}

.field-form {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.form-grid-fields {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(110px, 1fr));
  gap: 12px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.form-group label {
  font-size: 13px;
  font-weight: 600;
}

.yield-input-wrapper {
  position: relative;
  display: flex;
  align-items: center;
}

.yield-input-wrapper input {
  padding-right: 28px;
}

.pct-symbol {
  position: absolute;
  right: 12px;
  color: var(--text-secondary);
  font-weight: 600;
  font-size: 14px;
  pointer-events: none;
}

.btn-add-field {
  margin-top: 4px;
  width: 100%;
}

.summary-stats {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.stats-row-split {
  display: flex;
  gap: 12px;
}

.flex-1 {
  flex: 1;
}

.stat-box {
  background: rgba(0, 0, 0, 0.25);
  border: 1px solid var(--border-color);
  border-radius: 10px;
  padding: 12px 16px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.stat-label {
  font-size: 13px;
  color: var(--text-secondary);
  font-weight: 500;
}

.stat-value {
  font-size: 18px;
  font-weight: 800;
}

.text-accent {
  color: var(--primary);
}

.text-warning {
  color: var(--accent);
}

.ml-8 {
  margin-left: 8px;
}

.section-title {
  font-size: 20px;
  font-weight: 800;
  color: var(--text-primary);
  margin-bottom: 16px;
}

.no-fields {
  text-align: center;
  padding: 40px;
  color: var(--text-secondary);
}

.fields-grid-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.field-card {
  transition: var(--transition-smooth);
}

.field-card-selected {
  border-color: var(--primary);
  box-shadow: 0 0 20px rgba(46, 213, 115, 0.15);
}

.field-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-bottom: 16px;
  border-bottom: 1px solid var(--border-color);
  flex-wrap: wrap;
  gap: 16px;
}

.field-info-title {
  display: flex;
  align-items: center;
  gap: 16px;
  flex-wrap: wrap;
}

.field-avatar {
  font-weight: 800;
  font-size: 16px;
  color: var(--primary);
}

.field-size {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  padding: 4px 8px;
  border-radius: 6px;
  font-size: 13px;
  font-weight: 600;
}

/* Selector inline para Yield Bonus */
.field-bonus-edit-container {
  display: flex;
  align-items: center;
  gap: 8px;
}

.bonus-label {
  font-size: 12px;
  color: var(--text-secondary);
  font-weight: 500;
}

.bonus-input-wrapper {
  position: relative;
  display: flex;
  align-items: center;
  width: 90px;
}

.bonus-inline-input {
  padding: 6px 20px 6px 8px;
  font-size: 12px;
  text-align: right;
  height: 30px;
}

.pct-symbol-inline {
  position: absolute;
  right: 8px;
  font-size: 12px;
  color: var(--text-secondary);
  pointer-events: none;
}

/* Selector inline para Precio de Compra */
.field-price-edit-container {
  display: flex;
  align-items: center;
  gap: 8px;
}

.price-label {
  font-size: 12px;
  color: var(--text-secondary);
  font-weight: 500;
}

.price-input-wrapper {
  position: relative;
  display: flex;
  align-items: center;
  width: 110px;
}

.price-inline-input {
  padding: 6px 20px 6px 8px;
  font-size: 12px;
  text-align: right;
  height: 30px;
}

.price-symbol-inline {
  position: absolute;
  right: 8px;
  font-size: 12px;
  color: var(--text-secondary);
  pointer-events: none;
}

.field-actions {
  display: flex;
  gap: 8px;
}

.btn-sm {
  padding: 6px 12px;
  font-size: 12px;
}

.field-assigned-crop-info {
  padding-top: 16px;
}

.assigned-crop-container {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 12px;
}

.assigned-crop-container.no-crop {
  flex-direction: column;
  align-items: flex-start;
  gap: 8px;
}

.no-crop-text {
  font-size: 12px;
  color: var(--text-muted);
}

.assigned-crop-details {
  display: flex;
  gap: 8px;
  align-items: center;
}

.assigned-crop-yields {
  font-size: 13px;
  color: var(--text-secondary);
  display: flex;
  gap: 6px;
}

.crop-comparative-container {
  margin-top: 24px;
  padding-top: 16px;
  border-top: 1px dashed var(--border-color);
  animation: fadeIn 0.3s ease-in-out;
}

.comparative-title {
  font-size: 14px;
  font-weight: 700;
  color: var(--primary);
  margin-bottom: 4px;
}

.comparative-subtitle {
  font-size: 12px;
  color: var(--text-muted);
  margin-bottom: 12px;
}

.font-bold {
  font-weight: 700;
}

/* Tabla acumulada */
.accumulated-crops-section {
  border-left: 4px solid var(--accent);
  background: linear-gradient(135deg, rgba(255, 165, 2, 0.03) 0%, rgba(18, 30, 25, 0.65) 100%);
}

.no-accumulated-data {
  text-align: center;
  padding: 24px;
  color: var(--text-secondary);
  font-size: 14px;
  border: 1px dashed var(--border-color);
  border-radius: 8px;
}

.section-desc {
  font-size: 13px;
  color: var(--text-secondary);
  line-height: 1.5;
  margin-bottom: 12px;
}

.grand-total-row td {
  border-top: 2px solid var(--border-color);
  font-weight: 800;
  background: rgba(46, 213, 115, 0.08);
  color: var(--primary);
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(5px); }
  to { opacity: 1; transform: translateY(0); }
}

@media (max-width: 900px) {
  .form-grid-fields {
    grid-template-columns: 1fr;
    gap: 12px;
  }
}
</style>
