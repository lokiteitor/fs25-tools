<template>
  <div class="dashboard-container">
    <div class="welcome-section">
      <div class="welcome-content">
        <h2>¡Bienvenido, Director de Granja! 🧑‍🌾</h2>
        <p>Aquí tienes el resumen ejecutivo de tu explotación agrícola. Revisa tus campos, estado de los animales y planifica tu próxima cosecha.</p>
      </div>
      <div class="quick-stats">
        <div class="stat-pill">
          <span class="icon">🌍</span>
          <span class="value">{{ kpis.totalHectares.toFixed(2) }} ha</span>
          <span class="label">Propiedad</span>
        </div>
        <div class="stat-pill">
          <span class="icon">🌾</span>
          <span class="value">{{ kpis.totalFields }}</span>
          <span class="label">Campos</span>
        </div>
        <div class="stat-pill">
          <span class="icon">🐄</span>
          <span class="value">{{ kpis.totalAnimals }}</span>
          <span class="label">Animales</span>
        </div>
      </div>
    </div>

    <!-- Quick Actions -->
    <div class="actions-grid">
      <NuxtLink to="/fields" class="action-card field-card">
        <div class="card-bg"></div>
        <div class="content">
          <span class="icon-large">🌾</span>
          <h3>Campos y Cultivos</h3>
          <p>Gestiona hectáreas, precios y proyecciones de rendimiento.</p>
        </div>
      </NuxtLink>

      <NuxtLink to="/stables" class="action-card stable-card">
        <div class="card-bg"></div>
        <div class="content">
          <span class="icon-large">🛖</span>
          <h3>Tus Establos</h3>
          <p>Administra la capacidad y distribución de tus animales.</p>
        </div>
      </NuxtLink>

      <NuxtLink to="/animals/cows" class="action-card animal-card">
        <div class="card-bg"></div>
        <div class="content">
          <span class="icon-large">🐄</span>
          <h3>Calculadora Animal</h3>
          <p>Calcula raciones y área necesaria para alimentar tu ganado.</p>
        </div>
      </NuxtLink>

      <NuxtLink to="/machinery" class="action-card machinery-card">
        <div class="card-bg"></div>
        <div class="content">
          <span class="icon-large">🚜</span>
          <h3>Maquinaria</h3>
          <p>Lleva el control del mantenimiento y costos operativos.</p>
        </div>
      </NuxtLink>
    </div>

    <!-- Analytics Dashboard -->
    <div class="analytics-grid mt-24">
      <div class="analytics-card glass-card">
        <div class="card-header">
          <h3>Proyección de Cosecha</h3>
          <span class="badge">{{ kpis.totalYieldTons.toFixed(1) }} t en total</span>
        </div>
        <div class="chart-container" v-if="cropDistribution.length > 0">
          <div class="bars-container">
            <div 
              v-for="crop in cropDistribution" 
              :key="crop.name" 
              class="crop-bar-row"
            >
              <div class="crop-info">
                <span class="crop-name">{{ crop.name }}</span>
                <span class="crop-value">{{ crop.hectares.toFixed(2) }} ha ({{ ((crop.hectares / kpis.totalHectares) * 100).toFixed(0) }}%)</span>
              </div>
              <div class="progress-bar-bg">
                <div 
                  class="progress-bar-fill" 
                  :style="{ width: ((crop.hectares / maxCropHectares) * 100) + '%' }"
                ></div>
              </div>
            </div>
          </div>
        </div>
        <div v-else class="empty-state">
          <p>No tienes cultivos registrados. ¡Agrega campos para ver proyecciones!</p>
          <NuxtLink to="/fields" class="btn-premium btn-small mt-12">Agregar Campos</NuxtLink>
        </div>
      </div>

      <div class="analytics-card glass-card">
        <div class="card-header">
          <h3>Resumen Económico (Estimado)</h3>
        </div>
        <div class="economy-overview" v-if="kpis.totalYieldTons > 0">
          <div class="economy-row" v-if="difficulty === 'Easy'">
            <span>Ingresos (Temporada Alta) - Fácil</span>
            <span class="money text-success">${{ kpis.totalIncomeEasy.toLocaleString('en-US', {maximumFractionDigits:0}) }}</span>
          </div>
          <div class="economy-row" v-if="difficulty === 'Normal'">
            <span>Ingresos (Temporada Alta) - Normal</span>
            <span class="money text-warning">${{ kpis.totalIncomeNormal.toLocaleString('en-US', {maximumFractionDigits:0}) }}</span>
          </div>
          <div class="economy-row" v-if="difficulty === 'Hard'">
            <span>Ingresos (Temporada Alta) - Difícil</span>
            <span class="money text-danger">${{ kpis.totalIncomeHard.toLocaleString('en-US', {maximumFractionDigits:0}) }}</span>
          </div>
          <p class="disclaimer mt-12 text-sm">*Basado en campos actuales, cultivos configurados y venta en pico de precio. Rendimiento asumido con bonificaciones base.</p>
        </div>
        <div v-else class="empty-state">
          <p>Registra cultivos para ver un estimado de ingresos.</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { useDB } from '~/composables/useDB'
import { calculateFields } from '~/utils/cropCalculations'
import { useGlobalSettings } from '~/composables/useGlobalSettings'

definePageMeta({
  layout: 'default'
})

const db = useDB()
const { difficulty } = useGlobalSettings()

const kpis = reactive({
  totalFields: 0,
  totalHectares: 0,
  totalAnimals: 0,
  totalYieldTons: 0,
  totalIncomeEasy: 0,
  totalIncomeNormal: 0,
  totalIncomeHard: 0
})

const cropDistribution = ref([])

const maxCropHectares = computed(() => {
  if (cropDistribution.value.length === 0) return 1
  return Math.max(...cropDistribution.value.map(c => c.hectares))
})

onMounted(async () => {
  // 1. Cargar Campos
  const fields = await db.getAllFields()
  kpis.totalFields = fields.length
  
  let validFieldsForCalc = []
  let cropMap = {}

  fields.forEach(f => {
    kpis.totalHectares += f.hectares
    
    if (f.selectedCrop) {
      if (!cropMap[f.selectedCrop]) {
        cropMap[f.selectedCrop] = 0
      }
      cropMap[f.selectedCrop] += f.hectares

      validFieldsForCalc.push({
        name: `Campo ${f.fieldNumber}`,
        hectares: f.hectares,
        cropName: f.selectedCrop,
        isSilage: f.selectedCrop.includes('Silage') || false // Simplificación
      })
    }
  })

  // Preparar datos para el gráfico de barras
  cropDistribution.value = Object.keys(cropMap).map(key => ({
    name: key,
    hectares: cropMap[key]
  })).sort((a, b) => b.hectares - a.hectares)

  // Calcular rendimiento y economía
  const appSettings = await db.getSetting('app_settings', { yieldBonus: 0.425 })
  const yieldBonus = appSettings.yieldBonus

  if (validFieldsForCalc.length > 0) {
    try {
      const calcResult = calculateFields(validFieldsForCalc, yieldBonus)
      kpis.totalYieldTons = calcResult.totals.yieldTons
      kpis.totalIncomeEasy = calcResult.totals.income.maxSeasonal.easy
      kpis.totalIncomeNormal = calcResult.totals.income.maxSeasonal.normal
      kpis.totalIncomeHard = calcResult.totals.income.maxSeasonal.hard
    } catch (e) {
      console.warn("Error calculando rendimientos (es posible que algunos cultivos no tengan data):", e)
    }
  }

  // 2. Cargar Establos y Animales
  const stables = await db.getSetting('registered_stables', [])
  let animalCount = 0
  if (stables && Array.isArray(stables)) {
    stables.forEach(s => {
      animalCount += (s.currentCount || 0)
    })
  }
  kpis.totalAnimals = animalCount
})
</script>

<style scoped>
.dashboard-container {
  display: flex;
  flex-direction: column;
  gap: 32px;
  animation: fadeIn 0.5s ease-out;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

/* Welcome Section */
.welcome-section {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 24px;
  padding: 32px;
  background: linear-gradient(135deg, rgba(46, 213, 115, 0.1) 0%, rgba(18, 30, 25, 0.8) 100%);
  border-radius: 24px;
  border: 1px solid rgba(46, 213, 115, 0.2);
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
  position: relative;
  overflow: hidden;
}

.welcome-section::before {
  content: '';
  position: absolute;
  top: -50px;
  right: -50px;
  width: 200px;
  height: 200px;
  background: radial-gradient(circle, rgba(46, 213, 115, 0.15) 0%, transparent 70%);
  border-radius: 50%;
  pointer-events: none;
}

.welcome-content {
  flex: 1;
  min-width: 300px;
}

.welcome-content h2 {
  font-size: 28px;
  font-weight: 800;
  margin-bottom: 12px;
  background: linear-gradient(90deg, #fff, #2ed573);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.welcome-content p {
  color: var(--text-secondary);
  font-size: 16px;
  line-height: 1.6;
  max-width: 500px;
}

.quick-stats {
  display: flex;
  gap: 16px;
  flex-wrap: wrap;
}

.stat-pill {
  display: flex;
  flex-direction: column;
  align-items: center;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.05);
  padding: 16px 24px;
  border-radius: 16px;
  backdrop-filter: blur(10px);
  min-width: 120px;
}

.stat-pill .icon {
  font-size: 24px;
  margin-bottom: 8px;
}

.stat-pill .value {
  font-size: 20px;
  font-weight: 800;
  color: #fff;
}

.stat-pill .label {
  font-size: 12px;
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 1px;
  margin-top: 4px;
}

/* Actions Grid */
.actions-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 20px;
}

.action-card {
  position: relative;
  padding: 24px;
  border-radius: 20px;
  text-decoration: none;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  border: 1px solid rgba(255, 255, 255, 0.05);
  transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
  background: rgba(30, 35, 40, 0.5);
  backdrop-filter: blur(10px);
}

.action-card .card-bg {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  opacity: 0.1;
  transition: opacity 0.3s ease;
  z-index: 0;
}

.field-card .card-bg { background: linear-gradient(135deg, #f1c40f, #e67e22); }
.stable-card .card-bg { background: linear-gradient(135deg, #3498db, #2980b9); }
.animal-card .card-bg { background: linear-gradient(135deg, #2ecc71, #27ae60); }
.machinery-card .card-bg { background: linear-gradient(135deg, #e74c3c, #c0392b); }

.action-card:hover {
  transform: translateY(-5px);
  border-color: rgba(255, 255, 255, 0.2);
  box-shadow: 0 15px 30px rgba(0, 0, 0, 0.3);
}

.action-card:hover .card-bg {
  opacity: 0.2;
}

.action-card .content {
  position: relative;
  z-index: 1;
}

.icon-large {
  font-size: 40px;
  display: block;
  margin-bottom: 16px;
  transition: transform 0.3s ease;
}

.action-card:hover .icon-large {
  transform: scale(1.1) rotate(5deg);
}

.action-card h3 {
  font-size: 18px;
  font-weight: 700;
  color: #fff;
  margin-bottom: 8px;
}

.action-card p {
  font-size: 14px;
  color: var(--text-secondary);
  line-height: 1.5;
}

/* Analytics Grid */
.analytics-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
  gap: 24px;
}

.analytics-card {
  display: flex;
  flex-direction: column;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.card-header h3 {
  font-size: 18px;
  font-weight: 700;
  color: #fff;
}

.badge {
  background: rgba(46, 213, 115, 0.2);
  color: var(--primary);
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 700;
}

/* Bars Chart */
.chart-container {
  display: flex;
  flex-direction: column;
  gap: 16px;
  flex: 1;
}

.crop-bar-row {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.crop-info {
  display: flex;
  justify-content: space-between;
  font-size: 14px;
}

.crop-name {
  color: #fff;
  font-weight: 600;
}

.crop-value {
  color: var(--text-secondary);
}

.progress-bar-bg {
  width: 100%;
  height: 8px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 4px;
  overflow: hidden;
}

.progress-bar-fill {
  height: 100%;
  background: linear-gradient(90deg, #2ed573, #7bed9f);
  border-radius: 4px;
  transition: width 1s cubic-bezier(0.25, 0.8, 0.25, 1);
}

/* Economy Overview */
.economy-overview {
  display: flex;
  flex-direction: column;
  gap: 16px;
  flex: 1;
}

.economy-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: rgba(255, 255, 255, 0.02);
  border-radius: 12px;
  border-left: 3px solid transparent;
}

.economy-row:nth-child(1) { border-color: var(--success); }
.economy-row:nth-child(2) { border-color: var(--warning); }
.economy-row:nth-child(3) { border-color: var(--danger); }

.economy-row span {
  font-size: 14px;
  color: var(--text-secondary);
}

.economy-row .money {
  font-size: 16px;
  font-weight: 700;
}

.text-success { color: var(--success) !important; }
.text-warning { color: var(--warning) !important; }
.text-danger { color: var(--danger) !important; }

.disclaimer {
  color: rgba(255, 255, 255, 0.3);
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  padding: 32px 0;
  color: var(--text-secondary);
  flex: 1;
}

.btn-small {
  padding: 8px 16px;
  font-size: 14px;
}

/* Utilities */
.mt-24 { margin-top: 24px; }
.mt-12 { margin-top: 12px; }

@media (max-width: 768px) {
  .welcome-section {
    flex-direction: column;
    align-items: flex-start;
  }
  .quick-stats {
    width: 100%;
    justify-content: space-between;
  }
  .stat-pill {
    flex: 1;
    min-width: 0;
  }
  .analytics-grid {
    grid-template-columns: 1fr;
  }
}
</style>
