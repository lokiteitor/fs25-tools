<!-- app/pages/animals/pigs.vue -->
<template>
  <div class="pigs-container">
    <div class="grid-layout">
      
      <!-- Panel de Inputs (Configuración) -->
      <div class="glass-card config-card">
        <h3 class="card-title">🐷 Configuración de Pocilga</h3>
        
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
            <label for="num-pigs">Número de Cerdos</label>
            <input 
              id="num-pigs" 
              type="number" 
              v-model.number="inputs.numPigs" 
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
            <label for="sell-count">Cerdos vendidos/año</label>
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
            <span class="control-help">Requerido para generar estiércol (manure). Los cerdos comen un extra de paja para su cama.</span>
          </div>

          <!-- Selectores de cultivo por categoría -->
          <div class="form-group border-top-dashed pt-12">
            <label for="base-crop">Cultivo Base (50%)</label>
            <select id="base-crop" v-model="inputs.baseCrop" class="select-premium" @change="saveConfig">
              <option value="Corn">Maíz (Corn)</option>
              <option value="Sorghum">Sorgo (Sorghum)</option>
            </select>
          </div>

          <div class="form-group border-top-dashed pt-12">
            <label for="grain-crop">Cultivo Grano (25%)</label>
            <select id="grain-crop" v-model="inputs.grainCrop" class="select-premium" @change="saveConfig">
              <option value="Wheat">Trigo (Wheat)</option>
              <option value="Barley">Cebada (Barley)</option>
            </select>
          </div>

          <div class="form-group border-top-dashed pt-12">
            <label for="protein-crop">Cultivo Proteico (20%)</label>
            <select id="protein-crop" v-model="inputs.proteinCrop" class="select-premium" @change="saveConfig">
              <option value="Soy">Soja (Soy)</option>
              <option value="Canola">Canola</option>
              <option value="Sunflower">Girasol (Sunflower)</option>
            </select>
          </div>

          <div class="form-group border-top-dashed pt-12">
            <label for="root-crop">Cultivo de Raíz (5%)</label>
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
        <h3 class="card-title">💩 Producción de Residuos & Ventas</h3>
        
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
              <!-- Slurry -->
              <tr>
                <td><strong>Purín (Slurry)</strong></td>
                <td>{{ res.production.slurry.toFixed(0) }} L</td>
                <td>—</td>
              </tr>
              
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
                <td><strong>VENTA ANUAL DE CERDOS</strong></td>
                <td class="text-accent font-bold">${{ res.sales.porkSales.toLocaleString('es-ES') }}</td>
                <td class="text-accent font-bold">Por {{ inputs.sellCount }} Cerdos</td>
              </tr>
            </tbody>
          </table>
        </div>

        <div class="beef-sales-section mt-24">
          <h4>Venta de Cerdos de Carne</h4>
          <p class="section-desc">Los cerdos alcanzan su precio máximo de venta ($2,500) a los 24 meses de edad.</p>
        </div>
      </div>

    </div>

    <!-- Desglose de Alimento y Hectáreas Necesarias -->
    <div class="grid-layout mt-24">
      
      <!-- Hectáreas de Campo Necesarias -->
      <div class="glass-card">
        <h3 class="card-title">🚜 Desglose de Alimentación y Trabajo de Campo</h3>
        <p class="section-desc">Hectáreas necesarias anuales por cultivo para producir el alimento de forma autosuficiente:</p>
        
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
              <!-- Base (50%) -->
              <tr>
                <td><strong>Base (50%)</strong></td>
                <td>{{ res.feedBreakdown.base.crop }}</td>
                <td>{{ res.feedBreakdown.base.liters.toFixed(0) }} L</td>
                <td>{{ res.feedBreakdown.base.hectares.toFixed(3) }} ha</td>
                <td>{{ (res.feedBreakdown.base.hectares / 0.4046856).toFixed(3) }} ac</td>
              </tr>

              <!-- Grano (25%) -->
              <tr>
                <td><strong>Grano (25%)</strong></td>
                <td>{{ res.feedBreakdown.grain.crop }}</td>
                <td>{{ res.feedBreakdown.grain.liters.toFixed(0) }} L</td>
                <td>{{ res.feedBreakdown.grain.hectares.toFixed(3) }} ha</td>
                <td>{{ (res.feedBreakdown.grain.hectares / 0.4046856).toFixed(3) }} ac</td>
              </tr>

              <!-- Proteína (20%) -->
              <tr>
                <td><strong>Proteína (20%)</strong></td>
                <td>{{ res.feedBreakdown.protein.crop }}</td>
                <td>{{ res.feedBreakdown.protein.liters.toFixed(0) }} L</td>
                <td>{{ res.feedBreakdown.protein.hectares.toFixed(3) }} ha</td>
                <td>{{ (res.feedBreakdown.protein.hectares / 0.4046856).toFixed(3) }} ac</td>
              </tr>

              <!-- Raíz (5%) -->
              <tr>
                <td><strong>Raíz (5%)</strong></td>
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

      <!-- Notas sobre la alimentación de Cerdos -->
      <div class="glass-card">
        <h3 class="card-title">💡 Datos de Alimentación Porcina</h3>
        <ul class="info-list">
          <li><strong>Alimentación Eficiente:</strong> Para obtener el 100% de la salud de los cerdos, debes proveerles una dieta mixta. Puedes alcanzar el 100% de salud alimentándolos con 1) solo alimento Base, 2) Grano + Proteína, o 3) Grano + Raíz.</li>
          <li><strong>Velocidad de Recuperación:</strong> El alimento base (maíz/sorgo) aumenta la salud del cerdo más rápido que el grano. El grano recupera salud más rápido que la proteína, y esta última más rápido que los cultivos de raíz.</li>
          <li><strong>Simplificación:</strong> Si planeas alimentar tus cerdos usando una dieta simplificada, puedes ignorar los campos de las categorías que decidas no proveer. Los cerdos consumirán siempre una cantidad fija de cada tipo de alimento si está presente.</li>
        </ul>
      </div>

    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { useDB } from '~/composables/useDB'
import { calculatePigs } from '~/utils/animalCalculations'
import { useGlobalSettings } from '~/composables/useGlobalSettings'

definePageMeta({
  layout: 'default'
})

const db = useDB()
const { difficulty: globalDifficulty } = useGlobalSettings()

// Lista de establos y filtro
const stables = ref([])
const filteredStables = computed(() => {
  return stables.value.filter(s => s.type === 'Pig')
})

// Inputs reactivos
const inputs = reactive({
  selectedStableName: '',
  numPigs: 32,
  yieldBonus: 0.425,
  difficulty: 'Easy',
  sellPriceType: 'MaxSeasonal',
  sellCount: 16,
  provideStraw: true,
  baseCrop: 'Corn',
  grainCrop: 'Wheat',
  proteinCrop: 'Soy',
  rootCrop: 'Potato'
})

const yieldBonusPct = ref(42.5)

// Resultados calculados
const res = computed(() => {
  inputs.yieldBonus = yieldBonusPct.value / 100
  inputs.difficulty = globalDifficulty.value
  return calculatePigs(inputs)
})

// Cargar de IndexedDB
onMounted(async () => {
  // Cargar establos
  const savedStables = await db.getSetting('registered_stables', null)
  if (savedStables && Array.isArray(savedStables)) {
    stables.value = savedStables
  }

  // Cargar config global animal
  const saved = await db.getSetting('animal_pigs', null)
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
      inputs.numPigs = stable.currentCount
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
      stable.currentCount = inputs.numPigs
      stable.settings = JSON.parse(JSON.stringify(inputs))
      await db.saveSetting('registered_stables', JSON.parse(JSON.stringify(stables.value)))
    }
  }

  await db.saveSetting('animal_pigs', { ...inputs })
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
      inputs.numPigs = stable.currentCount
    }
  }
  yieldBonusPct.value = inputs.yieldBonus * 100
  await saveConfig()
}

const handleCountChange = async () => {
  if (inputs.selectedStableName) {
    const stable = stables.value.find(s => s.name === inputs.selectedStableName)
    if (stable) {
      if (inputs.numPigs < 0) inputs.numPigs = 0
      if (inputs.numPigs > stable.maxCapacity) {
        inputs.numPigs = stable.maxCapacity
      }
      stable.currentCount = inputs.numPigs
      stable.settings = JSON.parse(JSON.stringify(inputs))
      await db.saveSetting('registered_stables', JSON.parse(JSON.stringify(stables.value)))
    }
  }
  await saveConfig()
}
</script>

<style scoped>
.pigs-container {
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

.beef-sales-section h4 {
  font-size: 14px;
  font-weight: 700;
  color: var(--primary);
  margin-bottom: 4px;
}

.ml-8 {
  margin-left: 8px;
}

.mt-24 {
  margin-top: 24px;
}
</style>
