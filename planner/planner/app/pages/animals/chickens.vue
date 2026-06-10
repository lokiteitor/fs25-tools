<!-- app/pages/animals/chickens.vue -->
<template>
  <div class="chickens-container">
    <div class="grid-layout">
      
      <!-- Panel de Inputs (Configuración) -->
      <div class="glass-card config-card">
        <h3 class="card-title">🐔 Configuración de Gallinero</h3>
        
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
            <label for="num-chx">Número de Gallinas</label>
            <input 
              id="num-chx" 
              type="number" 
              v-model.number="inputs.numChx" 
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

          <!-- Dificultad Económica (Movido a Global) -->

          <div class="form-group">
            <label for="feed-bought-pct">Porcentaje Alimento Comprado</label>
            <div class="input-wrapper">
              <input 
                id="feed-bought-pct" 
                type="number" 
                v-model.number="inputs.feedBoughtPercent" 
                class="input-premium" 
                min="0" 
                max="100"
                @input="saveConfig"
              />
              <span class="pct-symbol">%</span>
            </div>
          </div>

          <div class="form-group">
            <label for="fieldwork-crop">Cultivo para Sembrar</label>
            <select id="fieldwork-crop" v-model="inputs.fieldworkCrop" class="select-premium" @change="saveConfig">
              <option value="Barley">Cebada (Barley)</option>
              <option value="Wheat">Trigo (Wheat)</option>
              <option value="Sorghum">Sorgo (Sorghum)</option>
            </select>
            <span class="control-help">Para el {{ 100 - inputs.feedBoughtPercent }}% producido en granja</span>
          </div>

          <div class="form-group">
            <label for="feed-type">Tipo de Alimento Comprado</label>
            <select id="feed-type" v-model="inputs.feedType" class="select-premium" @change="saveConfig">
              <option value="Wheat">Sacos de Trigo (Wheat) [1.5/L]</option>
              <option value="Oat">Sacos de Avena (Oat) [1.4/L]</option>
            </select>
            <span class="control-help">Para el {{ inputs.feedBoughtPercent }}% comprado en tienda</span>
          </div>
        </div>
      </div>

      <!-- Panel de Resultados de Producción e Ingreso Neto -->
      <div class="glass-card results-card">
        <h3 class="card-title">🥚 Producción & Rentabilidad</h3>
        
        <div class="table-container">
          <table class="table-premium">
            <thead>
              <tr>
                <th>Detalle</th>
                <th>Mensual</th>
                <th>Anual</th>
              </tr>
            </thead>
            <tbody>
              <!-- Producción Huevos -->
              <tr>
                <td>
                  <strong>Producción de Huevos</strong>
                  <span class="badge badge-primary ml-8">Producto</span>
                </td>
                <td>{{ res.eggs.monthly.toFixed(0) }} L</td>
                <td>{{ res.eggs.yearly.toFixed(0) }} L</td>
              </tr>
              
              <!-- Ventas Huevos -->
              <tr>
                <td><strong>Ingreso por Huevos</strong></td>
                <td class="text-accent font-bold">${{ res.eggs.revenueMonthly.toLocaleString('es-ES', { maximumFractionDigits: 0 }) }}</td>
                <td class="text-accent font-bold">${{ res.eggs.revenueYearly.toLocaleString('es-ES', { maximumFractionDigits: 0 }) }}</td>
              </tr>

              <!-- Consumo Alimento -->
              <tr>
                <td><strong>Consumo de Alimento</strong></td>
                <td>{{ (res.feed.total / 12).toFixed(0) }} L</td>
                <td>{{ res.feed.total.toFixed(0) }} L</td>
              </tr>

              <!-- Costo Alimento -->
              <tr :class="{ 'row-disabled': inputs.feedBoughtPercent === 0 }">
                <td>
                  <strong>Costo Alimento Comprado</strong>
                  <span v-if="inputs.feedBoughtPercent > 0" class="text-muted ml-8">({{ inputs.feedBoughtPercent }}%)</span>
                </td>
                <td class="text-danger">-${{ res.feed.costMonthly.toLocaleString('es-ES', { maximumFractionDigits: 0 }) }}</td>
                <td class="text-danger">-${{ res.feed.costYearly.toLocaleString('es-ES', { maximumFractionDigits: 0 }) }}</td>
              </tr>

              <!-- Ingreso Neto -->
              <tr class="total-row">
                <td><strong>INGRESO NETO ESTIMADO</strong></td>
                <td class="text-accent font-bold">${{ res.net.monthly.toLocaleString('es-ES', { maximumFractionDigits: 0 }) }}</td>
                <td class="text-accent font-bold">${{ res.net.yearly.toLocaleString('es-ES', { maximumFractionDigits: 0 }) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

    </div>

    <!-- Sección de Fieldwork e Información -->
    <div class="grid-layout mt-24">
      
      <!-- Panel de Trabajo de Campo -->
      <div class="glass-card">
        <h3 class="card-title">🚜 Trabajo de Campo Necesario</h3>
        <p class="section-desc">Área de cultivo estimada para producir la porción del alimento cultivada en la granja ({{ 100 - inputs.feedBoughtPercent }}%):</p>
        
        <div class="table-container">
          <table class="table-premium">
            <thead>
              <tr>
                <th>Uso del Campo</th>
                <th>Cultivo Seleccionado</th>
                <th>Hectáreas (ha)</th>
                <th>Acres (ac)</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td><strong>Alimento de Gallinas</strong></td>
                <td>{{ inputs.fieldworkCrop }}</td>
                <td class="text-accent font-bold">{{ res.fieldwork.hectares.toFixed(2) }} ha</td>
                <td class="text-accent font-bold">{{ (res.fieldwork.hectares / 0.4046856).toFixed(2) }} ac</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Notas y Detalles de Nutrición -->
      <div class="glass-card">
        <h3 class="card-title">💡 Datos del Gallinero</h3>
        <ul class="info-list">
          <li><strong>Nutrición:</strong> Las gallinas se alimentan principalmente de granos: trigo, cebada o sorgo. El sorgo ofrece el menor rendimiento por hectárea, requiriendo más tierra, mientras que la cebada ofrece el mejor rendimiento por ha.</li>
          <li><strong>Comprar Alimento:</strong> Comprar sacos de alimento en la tienda es costoso. El trigo comprado cuesta $1.5/L y la avena $1.4/L. El sorgo no se vende en la tienda.</li>
          <li><strong>Salud y Producción:</strong> Este cálculo asume gallinas adultas de más de 6 meses de edad (que producen al 100%). Los animales más jóvenes consumen menos pero no ponen huevos.</li>
        </ul>
      </div>

    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { useDB } from '~/composables/useDB'
import { calculateChickens } from '~/utils/animalCalculations'
import { useGlobalSettings } from '~/composables/useGlobalSettings'

definePageMeta({
  layout: 'default'
})

const db = useDB()
const { difficulty: globalDifficulty } = useGlobalSettings()

// Lista de establos y filtro
const stables = ref([])
const filteredStables = computed(() => {
  return stables.value.filter(s => s.type === 'Chicken')
})

// Inputs reactivos
const inputs = reactive({
  selectedStableName: '',
  numChx: 96,
  yieldBonus: 0.425,
  difficulty: 'Easy',
  sellPriceType: 'MaxSeasonal',
  feedBoughtPercent: 0,
  feedType: 'Wheat',
  fieldworkCrop: 'Wheat'
})

const yieldBonusPct = ref(42.5)

// Resultados calculados
const res = computed(() => {
  inputs.yieldBonus = yieldBonusPct.value / 100
  inputs.difficulty = globalDifficulty.value
  return calculateChickens(inputs)
})

// Cargar de IndexedDB
onMounted(async () => {
  // Cargar establos
  const savedStables = await db.getSetting('registered_stables', null)
  if (savedStables && Array.isArray(savedStables)) {
    stables.value = savedStables
  }

  // Cargar config global animal
  const saved = await db.getSetting('animal_chickens', null)
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
      inputs.numChx = stable.currentCount
    } else {
      inputs.selectedStableName = ''
    }
  }
  yieldBonusPct.value = inputs.yieldBonus * 100
})

// Guardar en IndexedDB
const saveConfig = async () => {
  inputs.yieldBonus = yieldBonusPct.value / 100

  if (inputs.selectedStableName) {
    const stable = stables.value.find(s => s.name === inputs.selectedStableName)
    if (stable) {
      stable.currentCount = inputs.numChx
      stable.settings = JSON.parse(JSON.stringify(inputs))
      await db.saveSetting('registered_stables', JSON.parse(JSON.stringify(stables.value)))
    }
  }

  await db.saveSetting('animal_chickens', { ...inputs })
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
      inputs.numChx = stable.currentCount
    }
  }
  yieldBonusPct.value = inputs.yieldBonus * 100
  await saveConfig()
}

const handleCountChange = async () => {
  if (inputs.selectedStableName) {
    const stable = stables.value.find(s => s.name === inputs.selectedStableName)
    if (stable) {
      if (inputs.numChx < 0) inputs.numChx = 0
      if (inputs.numChx > stable.maxCapacity) {
        inputs.numChx = stable.maxCapacity
      }
      stable.currentCount = inputs.numChx
      stable.settings = JSON.parse(JSON.stringify(inputs))
      await db.saveSetting('registered_stables', JSON.parse(JSON.stringify(stables.value)))
    }
  }
  await saveConfig()
}
</script>

<style scoped>
.chickens-container {
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

.control-help {
  font-size: 11px;
  color: var(--text-muted);
}

.row-disabled {
  opacity: 0.4;
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

.info-list {
  padding-left: 20px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.info-list li {
  font-size: 14px;
  color: var(--text-secondary);
  line-height: 1.5;
}

.text-danger {
  color: var(--danger-hover);
  font-weight: 700;
}

.ml-8 {
  margin-left: 8px;
}

.mt-24 {
  margin-top: 24px;
}
</style>
