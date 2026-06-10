<!-- app/pages/stables.vue -->
<template>
  <div class="stables-container">
    
    <!-- Introducción -->
    <div class="intro-card glass-card">
      <div class="intro-content">
        <h2>🏡 Gestión de Establos y Corrales</h2>
        <p class="intro-text">
          Registra tus establos, gallineros, chiqueros y apriscos para llevar un control detallado de su capacidad y ocupación en la granja. Una vez creados, podrás vincularlos en las <strong>Calculadoras de Animales</strong> para sincronizar automáticamente los consumos de comida, paja y producción de productos según la cantidad real de animales.
        </p>
      </div>
    </div>

    <!-- Resumen Consolidado Anual por Tipo de Animal -->
    <div class="glass-card summary-card" v-if="stablesList.length > 0">
      <h3 class="card-title mb-12">📊 Resumen Consolidado Anual de Consumo y Producción</h3>
      <p class="intro-text mb-16">
        Consumo de alimento, paja y producción de productos consolidados a través de todos tus establos según los parámetros individuales asignados en las calculadoras de animales:
      </p>
      
      <div class="table-container">
        <table class="table-premium">
          <thead>
            <tr>
              <th>Animal</th>
              <th class="text-center">Total Animales</th>
              <th>Consumo Alimento Anual</th>
              <th>Consumo Paja Anual</th>
              <th>Producción Fertilizante Anual</th>
              <th>Producción Principal / Ventas</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(data, animalKey) in consolidatedTotals" :key="animalKey" :class="{ 'row-disabled': data.count === 0 }">
              <td>
                <span class="animal-type-label">
                  {{ getAnimalTypeEmoji(animalKey) }} {{ getAnimalTypeSpanish(animalKey) }}s
                </span>
              </td>
              <td class="font-bold text-center">{{ data.count }}</td>
              <td>{{ data.food > 0 ? data.food.toLocaleString('es-ES', { maximumFractionDigits: 0 }) + ' L' : '—' }}</td>
              <td>{{ data.straw > 0 ? data.straw.toLocaleString('es-ES', { maximumFractionDigits: 0 }) + ' L' : '—' }}</td>
              <td>
                <div class="fertilizer-details">
                  <span v-if="data.slurry > 0">💧 Purín: {{ data.slurry.toLocaleString('es-ES', { maximumFractionDigits: 0 }) }} L</span>
                  <span v-if="data.manure > 0">💩 Estiércol: {{ data.manure.toLocaleString('es-ES', { maximumFractionDigits: 0 }) }} L</span>
                  <span v-if="data.slurry === 0 && data.manure === 0">—</span>
                </div>
              </td>
              <td>
                <span v-if="data.mainProduct > 0">
                  <strong class="text-accent" v-if="animalKey === 'Pig' || animalKey === 'Horse'">${{ data.mainProduct.toLocaleString('es-ES', { maximumFractionDigits: 0 }) }}/año</strong>
                  <strong class="text-accent-blue" v-else>{{ data.mainProduct.toLocaleString('es-ES', { maximumFractionDigits: 0 }) }} L ({{ data.productName }})</strong>
                </span>
                <span v-else>—</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <div class="grid-layout">
      <!-- FORMULARIO DE ALTA -->
      <div class="glass-card form-card">
        <h3 class="card-title">➕ Registrar Nuevo Establo</h3>
        <form @submit.prevent="addStable" class="stable-form">
          <div class="form-group mb-16">
            <label for="stable-name">Nombre del Establo</label>
            <input 
              id="stable-name" 
              type="text" 
              v-model="newStable.name" 
              required 
              class="input-premium" 
              placeholder="Ej: Establo Vacas Principal"
            />
          </div>

          <div class="form-group mb-16">
            <label for="stable-type">Tipo de Animal</label>
            <select id="stable-type" v-model="newStable.type" class="select-premium" required>
              <option value="Cow">🐮 Vacas (Cows)</option>
              <option value="Buffalo">🦬 Búfalos de Agua (Buffaloes)</option>
              <option value="Chicken">🐔 Gallinas (Chickens)</option>
              <option value="Sheep">🐑 Ovejas (Sheep)</option>
              <option value="Goat">🐐 Cabras (Goats)</option>
              <option value="Pig">🐷 Cerdos (Pigs)</option>
              <option value="Horse">🐴 Caballos (Horses)</option>
            </select>
          </div>

          <div class="grid-inputs mb-16">
            <div class="form-group">
              <label for="stable-max">Capacidad Máx.</label>
              <input 
                id="stable-max" 
                type="number" 
                min="1" 
                v-model.number="newStable.maxCapacity" 
                required 
                class="input-premium" 
                placeholder="Ej: 80"
              />
            </div>
            
            <div class="form-group">
              <label for="stable-current">Cantidad Actual</label>
              <input 
                id="stable-current" 
                type="number" 
                min="0" 
                :max="newStable.maxCapacity || 99999"
                v-model.number="newStable.currentCount" 
                required 
                class="input-premium" 
                placeholder="Ej: 45"
              />
            </div>
          </div>

          <button type="submit" class="btn-premium btn-add">
            <span>🏡</span> Registrar Establo
          </button>
        </form>
      </div>

      <!-- TABLA DE ESTABLOS REGISTRADOS -->
      <div class="glass-card table-card">
        <div class="card-header-flex">
          <h3 class="card-title mb-0">📋 Establos y Corrales Activos ({{ stablesList.length }})</h3>
          <button v-if="stablesList.length > 0" class="btn-clear" @click="resetToDefaultStables">
            Reestablecer Estructuras Base
          </button>
        </div>

        <div v-if="stablesList.length === 0" class="no-stables">
          <p>⚠️ No tienes ningún establo o corral registrado.</p>
          <p class="sub-text">Usa el formulario de la izquierda para dar de alta el primero y vincularlo a tus animales.</p>
        </div>

        <div v-else class="table-container">
          <table class="table-premium">
            <thead>
              <tr>
                <th>Nombre del Establo</th>
                <th class="type-col">Tipo de Animal</th>
                <th class="occup-col">Ocupación / Capacidad</th>
                <th class="progress-col">Uso corral</th>
                <th class="actions-col">Acciones</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(stable, index) in stablesList" :key="index">
                <td>
                  <input 
                    type="text" 
                    v-model="stable.name" 
                    @change="saveStablesList"
                    class="input-premium inline-name-input"
                  />
                </td>
                <td>
                  <span class="animal-type-label">
                    {{ getAnimalTypeEmoji(stable.type) }} {{ getAnimalTypeSpanish(stable.type) }}
                  </span>
                </td>
                <td>
                  <div class="inline-occup-inputs">
                    <input 
                      type="number" 
                      min="0" 
                      :max="stable.maxCapacity"
                      v-model.number="stable.currentCount" 
                      @input="saveStablesList"
                      class="input-premium inline-occup-input"
                    />
                    <span class="separator">/</span>
                    <input 
                      type="number" 
                      min="1" 
                      v-model.number="stable.maxCapacity" 
                      @input="saveStablesList"
                      class="input-premium inline-occup-input"
                    />
                  </div>
                </td>
                <td>
                  <div class="progress-bar-wrapper">
                    <span class="percentage-val">{{ getOccupationPercent(stable).toFixed(1) }}%</span>
                    <div class="progress-bar-bg">
                      <div 
                        class="progress-bar-fill" 
                        :class="{ 'full': getOccupationPercent(stable) >= 100, 'warning': getOccupationPercent(stable) >= 85 && getOccupationPercent(stable) < 100 }"
                        :style="{ width: Math.min(100, getOccupationPercent(stable)) + '%' }"
                      ></div>
                    </div>
                  </div>
                </td>
                <td>
                  <div class="actions-row">
                    <NuxtLink 
                      :to="getAnimalCalculatorLink(stable.type)" 
                      class="btn-premium btn-secondary btn-sm"
                      title="Ir a calculadora de este animal"
                    >
                      Ir 🧮
                    </NuxtLink>
                    <button 
                      class="btn-premium btn-danger btn-sm"
                      @click="deleteStable(index)"
                      title="Eliminar corral"
                    >
                      ✕
                    </button>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useDB } from '~/composables/useDB'
import { useGlobalSettings } from '~/composables/useGlobalSettings'
import { calculateCows, calculateChickens, calculateSheep, calculateGoats, calculatePigs, calculateHorses, calculateBuffaloes } from '~/utils/animalCalculations'

definePageMeta({
  layout: 'default'
})

const db = useDB()
const { difficulty: globalDifficulty } = useGlobalSettings()

// Lista de establos
const stablesList = ref([])

// Métodos de cálculo consolidados
const getStableCalculations = (stable) => {
  const count = stable.currentCount || 0
  const type = stable.type

  if (type === 'Cow') {
    const inputs = {
      numCows: count,
      yieldBonus: 0.425,
      grassHarvests: 2,
      provideStraw: true,
      breed: 'Holstein',
      feedType: 'TMR',
      difficulty: 'Easy',
      sellPriceType: 'MaxSeasonal',
      sellCount: 4,
      silageCrop: 'Corn',
      ...stable.settings,
      difficulty: globalDifficulty.value
    }
    inputs.numCows = count
    const res = calculateCows(inputs)
    return {
      food: Math.abs(res.production.food.yearly),
      straw: Math.abs(res.production.straw.yearly),
      mainProduct: { name: 'Leche', amount: res.production.milk.yearly },
      slurry: res.production.slurry.yearly,
      manure: res.production.manure.yearly
    }
  } else if (type === 'Chicken') {
    const inputs = {
      numChx: count,
      yieldBonus: 0.425,
      difficulty: 'Easy',
      sellPriceType: 'MaxSeasonal',
      feedBoughtPercent: 0,
      feedType: 'Wheat',
      fieldworkCrop: 'Wheat',
      ...stable.settings,
      difficulty: globalDifficulty.value
    }
    inputs.numChx = count
    const res = calculateChickens(inputs)
    return {
      food: res.feed.total,
      straw: 0,
      mainProduct: { name: 'Huevos', amount: res.eggs.yearly },
      slurry: 0,
      manure: 0
    }
  } else if (type === 'Sheep') {
    const inputs = {
      numSheep: count,
      yieldBonus: 0.425,
      grassHarvests: 2,
      difficulty: 'Easy',
      sellPriceType: 'MaxSeasonal',
      ...stable.settings,
      difficulty: globalDifficulty.value
    }
    inputs.numSheep = count
    const res = calculateSheep(inputs)
    return {
      food: res.feed.yearly,
      straw: 0,
      mainProduct: { name: 'Lana', amount: res.wool.yearly },
      slurry: 0,
      manure: 0
    }
  } else if (type === 'Goat') {
    const inputs = {
      numGoats: count,
      yieldBonus: 0.425,
      grassHarvests: 2,
      difficulty: 'Easy',
      sellPriceType: 'MaxSeasonal',
      ...stable.settings,
      difficulty: globalDifficulty.value
    }
    inputs.numGoats = count
    const res = calculateGoats(inputs)
    return {
      food: res.feed.yearly,
      straw: 0,
      mainProduct: { name: 'Leche de Cabra', amount: res.goatMilk.yearly },
      slurry: 0,
      manure: 0
    }
  } else if (type === 'Pig') {
    const inputs = {
      numPigs: count,
      yieldBonus: 0.425,
      difficulty: 'Easy',
      sellPriceType: 'MaxSeasonal',
      sellCount: Math.ceil(count * 0.5),
      provideStraw: true,
      baseCrop: 'Corn',
      grainCrop: 'Wheat',
      proteinCrop: 'Soy',
      rootCrop: 'Potato',
      ...stable.settings,
      difficulty: globalDifficulty.value
    }
    inputs.numPigs = count
    const res = calculatePigs(inputs)
    return {
      food: res.production.totalFeed,
      straw: Math.abs(res.production.straw),
      mainProduct: { name: 'Venta Cerdos', amount: res.sales.porkSales },
      slurry: res.production.slurry,
      manure: res.production.manure
    }
  } else if (type === 'Horse') {
    const inputs = {
      numHorses: count,
      yieldBonus: 0.425,
      grassHarvests: 2,
      sellCount: Math.ceil(count * 0.125),
      provideStraw: true,
      baseCrop: 'Oat',
      rootCrop: 'Potato',
      ...stable.settings
    }
    inputs.numHorses = count
    const res = calculateHorses(inputs)
    return {
      food: res.production.totalFeed,
      straw: Math.abs(res.production.straw),
      mainProduct: { name: 'Venta Caballos', amount: res.sales.horseSales },
      slurry: 0,
      manure: res.production.manure
    }
  } else if (type === 'Buffalo') {
    const inputs = {
      numBuffaloes: count,
      yieldBonus: 0.425,
      grassHarvests: 2,
      provideStraw: true,
      feedType: 'TMR',
      difficulty: 'Easy',
      sellPriceType: 'MaxSeasonal',
      sellCount: Math.ceil(count * 0.1),
      percentProductive: 100,
      silageCrop: 'Corn',
      ...stable.settings,
      difficulty: globalDifficulty.value
    }
    inputs.numBuffaloes = count
    const res = calculateBuffaloes(inputs)
    return {
      food: Math.abs(res.production.food.yearly),
      straw: Math.abs(res.production.straw.yearly),
      mainProduct: { name: 'Leche de Búfala', amount: res.production.milk.yearly },
      slurry: res.production.slurry.yearly,
      manure: res.production.manure.yearly
    }
  }

  return { food: 0, straw: 0, mainProduct: { name: 'N/A', amount: 0 }, slurry: 0, manure: 0 }
}

const consolidatedTotals = computed(() => {
  const totals = {
    Cow: { count: 0, food: 0, straw: 0, slurry: 0, manure: 0, mainProduct: 0, productName: 'Leche' },
    Buffalo: { count: 0, food: 0, straw: 0, slurry: 0, manure: 0, mainProduct: 0, productName: 'Leche de Búfala' },
    Chicken: { count: 0, food: 0, straw: 0, slurry: 0, manure: 0, mainProduct: 0, productName: 'Huevos' },
    Sheep: { count: 0, food: 0, straw: 0, slurry: 0, manure: 0, mainProduct: 0, productName: 'Lana' },
    Goat: { count: 0, food: 0, straw: 0, slurry: 0, manure: 0, mainProduct: 0, productName: 'Leche de Cabra' },
    Pig: { count: 0, food: 0, straw: 0, slurry: 0, manure: 0, mainProduct: 0, productName: 'Venta Cerdos' },
    Horse: { count: 0, food: 0, straw: 0, slurry: 0, manure: 0, mainProduct: 0, productName: 'Venta Caballos' }
  }

  stablesList.value.forEach(stable => {
    const t = totals[stable.type]
    if (t) {
      t.count += stable.currentCount || 0
      const calcs = getStableCalculations(stable)
      t.food += calcs.food
      t.straw += calcs.straw
      t.slurry += calcs.slurry
      t.manure += calcs.manure
      t.mainProduct += calcs.mainProduct.amount
    }
  })

  return totals
})

// Formulario reactivo para añadir establos
const newStable = ref({
  name: '',
  type: 'Cow',
  maxCapacity: null,
  currentCount: null
})

// Establos por defecto en caso de estar vacía
const defaultStables = [
  { name: 'Establo Vacas Principal', type: 'Cow', maxCapacity: 80, currentCount: 45 },
  { name: 'Gallinero Granero', type: 'Chicken', maxCapacity: 360, currentCount: 150 },
  { name: 'Pradera Ovejas Norte', type: 'Sheep', maxCapacity: 60, currentCount: 24 }
]

// Cargar establos al montar
onMounted(async () => {
  const savedList = await db.getSetting('registered_stables', null)
  if (savedList && Array.isArray(savedList)) {
    stablesList.value = savedList
  } else {
    // Si no hay nada guardado en IndexedDB, inicializamos con los valores por defecto
    stablesList.value = JSON.parse(JSON.stringify(defaultStables))
    await saveStablesList()
  }
})

// Guardar lista en IndexedDB
const saveStablesList = async () => {
  await db.saveSetting('registered_stables', JSON.parse(JSON.stringify(stablesList.value)))
}

// Agregar establo
const addStable = async () => {
  if (!newStable.value.name || !newStable.value.type || newStable.value.maxCapacity === null || newStable.value.currentCount === null) return

  // Validar que actual no exceda el máximo
  if (newStable.value.currentCount > newStable.value.maxCapacity) {
    newStable.value.currentCount = newStable.value.maxCapacity
  }

  stablesList.value.push({
    name: newStable.value.name,
    type: newStable.value.type,
    maxCapacity: newStable.value.maxCapacity,
    currentCount: newStable.value.currentCount
  })

  // Reset formulario
  newStable.value.name = ''
  newStable.value.type = 'Cow'
  newStable.value.maxCapacity = null
  newStable.value.currentCount = null

  await saveStablesList()
}

// Eliminar establo
const deleteStable = async (index) => {
  if (confirm('¿Estás seguro de que deseas eliminar este establo de la lista?')) {
    stablesList.value.splice(index, 1)
    await saveStablesList()
  }
}

// Reestablecer establos por defecto
const resetToDefaultStables = async () => {
  if (confirm('¿Deseas restablecer tus establos a los corrales iniciales por defecto? Esto borrará tus establos actuales.')) {
    stablesList.value = JSON.parse(JSON.stringify(defaultStables))
    await saveStablesList()
  }
}

// --- Métodos de Ayuda / Formateadores ---

// Porcentaje de ocupación
const getOccupationPercent = (stable) => {
  if (!stable.maxCapacity) return 0
  return (stable.currentCount / stable.maxCapacity) * 100
}

// Mapeo de tipo de animal a español
const getAnimalTypeSpanish = (type) => {
  const map = {
    Cow: 'Vaca',
    Buffalo: 'Búfalo',
    Chicken: 'Gallina',
    Sheep: 'Oveja',
    Goat: 'Cabra',
    Pig: 'Cerdo',
    Horse: 'Caballo'
  }
  return map[type] || type
}

// Mapeo de tipo de animal a emoji
const getAnimalTypeEmoji = (type) => {
  const map = {
    Cow: '🐮',
    Buffalo: '🦬',
    Chicken: '🐔',
    Sheep: '🐑',
    Goat: '🐐',
    Pig: '🐷',
    Horse: '🐴'
  }
  return map[type] || '🐾'
}

// Enlace de la calculadora correspondiente
const getAnimalCalculatorLink = (type) => {
  const map = {
    Cow: '/animals/cows',
    Buffalo: '/animals/buffaloes',
    Chicken: '/animals/chickens',
    Sheep: '/animals/sheep',
    Goat: '/animals/goats',
    Pig: '/animals/pigs',
    Horse: '/animals/horses'
  }
  return map[type] || '/'
}
</script>

<style scoped>
.stables-container {
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

@media (max-width: 950px) {
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

.form-card {
  border-left: 4px solid var(--primary);
}

.stable-form {
  display: flex;
  flex-direction: column;
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

.grid-inputs {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}

.mb-16 {
  margin-bottom: 16px;
}

.btn-add {
  width: 100%;
}

.card-header-flex {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  border-bottom: 1px solid var(--border-color);
  padding-bottom: 12px;
}

.btn-clear {
  background: transparent;
  border: none;
  color: var(--primary);
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 4px;
  transition: var(--transition-smooth);
}

.btn-clear:hover {
  background: rgba(46, 213, 115, 0.08);
}

.no-stables {
  text-align: center;
  padding: 40px;
  color: var(--text-secondary);
}

.no-stables .sub-text {
  font-size: 12px;
  color: var(--text-muted);
  margin-top: 8px;
}

/* Tabla Estilos */
.table-premium th {
  padding: 12px;
}

.table-premium td {
  padding: 8px 12px;
  vertical-align: middle;
}

.inline-name-input {
  background: rgba(0, 0, 0, 0.15);
  border-color: transparent;
  font-weight: 600;
  font-size: 14px;
}

.inline-name-input:focus {
  border-color: var(--primary);
  background: rgba(0, 0, 0, 0.4);
}

.animal-type-label {
  font-weight: 600;
  font-size: 13px;
  color: var(--text-primary);
}

.inline-occup-inputs {
  display: flex;
  align-items: center;
  gap: 4px;
}

.inline-occup-input {
  padding: 6px 4px;
  font-size: 13px;
  text-align: center;
  background: rgba(0, 0, 0, 0.15);
  border-color: transparent;
  width: 55px;
}

.inline-occup-input:focus {
  border-color: var(--primary);
  background: rgba(0, 0, 0, 0.4);
}

.separator {
  color: var(--text-muted);
  font-weight: 700;
  font-size: 14px;
}

/* Ocupación Barra */
.progress-bar-wrapper {
  display: flex;
  flex-direction: column;
  gap: 4px;
  width: 100%;
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
  transition: width 0.3s ease;
}

.progress-bar-fill.warning {
  background: var(--accent);
  box-shadow: 0 0 5px var(--accent-glow);
}

.progress-bar-fill.full {
  background: var(--danger);
  box-shadow: 0 0 5px var(--danger-glow);
}

.actions-row {
  display: flex;
  gap: 8px;
}

.btn-sm {
  padding: 6px 12px;
  font-size: 12px;
}

/* Col Widths */
.type-col {
  width: 130px;
}

.occup-col {
  width: 150px;
}

.progress-col {
  width: 160px;
}

.summary-card {
  border-left: 4px solid var(--accent);
  background: linear-gradient(135deg, rgba(255, 165, 2, 0.08) 0%, rgba(18, 30, 25, 0.65) 100%);
}

.fertilizer-details {
  display: flex;
  flex-direction: column;
  gap: 2px;
  font-size: 12px;
}

.text-accent-blue {
  color: #3498db;
  font-weight: 700;
}

.text-center {
  text-align: center;
}

.font-bold {
  font-weight: 700;
}

.mb-12 {
  margin-bottom: 12px;
}

.mb-16 {
  margin-bottom: 16px;
}

.row-disabled {
  opacity: 0.35;
}
</style>
