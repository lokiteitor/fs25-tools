<!-- app/pages/animals/horses.vue -->
<template>
  <div class="horses-container">
    <div class="grid-layout">
      
      <!-- Panel de Inputs (Configuración) -->
      <div class="glass-card config-card">
        <h3 class="card-title">🐴 Configuración de Establos</h3>
        
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
            <label for="num-horses">Número de Caballos</label>
            <input 
              id="num-horses" 
              type="number" 
              v-model.number="inputs.numHorses" 
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
            <label for="sell-count">Caballos vendidos/año</label>
            <input 
              id="sell-count" 
              type="number" 
              v-model.number="inputs.sellCount" 
              class="input-premium" 
              min="0"
              @input="saveConfig"
            />
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
            <span class="control-help">Requerido para generar estiércol (manure). Los caballos no generan purín (slurry).</span>
          </div>

          <!-- Selectores de cultivo por categoría -->
          <div class="form-group border-top-dashed pt-12">
            <label for="base-crop">Alimento Base</label>
            <select id="base-crop" v-model="inputs.baseCrop" class="select-premium" @change="saveConfig">
              <option value="Oat">Avena (Oat)</option>
              <option value="Sorghum">Sorgo (Sorghum)</option>
            </select>
          </div>

          <div class="form-group border-top-dashed pt-12">
            <label for="root-crop">Alimento de Raíz</label>
            <select id="root-crop" v-model="inputs.rootCrop" class="select-premium" @change="saveConfig">
              <option value="Potato">Patata (Potato)</option>
              <option value="Sugarbeet">Remolacha Azucarera (Sugarbeet)</option>
              <option value="Redbeet">Remolacha Roja (Redbeet)</option>
              <option value="Parsnip">Chirivía (Parsnip)</option>
              <option value="Carrot">Zanahoria (Carrot)</option>
            </select>
          </div>
        </div>
      </div>

      <!-- Panel de Resultados de Producción e Ingresos -->
      <div class="glass-card results-card">
        <h3 class="card-title">💩 Producción & Ventas Equinas</h3>
        
        <div class="table-container">
          <table class="table-premium">
            <thead>
              <tr>
                <th>Detalle de Salida</th>
                <th>Anual</th>
                <th>Monetario / Estado</th>
              </tr>
            </thead>
            <tbody>
              <!-- Manure -->
              <tr :class="{ 'row-disabled': !inputs.provideStraw }">
                <td>
                  <strong>Estiércol (Manure)</strong>
                  <span v-if="!inputs.provideStraw" class="text-muted ml-8">(Requiere Paja)</span>
                </td>
                <td>{{ res.production.manure.toFixed(0) }} L</td>
                <td>—</td>
              </tr>

              <!-- Straw cama -->
              <tr :class="{ 'row-disabled': !inputs.provideStraw }">
                <td><strong>Paja cama consumida</strong></td>
                <td>{{ Math.abs(res.production.straw).toFixed(0) }} L</td>
                <td>—</td>
              </tr>

              <!-- Ventas anuales -->
              <tr class="total-row">
                <td><strong>VENTA ANUAL DE CABALLOS</strong></td>
                <td class="text-accent font-bold">${{ res.sales.horseSales.toLocaleString('es-ES') }}</td>
                <td class="text-accent font-bold">Por {{ inputs.sellCount }} Caballos</td>
              </tr>
            </tbody>
          </table>
        </div>

        <div class="beef-sales-section mt-24">
          <h4>Venta de Caballos de Raza</h4>
          <p class="section-desc">Los caballos alcanzan su precio máximo de venta ($5,000) a los 36 meses de edad si se entrenan correctamente al 100%.</p>
        </div>
      </div>

    </div>

    <!-- Desglose de Alimento y Hectáreas Necesarias -->
    <div class="grid-layout mt-24">
      
      <!-- Hectáreas de Campo Necesarias -->
      <div class="glass-card">
        <h3 class="card-title">🚜 Desglose de Alimentación y Trabajo de Campo</h3>
        <p class="section-desc">Hectáreas necesarias anuales por cultivo para producir el alimento de tus caballos de forma autosuficiente:</p>
        
        <div class="table-container">
          <table class="table-premium">
            <thead>
              <tr>
                <th>Categoría Alimento</th>
                <th>Cultivo Elegido</th>
                <th>Consumo Anual</th>
                <th>Hectáreas (ha)</th>
                <th>Acres (ac)</th>
              </tr>
            </thead>
            <tbody>
              <!-- Base (Avena o Sorgo) -->
              <tr>
                <td><strong>Base</strong></td>
                <td>{{ res.feedBreakdown.base.crop }}</td>
                <td>{{ res.feedBreakdown.base.liters.toFixed(0) }} L</td>
                <td>{{ res.feedBreakdown.base.hectares.toFixed(3) }} ha</td>
                <td>{{ (res.feedBreakdown.base.hectares / 0.4046856).toFixed(3) }} ac</td>
              </tr>

              <!-- Heno (Hay) -->
              <tr>
                <td><strong>Heno (Hay)</strong></td>
                <td>Hierba seca (Hay)</td>
                <td>{{ res.feedBreakdown.hay.liters.toFixed(0) }} L</td>
                <td>{{ res.feedBreakdown.hay.hectares.toFixed(3) }} ha</td>
                <td>{{ (res.feedBreakdown.hay.hectares / 0.4046856).toFixed(3) }} ac</td>
              </tr>

              <!-- Raíz -->
              <tr>
                <td><strong>Raíz</strong></td>
                <td>{{ res.feedBreakdown.root.crop }}</td>
                <td>{{ res.feedBreakdown.root.liters.toFixed(0) }} L</td>
                <td>{{ res.feedBreakdown.root.hectares.toFixed(4) }} ha</td>
                <td>{{ (res.feedBreakdown.root.hectares / 0.4046856).toFixed(4) }} ac</td>
              </tr>

              <!-- Totalizador -->
              <tr class="total-row">
                <td><strong>TOTAL CULTIVO</strong></td>
                <td>Alimentación Completa</td>
                <td>{{ res.production.totalFeed.toFixed(0) }} L</td>
                <td class="text-accent font-bold">{{ res.feedBreakdown.totalHectares.toFixed(2) }} ha</td>
                <td class="text-accent font-bold">{{ (res.feedBreakdown.totalHectares / 0.4046856).toFixed(2) }} ac</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Notas sobre la alimentación de Caballos -->
      <div class="glass-card">
        <h3 class="card-title">💡 Datos del Establos Equinos</h3>
        <ul class="info-list">
          <li><strong>Salud y Entrenamiento:</strong> Los caballos consumen alimento base (avena o sorgo), heno y cultivos de raíz. Para maximizar su salud (100%), puedes proveerles cualquier tipo de alimento de forma individual. La mecánica de caballos es simple pero flexible.</li>
          <li><strong>Cama de Paja:</strong> Proveer paja es opcional pero altamente recomendado si deseas producir estiércol (manure) para fertilizar tus propios campos de cultivo de forma gratuita. Los caballos no generan purín líquido (slurry).</li>
          <li><strong>Cultivos de Raíz:</strong> Aunque los cultivos de raíz (como patatas, remolachas o zanahorias) no se mencionan explícitamente en la ayuda oficial del juego de FS25 para caballos, el código del juego los acepta como un alimento válido de alta calidad.</li>
        </ul>
      </div>

    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { useDB } from '~/composables/useDB'
import { calculateHorses } from '~/utils/animalCalculations'

definePageMeta({
  layout: 'default'
})

const db = useDB()

// Lista de establos y filtro
const stables = ref([])
const filteredStables = computed(() => {
  return stables.value.filter(s => s.type === 'Horse')
})

// Inputs reactivos
const inputs = reactive({
  selectedStableName: '',
  numHorses: 16,
  yieldBonus: 0.425,
  grassHarvests: 2,
  sellCount: 2,
  provideStraw: true,
  baseCrop: 'Oat',
  rootCrop: 'Potato'
})

const yieldBonusPct = ref(42.5)

// Resultados calculados
const res = computed(() => {
  inputs.yieldBonus = yieldBonusPct.value / 100
  return calculateHorses(inputs)
})

// Cargar de IndexedDB
onMounted(async () => {
  // Cargar establos
  const savedStables = await db.getSetting('registered_stables', null)
  if (savedStables && Array.isArray(savedStables)) {
    stables.value = savedStables
  }

  // Cargar config global animal
  const saved = await db.getSetting('animal_horses', null)
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
      inputs.numHorses = stable.currentCount
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
      stable.currentCount = inputs.numHorses
      stable.settings = JSON.parse(JSON.stringify(inputs))
      await db.saveSetting('registered_stables', JSON.parse(JSON.stringify(stables.value)))
    }
  }

  await db.saveSetting('animal_horses', { ...inputs })
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
      inputs.numHorses = stable.currentCount
    }
  }
  yieldBonusPct.value = inputs.yieldBonus * 100
  await saveConfig()
}

const handleCountChange = async () => {
  if (inputs.selectedStableName) {
    const stable = stables.value.find(s => s.name === inputs.selectedStableName)
    if (stable) {
      if (inputs.numHorses < 0) inputs.numHorses = 0
      if (inputs.numHorses > stable.maxCapacity) {
        inputs.numHorses = stable.maxCapacity
      }
      stable.currentCount = inputs.numHorses
      stable.settings = JSON.parse(JSON.stringify(inputs))
      await db.saveSetting('registered_stables', JSON.parse(JSON.stringify(stables.value)))
    }
  }
  await saveConfig()
}
</script>

<style scoped>
.horses-container {
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

.border-top-dashed {
  border-top: 1px dashed var(--border-color);
}

.pt-12 {
  padding-top: 12px;
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
