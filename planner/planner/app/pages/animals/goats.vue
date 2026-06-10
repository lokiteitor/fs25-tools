<template>
  <div class="goats-container">
    <div class="grid-layout">
      
      <!-- Panel de Inputs (Configuración) -->
      <div class="glass-card config-card">
        <h3 class="card-title">🐐 Configuración de Aprisco</h3>
        
        <div class="form-grid">
          <div class="form-group">
            <label for="selected-goats-stable">Vincular Establo Cabras</label>
            <select 
              id="selected-goats-stable" 
              v-model="inputs.selectedGoatsStableName" 
              class="select-premium" 
              @change="handleGoatsStableChange"
            >
              <option value="">Ninguno (Control Manual)</option>
              <option 
                v-for="stable in goatsStables" 
                :key="stable.name" 
                :value="stable.name"
              >
                {{ stable.name }} ({{ stable.currentCount }}/{{ stable.maxCapacity }})
              </option>
            </select>
          </div>

          <div class="form-group">
            <label for="num-goats">Número de Cabras</label>
            <input 
              id="num-goats" 
              type="number" 
              v-model.number="inputs.numGoats" 
              class="input-premium" 
              min="0"
              @input="handleGoatsCountChange"
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

          <!-- Dificultad Económica (Movido a Global) -->

          <div class="form-group">
            <label for="sell-price-type">Precio de Venta</label>
            <select id="sell-price-type" v-model="inputs.sellPriceType" class="select-premium" @change="saveConfig">
              <option value="Baseline">Promedio (Baseline)</option>
              <option value="MaxSeasonal">Máximo Estacional</option>
            </select>
          </div>
        </div>
      </div>

      <!-- Panel de Producción de Leche -->
      <div class="glass-card results-card">
        <h3 class="card-title">🥛 Producción & Ventas de Leche</h3>
        
        <div class="table-container">
          <table class="table-premium">
            <thead>
              <tr>
                <th>Producto / Origen</th>
                <th>Mensual</th>
                <th>Anual</th>
                <th>Ingresos Estimados</th>
              </tr>
            </thead>
            <tbody>
              <!-- Leche de Cabra -->
              <tr :class="{ 'row-disabled': inputs.numGoats === 0 }">
                <td>
                  <strong>Leche de Cabra (Milk)</strong>
                  <span class="badge badge-accent ml-8">Cabras</span>
                </td>
                <td>{{ res.goatMilk.monthly.toFixed(0) }} L</td>
                <td>{{ res.goatMilk.yearly.toFixed(0) }} L</td>
                <td class="text-accent font-bold">${{ res.goatMilk.revenueYearly.toLocaleString('es-ES', { maximumFractionDigits: 0 }) }}/año</td>
              </tr>

              <!-- Totalizador -->
              <tr class="total-row">
                <td><strong>INGRESOS TOTALES</strong></td>
                <td>—</td>
                <td>—</td>
                <td class="text-accent font-bold">${{ res.goatMilk.revenueYearly.toLocaleString('es-ES', { maximumFractionDigits: 0 }) }}/año</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

    </div>

    <!-- Panel de Alimentación y Hectáreas Requeridas -->
    <div class="grid-layout mt-24">
      
      <!-- Hectáreas de Campo -->
      <div class="glass-card">
        <h3 class="card-title">🚜 Hectáreas de Pasto Requeridas</h3>
        <p class="section-desc">Área estimada de cultivo de hierba (Grass) necesaria para alimentar a tus cabras al año de forma autosuficiente:</p>
        
        <div class="table-container">
          <table class="table-premium">
            <thead>
              <tr>
                <th>Animales</th>
                <th>Alimento Anual</th>
                <th>Hectáreas (ha)</th>
                <th>Acres (ac)</th>
              </tr>
            </thead>
            <tbody>
              <tr :class="{ 'row-disabled': inputs.numGoats === 0 }">
                <td><strong>Cabras</strong></td>
                <td>{{ res.feed.yearly.toFixed(0) }} L</td>
                <td>{{ res.fieldwork.hectares.toFixed(3) }} ha</td>
                <td>{{ (res.fieldwork.hectares / 0.4046856).toFixed(3) }} ac</td>
              </tr>
              <tr class="total-row">
                <td><strong>TOTAL PASTO</strong></td>
                <td>{{ res.feed.totalYearly.toFixed(0) }} L</td>
                <td class="text-accent font-bold">{{ res.fieldwork.totalHectares.toFixed(2) }} ha</td>
                <td class="text-accent font-bold">{{ (res.fieldwork.totalHectares / 0.4046856).toFixed(2) }} ac</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Notas sobre Cabras -->
      <div class="glass-card">
        <h3 class="card-title">💡 Datos del Aprisco</h3>
        <ul class="info-list">
          <li><strong>Nutrición Simple:</strong> Las cabras en Farming Simulator 25 solo consumen pasto o heno. No requieren raciones mezcladas, lo que hace su mantenimiento muy simple.</li>
          <li><strong>Madurez del Hato:</strong> Los cálculos de producción de este menú asumen animales adultos (18 meses o más), que es cuando alcanzan su máxima tasa de producción. Los animales jóvenes consumen menos pero no producen leche.</li>
          <li><strong>Leche de Cabra:</strong> Tradicionalmente, la leche de cabra se vende a un precio por litro sustancialmente más alto que la lana en bruto, lo que puede hacer que las cabras sean una opción muy rentable si no deseas procesar lana en tejidos en una fábrica.</li>
        </ul>
      </div>

    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { useDB } from '~/composables/useDB'
import { calculateGoats } from '~/utils/animalCalculations'
import { useGlobalSettings } from '~/composables/useGlobalSettings'

definePageMeta({
  layout: 'default'
})

const db = useDB()
const { difficulty: globalDifficulty } = useGlobalSettings()

// Lista de establos y filtros por tipo
const stables = ref([])
const goatsStables = computed(() => {
  return stables.value.filter(s => s.type === 'Goat')
})

// Inputs reactivos
const inputs = reactive({
  selectedGoatsStableName: '',
  numGoats: 12,
  yieldBonus: 0.425,
  grassHarvests: 2,
  difficulty: 'Easy',
  sellPriceType: 'MaxSeasonal'
})

const yieldBonusPct = ref(42.5)

// Resultados calculados
const res = computed(() => {
  inputs.yieldBonus = yieldBonusPct.value / 100
  inputs.difficulty = globalDifficulty.value
  return calculateGoats(inputs)
})

// Cargar de IndexedDB
onMounted(async () => {
  // Cargar establos
  const savedStables = await db.getSetting('registered_stables', null)
  if (savedStables && Array.isArray(savedStables)) {
    stables.value = savedStables
  }

  // Cargar config global animal
  const saved = await db.getSetting('animal_goats', null)
  if (saved) {
    Object.assign(inputs, saved)
  }

  // Sincronizar cantidades y configuraciones si hay establos vinculados
  if (inputs.selectedGoatsStableName) {
    const stable = stables.value.find(s => s.name === inputs.selectedGoatsStableName)
    if (stable) {
      if (stable.settings) {
        Object.assign(inputs, stable.settings)
      } else {
        stable.settings = JSON.parse(JSON.stringify(inputs))
      }
      inputs.numGoats = stable.currentCount
    } else {
      inputs.selectedGoatsStableName = ''
    }
  }
  yieldBonusPct.value = inputs.yieldBonus * 100
})

// Guardar en IndexedDB
const saveConfig = async () => {
  inputs.yieldBonus = yieldBonusPct.value / 100

  let stablesChanged = false

  if (inputs.selectedGoatsStableName) {
    const stable = stables.value.find(s => s.name === inputs.selectedGoatsStableName)
    if (stable) {
      stable.currentCount = inputs.numGoats
      stable.settings = JSON.parse(JSON.stringify(inputs))
      stablesChanged = true
    }
  }

  if (stablesChanged) {
    await db.saveSetting('registered_stables', JSON.parse(JSON.stringify(stables.value)))
  }

  await db.saveSetting('animal_goats', { ...inputs })
}

const handleGoatsStableChange = async () => {
  if (inputs.selectedGoatsStableName) {
    const stable = stables.value.find(s => s.name === inputs.selectedGoatsStableName)
    if (stable) {
      if (stable.settings) {
        Object.assign(inputs, stable.settings)
      } else {
        stable.settings = JSON.parse(JSON.stringify(inputs))
      }
      inputs.numGoats = stable.currentCount
    }
  }
  yieldBonusPct.value = inputs.yieldBonus * 100
  await saveConfig()
}

const handleGoatsCountChange = async () => {
  if (inputs.selectedGoatsStableName) {
    const stable = stables.value.find(s => s.name === inputs.selectedGoatsStableName)
    if (stable) {
      if (inputs.numGoats < 0) inputs.numGoats = 0
      if (inputs.numGoats > stable.maxCapacity) {
        inputs.numGoats = stable.maxCapacity
      }
      stable.currentCount = inputs.numGoats
      stable.settings = JSON.parse(JSON.stringify(inputs))
      await db.saveSetting('registered_stables', JSON.parse(JSON.stringify(stables.value)))
    }
  }
  await saveConfig()
}
</script>

<style scoped>
.goats-container {
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

.ml-8 {
  margin-left: 8px;
}

.mt-24 {
  margin-top: 24px;
}
</style>
