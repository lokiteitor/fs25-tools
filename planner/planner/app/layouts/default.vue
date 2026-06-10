<!-- app/layouts/default.vue -->
<template>
  <div class="layout-wrapper">
    <!-- Sidebar Navigation -->
    <aside class="sidebar glass-card">
      <div class="sidebar-brand">
        <span class="brand-emoji">🚜</span>
        <span class="brand-text">FS25 <span class="accent-text">Planner</span></span>
      </div>
      
      <nav class="sidebar-nav">
        <NuxtLink to="/" class="nav-item" exact-active-class="active">
          <span class="nav-icon">📊</span>
          <span>Dashboard</span>
        </NuxtLink>
        
        <NuxtLink to="/fields" class="nav-item" active-class="active">
          <span class="nav-icon">🌾</span>
          <span>Gestión de Campos</span>
        </NuxtLink>
        
        <NuxtLink to="/machinery" class="nav-item" active-class="active">
          <span class="nav-icon">🚜</span>
          <span>Mi Maquinaria</span>
        </NuxtLink>
        
        <NuxtLink to="/speed-calculator" class="nav-item" active-class="active">
          <span class="nav-icon">⏱️</span>
          <span>Tiempo de Trabajo</span>
        </NuxtLink>
        
        <NuxtLink to="/stables" class="nav-item" active-class="active">
          <span class="nav-icon">🏡</span>
          <span>Mis Establos</span>
        </NuxtLink>
        
        <div class="nav-group">
          <div class="nav-group-header">
            <span class="nav-icon">🐄</span>
            <span>Animales</span>
          </div>
          <div class="nav-group-items">
            <NuxtLink to="/animals/cows" class="nav-subitem" active-class="active">
              <span class="nav-icon">🐮</span> Vacas
            </NuxtLink>
            <NuxtLink to="/animals/buffaloes" class="nav-subitem" active-class="active">
              <span class="nav-icon">🦬</span> Búfalos de Agua
            </NuxtLink>
            <NuxtLink to="/animals/chickens" class="nav-subitem" active-class="active">
              <span class="nav-icon">🐔</span> Gallinas
            </NuxtLink>
            <NuxtLink to="/animals/sheep" class="nav-subitem" active-class="active">
              <span class="nav-icon">🐑</span> Ovejas
            </NuxtLink>
            <NuxtLink to="/animals/goats" class="nav-subitem" active-class="active">
              <span class="nav-icon">🐐</span> Cabras
            </NuxtLink>
            <NuxtLink to="/animals/pigs" class="nav-subitem" active-class="active">
              <span class="nav-icon">🐷</span> Cerdos
            </NuxtLink>
            <NuxtLink to="/animals/horses" class="nav-subitem" active-class="active">
              <span class="nav-icon">🐴</span> Caballos
            </NuxtLink>
          </div>
        </div>
      </nav>

      <div class="sidebar-footer">
        <div class="global-settings">
          <label for="global-difficulty" class="settings-label">Dificultad Global</label>
          <select id="global-difficulty" v-model="difficulty" class="select-premium settings-select" @change="saveSettings">
            <option value="Easy">Fácil</option>
            <option value="Normal">Normal</option>
            <option value="Hard">Difícil</option>
          </select>
        </div>
        <div class="footer-info">
          <p>Dirección de Granja</p>
          <span class="version-tag">FS25 Tools v1.1</span>
        </div>
      </div>
    </aside>

    <!-- Main Content Area -->
    <div class="main-wrapper">
      <header class="main-header glass-card">
        <div class="header-title-container">
          <h1 class="header-page-title">{{ pageTitle }}</h1>
          <p class="header-subtitle">{{ pageSubtitle }}</p>
        </div>
      </header>

      <main class="page-content">
        <slot />
      </main>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useGlobalSettings } from '~/composables/useGlobalSettings'

const route = useRoute()
const { difficulty, loadSettings, saveSettings } = useGlobalSettings()

onMounted(async () => {
  await loadSettings()
})

const pageTitle = computed(() => {
  if (route.path === '/fields') return 'Gestión de Campos & Cultivos'
  if (route.path === '/machinery') return 'Gestión de Maquinaria'
  if (route.path === '/speed-calculator') return 'Calculadora de Tiempo de Trabajo'
  if (route.path === '/stables') return 'Gestión de Establos'
  if (route.path.startsWith('/animals/cows')) return 'Calculadora de Vacas'
  if (route.path.startsWith('/animals/buffaloes')) return 'Calculadora de Búfalos de Agua'
  if (route.path.startsWith('/animals/chickens')) return 'Calculadora de Gallinas'
  if (route.path.startsWith('/animals/sheep')) return 'Calculadora de Ovejas'
  if (route.path.startsWith('/animals/goats')) return 'Calculadora de Cabras'
  if (route.path.startsWith('/animals/pigs')) return 'Calculadora de Cerdos'
  if (route.path.startsWith('/animals/horses')) return 'Calculadora de Caballos'
  return 'FS25 Farm Planner'
})

const pageSubtitle = computed(() => {
  if (route.path === '/fields') return 'Administra tus hectáreas, costes de compra y retorno económico de tus cosechas'
  if (route.path === '/machinery') return 'Registra y administra tu flota de tractores, cosechadoras e implementos'
  if (route.path === '/speed-calculator') return 'Estima el tiempo de trabajo con múltiples herramientas operando en paralelo'
  if (route.path === '/stables') return 'Administra tus corrales, gallineros y apriscos, controlando su capacidad y ocupación'
  if (route.path.startsWith('/animals/cows')) return 'Análisis de leche, estiércol, TMR y hectáreas de pasto/chaff'
  if (route.path.startsWith('/animals/buffaloes')) return 'Análisis de leche de búfala, estiércol, TMR y necesidades de pasto'
  if (route.path.startsWith('/animals/chickens')) return 'Producción de huevos, costos de alimento y hectáreas de grano'
  if (route.path.startsWith('/animals/sheep')) return 'Calculadora de producción de lana'
  if (route.path.startsWith('/animals/goats')) return 'Calculadora de producción de leche de cabra'
  if (route.path.startsWith('/animals/pigs')) return 'Análisis de alimentación de cerdos por partes y hectáreas estimadas'
  if (route.path.startsWith('/animals/horses')) return 'Cálculo de heno, avena y rentabilidad de equinos'
  return 'Bienvenido a tu panel de decisiones agrícolas'
})
</script>

<style scoped>
.layout-wrapper {
  display: flex;
  min-height: 100vh;
  gap: 24px;
  padding: 24px;
}

.sidebar {
  width: 280px;
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
  border-radius: 20px;
  height: calc(100vh - 48px);
  position: sticky;
  top: 24px;
  background: rgba(18, 30, 25, 0.85);
}

.sidebar-brand {
  display: flex;
  align-items: center;
  gap: 12px;
  padding-bottom: 24px;
  border-bottom: 1px solid var(--border-color);
  margin-bottom: 24px;
}

.brand-emoji {
  font-size: 28px;
}

.brand-text {
  font-size: 20px;
  font-weight: 800;
  letter-spacing: 0.5px;
}

.accent-text {
  color: var(--primary);
}

.sidebar-nav {
  display: flex;
  flex-direction: column;
  gap: 12px;
  flex-grow: 1;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  color: var(--text-secondary);
  text-decoration: none;
  font-weight: 600;
  border-radius: 10px;
  transition: var(--transition-smooth);
  border: 1px solid transparent;
}

.nav-item:hover {
  background: rgba(46, 213, 115, 0.08);
  color: var(--primary);
  border-color: rgba(46, 213, 115, 0.1);
}

.nav-item.active {
  background: rgba(46, 213, 115, 0.15);
  color: var(--primary);
  border-color: var(--border-color);
  box-shadow: 0 0 15px rgba(46, 213, 115, 0.1);
}

.nav-group {
  margin-top: 12px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.nav-group-header {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 16px;
  color: var(--text-muted);
  font-size: 12px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 1px;
}

.nav-group-items {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding-left: 12px;
}

.nav-subitem {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 16px;
  color: var(--text-secondary);
  text-decoration: none;
  font-size: 14px;
  font-weight: 500;
  border-radius: 8px;
  transition: var(--transition-smooth);
  border: 1px solid transparent;
}

.nav-subitem:hover {
  background: rgba(46, 213, 115, 0.08);
  color: var(--primary);
  border-color: rgba(46, 213, 115, 0.1);
}

.nav-subitem.active {
  background: rgba(46, 213, 115, 0.15);
  color: var(--primary);
  border-color: var(--border-color);
}

.sidebar-footer {
  margin-top: auto;
  padding-top: 24px;
  border-top: 1px solid var(--border-color);
  text-align: center;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.global-settings {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 0 16px;
}

.settings-label {
  font-size: 12px;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 1px;
  font-weight: 700;
  text-align: left;
}

.settings-select {
  width: 100%;
  padding: 8px 12px;
  background: rgba(30, 35, 40, 0.8);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  color: #fff;
  font-size: 14px;
  outline: none;
}

.settings-select:focus {
  border-color: var(--primary);
}

.footer-info p {
  font-size: 13px;
  color: var(--text-secondary);
  font-weight: 500;
}

.version-tag {
  font-size: 11px;
  color: var(--text-muted);
  display: inline-block;
  margin-top: 4px;
}

.main-wrapper {
  display: flex;
  flex-direction: column;
  gap: 24px;
  flex-grow: 1;
  min-width: 0; /* Evita que las tablas ensanchen el layout */
}

.main-header {
  padding: 20px 32px;
  border-radius: 20px;
}

.header-page-title {
  font-size: 24px;
  font-weight: 800;
  color: var(--text-primary);
  margin-bottom: 4px;
}

.header-subtitle {
  font-size: 14px;
  color: var(--text-secondary);
}

.page-content {
  flex-grow: 1;
}

@media (max-width: 1024px) {
  .layout-wrapper {
    flex-direction: column;
    padding: 16px;
  }
  
  .sidebar {
    width: 100%;
    height: auto;
    position: static;
  }
  
  .nav-group-items {
    flex-direction: row;
    flex-wrap: wrap;
    padding-left: 0;
  }
}
</style>
