<!-- app/pages/machinery.vue -->
<template>
  <div class="machinery-container">
    
    <!-- Introducción -->
    <div class="intro-card glass-card">
      <div class="intro-content">
        <h2>🚜 Flota y Equipamiento de Trabajo</h2>
        <p class="intro-text">
          Registra y administra las herramientas de tu granja. Define sus anchos y velocidades de trabajo para calcular automáticamente su rendimiento por hora. Estas herramientas estarán disponibles en la <strong>Calculadora de Tiempo de Trabajo</strong> para planificar tareas en paralelo.
        </p>
      </div>
    </div>

    <div class="grid-layout">
      <!-- FORMULARIO DE ALTA -->
      <div class="glass-card form-card">
        <h3 class="card-title">➕ Registrar Nuevo Equipo</h3>
        <form @submit.prevent="addMachinery" class="machinery-form">
          <div class="form-group mb-16">
            <label for="eq-name">Nombre del Equipo / Tractor</label>
            <input 
              id="eq-name" 
              type="text" 
              v-model="newEq.name" 
              required 
              class="input-premium" 
              placeholder="Ej: John Deere 8R + Sembradora 9m"
            />
          </div>

          <div class="grid-inputs mb-16">
            <div class="form-group">
              <label for="eq-width">Ancho de Trabajo (m)</label>
              <input 
                id="eq-width" 
                type="number" 
                step="0.1" 
                min="0.1" 
                v-model.number="newEq.width" 
                required 
                class="input-premium" 
                placeholder="Ej: 9.0"
              />
            </div>
            
            <div class="form-group">
              <label for="eq-speed">Velocidad de Trabajo (km/h)</label>
              <input 
                id="eq-speed" 
                type="number" 
                step="1" 
                min="1" 
                v-model.number="newEq.speed" 
                required 
                class="input-premium" 
                placeholder="Ej: 15"
              />
            </div>
          </div>

          <button type="submit" class="btn-premium btn-add">
            <span>➕</span> Registrar Maquinaria
          </button>
        </form>
      </div>

      <!-- TABLA DE FLOTA REGISTRADA -->
      <div class="glass-card table-card">
        <div class="card-header-flex">
          <h3 class="card-title mb-0">📋 Flota Registrada ({{ machineryList.length }} equipos)</h3>
          <button v-if="machineryList.length > 0" class="btn-clear" @click="resetToDefaultFleet">
            Reestablecer Valores Base
          </button>
        </div>

        <div v-if="machineryList.length === 0" class="no-machinery">
          <p>⚠️ No tienes ningún equipo registrado.</p>
          <p class="sub-text">Completa el formulario de la izquierda para dar de alta tu primer tractor o implemento.</p>
        </div>

        <div v-else class="table-container">
          <table class="table-premium">
            <thead>
              <tr>
                <th>Nombre del Equipo</th>
                <th class="width-col">Ancho (m)</th>
                <th class="speed-col">Velocidad (km/h)</th>
                <th>Capacidad Teórica</th>
                <th class="actions-col">Acción</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(item, index) in machineryList" :key="index">
                <td>
                  <input 
                    type="text" 
                    v-model="item.name" 
                    @change="saveMachineryList"
                    class="input-premium inline-name-input"
                  />
                </td>
                <td>
                  <div class="inline-input-wrapper">
                    <input 
                      type="number" 
                      step="0.1" 
                      min="0.1" 
                      v-model.number="item.width" 
                      @input="saveMachineryList"
                      class="input-premium inline-table-input"
                    />
                    <span class="unit">m</span>
                  </div>
                </td>
                <td>
                  <div class="inline-input-wrapper">
                    <input 
                      type="number" 
                      step="1" 
                      min="1" 
                      v-model.number="item.speed" 
                      @input="saveMachineryList"
                      class="input-premium inline-table-input"
                    />
                    <span class="unit">km/h</span>
                  </div>
                </td>
                <td>
                  <span class="capacity-value text-accent">
                    {{ getCapacity(item).toFixed(2) }} ha/h
                  </span>
                </td>
                <td>
                  <button 
                    class="btn-premium btn-danger btn-sm"
                    @click="deleteMachinery(index)"
                    title="Eliminar de la flota"
                  >
                    Eliminar
                  </button>
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
import { ref, onMounted } from 'vue'
import { useDB } from '~/composables/useDB'

definePageMeta({
  layout: 'default'
})

const db = useDB()

// Lista de maquinaria
const machineryList = ref([])

// Formulario reactivo para alta
const newEq = ref({
  name: '',
  width: null,
  speed: null
})

// Flota por defecto en caso de estar vacía
const defaultFleet = [
  { name: 'John Deere 8R (Sembradora Horsch 9m)', width: 9.0, speed: 15 },
  { name: 'Case IH Magnum (Cultivador Kuhn 12m)', width: 12.0, speed: 12 },
  { name: 'Fendt 939 Vario (Segadora Triple 6m)', width: 6.0, speed: 22 }
]

// Cargar flota al montar
onMounted(async () => {
  const savedList = await db.getSetting('registered_machinery', null)
  if (savedList && Array.isArray(savedList)) {
    machineryList.value = savedList
  } else {
    // Si no hay nada en IndexedDB, inicializamos con los valores por defecto
    machineryList.value = JSON.parse(JSON.stringify(defaultFleet))
    await saveMachineryList()
  }
})

// Guardar lista en IndexedDB
const saveMachineryList = async () => {
  await db.saveSetting('registered_machinery', JSON.parse(JSON.stringify(machineryList.value)))
}

// Calcular capacidad teórica individual (ha/h) = (ancho * velocidad) / 10
const getCapacity = (item) => {
  if (!item.width || !item.speed) return 0
  return (item.width * item.speed) / 10
}

// Agregar equipo
const addMachinery = async () => {
  if (!newEq.value.name || !newEq.value.width || !newEq.value.speed) return

  machineryList.value.push({
    name: newEq.value.name,
    width: newEq.value.width,
    speed: newEq.value.speed
  })

  // Reset formulario
  newEq.value.name = ''
  newEq.value.width = null
  newEq.value.speed = null

  await saveMachineryList()
}

// Eliminar equipo
const deleteMachinery = async (index) => {
  if (confirm('¿Estás seguro de que deseas eliminar este equipo de tu flota?')) {
    machineryList.value.splice(index, 1)
    await saveMachineryList()
  }
}

// Reestablecer flota por defecto
const resetToDefaultFleet = async () => {
  if (confirm('¿Deseas restablecer tu flota a los equipos por defecto? Esto borrará tus equipos actuales.')) {
    machineryList.value = JSON.parse(JSON.stringify(defaultFleet))
    await saveMachineryList()
  }
}
</script>

<style scoped>
.machinery-container {
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

.machinery-form {
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

.no-machinery {
  text-align: center;
  padding: 40px;
  color: var(--text-secondary);
}

.no-machinery .sub-text {
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

.inline-input-wrapper {
  position: relative;
  display: flex;
  align-items: center;
}

.inline-table-input {
  padding: 6px 30px 6px 8px;
  font-size: 13px;
  text-align: right;
  background: rgba(0, 0, 0, 0.15);
  border-color: transparent;
  width: 90px;
}

.inline-table-input:focus {
  border-color: var(--primary);
  background: rgba(0, 0, 0, 0.4);
}

.inline-input-wrapper .unit {
  position: absolute;
  right: 8px;
  font-size: 11px;
  color: var(--text-muted);
  pointer-events: none;
}

.capacity-value {
  font-weight: 700;
  font-size: 14px;
}

.btn-sm {
  padding: 6px 12px;
  font-size: 12px;
}

/* Col Widths */
.width-col {
  width: 110px;
}

.speed-col {
  width: 120px;
}

.actions-col {
  width: 80px;
}
</style>
