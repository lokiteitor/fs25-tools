<!-- app/pages/animals/cows.vue -->
<template>
  <div class="cows-container">
    <div class="grid-layout">
      
      <!-- Panel de Inputs (Configuración) -->
      <div class="glass-card config-card">
        <h3 class="card-title">🐮 Configuración de Hato</h3>
        
        <div class="form-grid">
          <div class="form-group">
            <label for="selected-stable">Vincular Establo</label>
            <select 
              id="selected-stable" 
              v-model="inputs.selectedStableName" 
              class="select-premium" 
              @change="handleStableChange"
            >
              <option value="">Ninguno (Control Manual)</option>
              <option 
                v-for="stable in filteredStables" 
                :key="stable.name" 
                :value="stable.name"
              >
                {{ stable.name }} ({{ stable.currentCount }}/{{ stable.maxCapacity }})
              </option>
            </select>
          </div>

          <div class="form-group">
            <label for="num-cows">Número de Vacas</label>
            <input 
              id="num-cows" 
              type="number" 
              v-model.number="inputs.numCows" 
              class="input-premium" 
              min="0"
              @input="handleCountChange"
            />
          </div>

          <div class="form-group">
            <label for="yield-bonus">Yield Bonus (%)</label>
            <div class="input-wrapper">
              <input 
                id="yield-bonus" 
                type="number" 
                v-model.number="yieldBonusPct" 
                class="input-premium" 
                min="0" 
                max="200"
                @input="saveConfig"
              />
              <span class="pct-symbol">%</span>
            </div>
          </div>

          <div class="form-group">
            <label for="grass-harvests">Cosechas de Pasto al Año</label>
            <input 
              id="grass-harvests" 
              type="number" 
              v-model.number="inputs.grassHarvests" 
              class="input-premium" 
              min="1" 
              max="10"
              @input="saveConfig"
            />
          </div>

          <div class="form-group">
            <label for="sell-count">Vacas vendidas/año</label>
            <input 
              id="sell-count" 
              type="number" 
              v-model.number="inputs.sellCount" 
              class="input-premium" 
              min="0"
              @input="saveConfig"
            />
          </div>

          <div class="form-group">
            <label for="silage-crop">Cultivo para Ensilaje</label>
            <select id="silage-crop" v-model="inputs.silageCrop" class="select-premium" @change="saveConfig">
              <option value="Corn">Maíz (Corn) [7.8x chaff]</option>
              <option value="Barley">Cebada (Barley) [4.0x chaff]</option>
              <option value="Wheat">Trigo (Wheat) [4.0x chaff]</option>
              <option value="Sorghum">Sorgo (Sorghum) [4.0x chaff]</option>
              <option value="Sunflower">Girasol (Sunflower) [6.0x chaff]</option>
              <option value="Oat">Avena (Oat) [4.0x chaff]</option>
              <option value="Canola">Canola [4.0x chaff]</option>
              <option value="Soybean">Soja (Soybean) [4.0x chaff]</option>
            </select>
          </div>

          <div class="form-group">
            <label for="feed-type">Tipo de Alimentación</label>
            <select id="feed-type" v-model="inputs.feedType" class="select-premium" @change="saveConfig">
              <option value="TMR">Ración Total Mezclada (TMR) [100% Prod.]</option>
              <option value="Simple">Pasto / Ensilaje Mezclado [100% Prod.]</option>
              <option value="Hay">Heno Simple [80% Prod.]</option>
              <option value="Grass">Hierba / Pasto Directo [40% Prod.]</option>
            </select>
          </div>

          <!-- Dificultad Económica (Movido a Global) -->

          <div class="form-group">
            <label for="sell-price-type">Precio de Venta Leche</label>
            <select id="sell-price-type" v-model="inputs.sellPriceType" class="select-premium" @change="saveConfig">
              <option value="Baseline">Promedio (Baseline)</option>
              <option value="MaxSeasonal">Máximo Estacional</option>
            </select>
          </div>

          <div class="form-group checkbox-group">
            <label class="checkbox-label">
              <input 
                type="checkbox" 
                v-model="inputs.provideStraw" 
                @change="saveConfig"
              />
              <span>Proveer Paja (Straw Bedding)</span>
            </label>
            <span class="control-help">Necesario para generar estiércol (manure) y obtener +11% de producción láctea.</span>
          </div>
        </div>
      </div>

      <!-- Panel de Resultados de Producción -->
      <div class="glass-card results-card">
        <h3 class="card-title">🥛 Producción & Consumo</h3>
        
        <div class="table-container">
          <table class="table-premium">
            <thead>
              <tr>
                <th>Producto / Insumo</th>
                <th>Mensual</th>
                <th>Anual</th>
                <th>Ganancia / Costo</th>
              </tr>
            </thead>
            <tbody>
              <!-- Leche -->
              <tr>
                <td>
                  <strong>Leche (Milk)</strong>
                  <span class="badge badge-primary ml-8">Producto</span>
                </td>
                <td>{{ res.production.milk.monthly.toFixed(0) }} L</td>
                <td>{{ res.production.milk.yearly.toFixed(0) }} L</td>
                <td class="text-accent font-bold">${{ res.production.milk.revenueYearly.toLocaleString('es-ES', { maximumFractionDigits: 0 }) }}/año</td>
              </tr>
              
              <!-- Comida -->
              <tr>
                <td><strong>Alimento (Food)</strong></td>
                <td>{{ Math.abs(res.production.food.monthly).toFixed(0) }} L</td>
                <td>{{ Math.abs(res.production.food.yearly).toFixed(0) }} L</td>
                <td>—</td>
              </tr>

              <!-- Purín -->
              <tr>
                <td><strong>Purín (Slurry)</strong></td>
                <td>{{ res.production.slurry.monthly.toFixed(0) }} L</td>
                <td>{{ res.production.slurry.yearly.toFixed(0) }} L</td>
                <td>—</td>
              </tr>

              <!-- Estiércol -->
              <tr :class="{ 'row-disabled': !inputs.provideStraw }">
                <td>
                  <strong>Estiércol (Manure)</strong>
                  <span v-if="!inputs.provideStraw" class="text-muted ml-8">(Requiere Paja)</span>
                </td>
                <td>{{ res.production.manure.monthly.toFixed(0) }} L</td>
                <td>{{ res.production.manure.yearly.toFixed(0) }} L</td>
                <td>—</td>
              </tr>

              <!-- Paja cama -->
              <tr :class="{ 'row-disabled': !inputs.provideStraw }">
                <td><strong>Paja Cama (Straw Bedding)</strong></td>
                <td>{{ Math.abs(res.production.straw.monthly).toFixed(0) }} L</td>
                <td>{{ Math.abs(res.production.straw.yearly).toFixed(0) }} L</td>
                <td>—</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

    </div>

    <!-- Sección de Trabajo de Campo e Insumos TMR -->
    <div class="grid-layout mt-24">
      
      <!-- Panel de Trabajo de Campo (Fieldwork Hectares) -->
      <div class="glass-card">
        <h3 class="card-title">🚜 Hectáreas de Campo Requeridas</h3>
        <p class="section-desc">Área de cultivo estimada para producir el alimento y cama de tu hato de forma autosuficiente al año:</p>
        
        <div class="table-container">
          <table class="table-premium">
            <thead>
              <tr>
                <th>Uso del Campo</th>
                <th>Cultivo / Método</th>
                <th>Hectáreas (ha)</th>
                <th>Acres (ac)</th>
              </tr>
            </thead>
            <tbody>
              <!-- Si es Hierba / Pasto Directo -->
              <tr v-if="inputs.feedType === 'Grass'">
                <td><strong>Hierba Directa (Pasto)</strong></td>
                <td>Hierba fresca (Grass)</td>
                <td>{{ res.fieldwork.simple.grass.toFixed(2) }} ha</td>
                <td>{{ (res.fieldwork.simple.grass / 0.4046856).toFixed(2) }} ac</td>
              </tr>

              <!-- Si es Heno Simple -->
              <tr v-else-if="inputs.feedType === 'Hay'">
                <td><strong>Heno Directo</strong></td>
                <td>Heno (Hierba Cosechada/Secada)</td>
                <td>{{ res.fieldwork.tmr.hayMix.toFixed(2) }} ha</td>
                <td>{{ (res.fieldwork.tmr.hayMix / 0.4046856).toFixed(2) }} ac</td>
              </tr>

              <!-- Si es Alimentación Simple Mezclada -->
              <template v-else-if="inputs.feedType === 'Simple'">
                <tr>
                  <td><strong>Pasto o Heno</strong></td>
                  <td>Hierba (Grass)</td>
                  <td>{{ res.fieldwork.simple.grass.toFixed(2) }} ha</td>
                  <td>{{ (res.fieldwork.simple.grass / 0.4046856).toFixed(2) }} ac</td>
                </tr>
                <tr>
                  <td><strong>Ensilaje Simple</strong></td>
                  <td>Ensilaje de {{ inputs.silageCrop }} (Silage)</td>
                  <td>{{ res.fieldwork.simple.silage.toFixed(2) }} ha</td>
                  <td>{{ (res.fieldwork.simple.silage / 0.4046856).toFixed(2) }} ac</td>
                </tr>
              </template>

              <!-- Si es Alimentación TMR -->
              <template v-else>
                <tr>
                  <td><strong>Paja en TMR (Straw Mix)</strong></td>
                  <td>Residuo de cereal</td>
                  <td>{{ res.fieldwork.tmr.strawMix.toFixed(4) }} ha</td>
                  <td>{{ (res.fieldwork.tmr.strawMix / 0.4046856).toFixed(4) }} ac</td>
                </tr>
                <tr>
                  <td><strong>Heno en TMR (Hay Mix)</strong></td>
                  <td>Hierba Cosechada (Grass)</td>
                  <td>{{ res.fieldwork.tmr.hayMix.toFixed(2) }} ha</td>
                  <td>{{ (res.fieldwork.tmr.hayMix / 0.4046856).toFixed(2) }} ac</td>
                </tr>
                <tr>
                  <td><strong>Ensilaje en TMR (Silage Mix)</strong></td>
                  <td>Chaff de {{ inputs.silageCrop }} Fermentado</td>
                  <td>{{ res.fieldwork.tmr.silageMix.toFixed(2) }} ha</td>
                  <td>{{ (res.fieldwork.tmr.silageMix / 0.4046856).toFixed(2) }} ac</td>
                </tr>
              </template>

              <!-- Cama de paja si aplica -->
              <tr :class="{ 'row-disabled': !inputs.provideStraw }">
                <td><strong>Cama de Paja (Bedding)</strong></td>
                <td>Cosecha de paja</td>
                <td>{{ res.fieldwork.strawBedding.toFixed(4) }} ha</td>
                <td>{{ (res.fieldwork.strawBedding / 0.4046856).toFixed(4) }} ac</td>
              </tr>

              <!-- Totalizador -->
              <tr class="total-row">
                <td><strong>TOTAL REQUERIDO</strong></td>
                <td>Autoabastecimiento</td>
                <td class="text-accent font-bold">{{ totalHectaresNeeded.toFixed(2) }} ha</td>
                <td class="text-accent font-bold">{{ (totalHectaresNeeded / 0.4046856).toFixed(2) }} ac</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Costos TMR e Ingresos por Ventas -->
      <div class="glass-card">
        <h3 class="card-title">💰 Costos TMR & Ventas de Carne</h3>
        
        <!-- Desglose TMR (Solo si se selecciona TMR) -->
        <div v-if="inputs.feedType === 'TMR'" class="tmr-breakdown-section">
          <h4>Detalle de Ración Total Mezclada (TMR) Anual</h4>
          <div class="tmr-grid">
            <div class="tmr-item">
              <span class="tmr-label">Heno (Hay) [37.44%]</span>
              <span class="tmr-val">{{ res.tmrUsage.hay.toFixed(0) }} L</span>
            </div>
            <div class="tmr-item">
              <span class="tmr-label">Ensilaje (Silage) [37.44%]</span>
              <span class="tmr-val">{{ res.tmrUsage.silage.toFixed(0) }} L</span>
            </div>
            <div class="tmr-item">
              <span class="tmr-label">Paja (Straw) [20.32%]</span>
              <span class="tmr-val">{{ res.tmrUsage.straw.toFixed(0) }} L</span>
            </div>
            <div class="tmr-item highlight-red">
              <span class="tmr-label">Alimento Mineral [4.8%]</span>
              <span class="tmr-val">{{ res.tmrUsage.mineral.toFixed(0) }} L</span>
            </div>
          </div>

          <div class="mineral-cost-box mt-16">
            <div class="cost-row">
              <span>Costo Alimento Mineral (Mensual)</span>
              <span class="text-danger">-${{ res.tmrUsage.mineralCostMonthly.toFixed(2) }}</span>
            </div>
            <div class="cost-row">
              <span>Costo Alimento Mineral (Anual)</span>
              <span class="text-danger">-${{ res.tmrUsage.mineralCostYearly.toFixed(2) }}</span>
            </div>
          </div>
        </div>

        <div v-else class="simple-feed-info">
          <p>La alimentación simple, con heno o hierba directa no requiere insumos comprados de Alimento Mineral. Todo el alimento puede ser cultivado o cosechado de forma gratuita en tu granja.</p>
        </div>

        <!-- Ventas de ganado de carne -->
        <div class="beef-sales-section mt-24">
          <h4>Venta Anual de Novillos de Carne</h4>
          <p class="section-desc">Asumiendo la venta de animales a los 36 meses de edad (precio máximo de $3,500):</p>
          <div class="sales-box mt-12">
            <div class="sales-row">
              <span>Venta de {{ inputs.sellCount }} cabezas/año</span>
              <span class="text-accent-gold font-bold">+${{ res.sales.beefSales.toLocaleString('es-ES') }}</span>
            </div>
          </div>
        </div>
      </div>

    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { useRoute } from 'vue-router'
import { calculateCows } from '~/utils/animalCalculations'
import { useGlobalSettings } from '~/composables/useGlobalSettings'

definePageMeta({
  layout: 'default'
})

const db = useDB()
const { difficulty: globalDifficulty } = useGlobalSettings()

// Lista de establos y filtro
const stables = ref([])
const filteredStables = computed(() => {
  return stables.value.filter(s => s.type === 'Cow')
})

// Inputs reactivos
const inputs = reactive({
  selectedStableName: '',
  numCows: 12,
  yieldBonus: 0.425,
  grassHarvests: 2,
  provideStraw: true,
  breed: 'Holstein',
  feedType: 'TMR',
  difficulty: 'Easy',
  sellPriceType: 'MaxSeasonal',
  sellCount: 4,
  silageCrop: 'Corn'
})

// Adaptador para yield bonus en porcentaje
const yieldBonusPct = ref(42.5)

// Resultados calculados
const res = computed(() => {
  inputs.yieldBonus = yieldBonusPct.value / 100
  inputs.difficulty = globalDifficulty.value
  return calculateCows(inputs)
})

// Cargar configuración de IndexedDB al montar
onMounted(async () => {
  // Cargar establos
  const savedStables = await db.getSetting('registered_stables', null)
  if (savedStables && Array.isArray(savedStables)) {
    stables.value = savedStables
  }

  // Cargar config animal global
  const saved = await db.getSetting('animal_cows', null)
  if (saved) {
    Object.assign(inputs, saved)
  }

  // Sincronizar cantidad y configuraciones si hay un establo vinculado
  if (inputs.selectedStableName) {
    const stable = stables.value.find(s => s.name === inputs.selectedStableName)
    if (stable) {
      if (stable.settings) {
        Object.assign(inputs, stable.settings)
      } else {
        stable.settings = JSON.parse(JSON.stringify(inputs))
      }
      inputs.numCows = stable.currentCount
    } else {
      inputs.selectedStableName = ''
    }
  }
  yieldBonusPct.value = inputs.yieldBonus * 100
})

// Guardar configuración en IndexedDB al cambiar
const saveConfig = async () => {
  inputs.yieldBonus = yieldBonusPct.value / 100

  if (inputs.selectedStableName) {
    const stable = stables.value.find(s => s.name === inputs.selectedStableName)
    if (stable) {
      stable.currentCount = inputs.numCows
      stable.settings = JSON.parse(JSON.stringify(inputs))
      await db.saveSetting('registered_stables', JSON.parse(JSON.stringify(stables.value)))
    }
  }

  await db.saveSetting('animal_cows', { ...inputs })
}

const handleStableChange = async () => {
  if (inputs.selectedStableName) {
    const stable = stables.value.find(s => s.name === inputs.selectedStableName)
    if (stable) {
      if (stable.settings) {
        Object.assign(inputs, stable.settings)
      } else {
        stable.settings = JSON.parse(JSON.stringify(inputs))
      }
      inputs.numCows = stable.currentCount
    }
  }
  yieldBonusPct.value = inputs.yieldBonus * 100
  await saveConfig()
}

const handleCountChange = async () => {
  if (inputs.selectedStableName) {
    const stable = stables.value.find(s => s.name === inputs.selectedStableName)
    if (stable) {
      if (inputs.numCows < 0) inputs.numCows = 0
      if (inputs.numCows > stable.maxCapacity) {
        inputs.numCows = stable.maxCapacity
      }
      stable.currentCount = inputs.numCows
      stable.settings = JSON.parse(JSON.stringify(inputs))
      await db.saveSetting('registered_stables', JSON.parse(JSON.stringify(stables.value)))
    }
  }
await saveConfig()
}

// Hectáreas Totales Requeridas
const totalHectaresNeeded = computed(() => {
  if (inputs.feedType === 'Grass') {
    return res.value.fieldwork.simple.grass + res.value.fieldwork.strawBedding
  } else if (inputs.feedType === 'Hay') {
    return res.value.fieldwork.tmr.hayMix + res.value.fieldwork.strawBedding
  } else if (inputs.feedType === 'Simple') {
    return res.value.fieldwork.simple.grass + res.value.fieldwork.simple.silage + res.value.fieldwork.strawBedding
  } else {
    return res.value.fieldwork.tmr.totalTmrHectares
  }
})
</script>

<style scoped>
.cows-container {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.grid-layout {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
  gap: 24px;
}

.card-title {
  font-size: 16px;
  font-weight: 700;
  color: var(--primary);
  margin-bottom: 16px;
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 16px;
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

.input-wrapper {
  position: relative;
  display: flex;
  align-items: center;
}

.input-wrapper input {
  padding-right: 32px;
}

.pct-symbol {
  position: absolute;
  right: 12px;
  color: var(--text-secondary);
  font-weight: 600;
  font-size: 14px;
  pointer-events: none;
}

.checkbox-group {
  grid-column: 1 / -1;
  display: flex;
  flex-direction: column;
  gap: 4px;
  margin-top: 8px;
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
}

.checkbox-label input {
  width: 16px;
  height: 16px;
  accent-color: var(--primary);
}

.control-help {
  font-size: 11px;
  color: var(--text-muted);
}

.row-disabled {
  opacity: 0.4;
  text-decoration: line-through;
}

.total-row td {
  border-top: 2px solid var(--border-color);
  font-size: 15px;
  background: rgba(46, 213, 115, 0.05);
}

.section-desc {
  font-size: 13px;
  color: var(--text-secondary);
  margin-bottom: 12px;
}

.tmr-breakdown-section h4 {
  font-size: 14px;
  font-weight: 700;
  color: var(--primary);
  margin-bottom: 12px;
}

.tmr-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 8px;
}

.tmr-item {
  background: rgba(0, 0, 0, 0.2);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  padding: 8px 12px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.tmr-item.highlight-red {
  border-color: rgba(255, 71, 87, 0.3);
  background: rgba(255, 71, 87, 0.05);
}

.tmr-label {
  font-size: 11px;
  color: var(--text-secondary);
}

.tmr-val {
  font-size: 14px;
  font-weight: 700;
}

.mineral-cost-box {
  background: rgba(255, 71, 87, 0.08);
  border: 1px solid rgba(255, 71, 87, 0.2);
  border-radius: 8px;
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.cost-row {
  display: flex;
  justify-content: space-between;
  font-size: 13px;
  font-weight: 500;
}

.text-danger {
  color: var(--danger-hover);
  font-weight: 700;
}

.simple-feed-info {
  font-size: 13px;
  color: var(--text-secondary);
  line-height: 1.5;
  padding: 16px;
  background: rgba(255, 255, 255, 0.02);
  border: 1px dashed var(--border-color);
  border-radius: 8px;
}

.beef-sales-section h4 {
  font-size: 14px;
  font-weight: 700;
  color: var(--primary);
  margin-bottom: 4px;
}

.sales-box {
  background: rgba(255, 165, 2, 0.08);
  border: 1px solid rgba(255, 165, 2, 0.2);
  border-radius: 8px;
  padding: 12px;
}

.sales-row {
  display: flex;
  justify-content: space-between;
  font-size: 14px;
}

.text-accent-gold {
  color: var(--accent);
}

.ml-8 {
  margin-left: 8px;
}

.mt-12 {
  margin-top: 12px;
}

.mt-16 {
  margin-top: 16px;
}

.mt-24 {
  margin-top: 24px;
}
</style>
