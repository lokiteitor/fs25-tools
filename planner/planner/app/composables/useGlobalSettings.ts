import { useState } from '#imports'
import { useDB } from '~/composables/useDB'

export const useGlobalSettings = () => {
  const db = useDB()

  // Use useState to share the reactive state across components
  const difficulty = useState<'Easy' | 'Normal' | 'Hard'>('globalDifficulty', () => 'Normal')
  const yieldBonus = useState<number>('globalYieldBonus', () => 0.425)

  // Initialize from DB
  const loadSettings = async () => {
    const savedSettings = await db.getSetting('app_settings', {
      difficulty: 'Normal',
      yieldBonus: 0.425
    })
    
    difficulty.value = savedSettings.difficulty
    yieldBonus.value = savedSettings.yieldBonus
  }

  // Save to DB
  const saveSettings = async () => {
    await db.saveSetting('app_settings', {
      difficulty: difficulty.value,
      yieldBonus: yieldBonus.value
    })
  }

  return {
    difficulty,
    yieldBonus,
    loadSettings,
    saveSettings
  }
}
