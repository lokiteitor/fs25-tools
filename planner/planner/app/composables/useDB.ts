// app/composables/useDB.ts

const DB_NAME = 'fs25_farm_planner_db'
const DB_VERSION = 1

export interface FieldItem {
  id?: number
  fieldNumber: number
  hectares: number
  selectedCrop?: string // Cultivo seleccionado para este campo
  yieldBonus?: number // Bono de rendimiento específico del campo (decimal, ej: 0.425)
  purchasePrice?: number // Precio por el que se compró el campo
}

export interface AppSettings {
  yieldBonus: number
  difficulty: 'Easy' | 'Normal' | 'Hard'
  sellPrice: 'Baseline' | 'MaxSeasonal'
}

let dbInstance: IDBDatabase | null = null

const getDB = (): Promise<IDBDatabase> => {
  return new Promise((resolve, reject) => {
    if (dbInstance) return resolve(dbInstance)
    if (typeof window === 'undefined') {
      return reject(new Error('IndexedDB is only available in the browser'))
    }

    const request = window.indexedDB.open(DB_NAME, DB_VERSION)

    request.onerror = () => reject(request.error)
    request.onsuccess = () => {
      dbInstance = request.result
      resolve(dbInstance)
    }

    request.onupgradeneeded = (event) => {
      const db = request.result
      // Store de campos
      if (!db.objectStoreNames.contains('fields')) {
        db.createObjectStore('fields', { keyPath: 'id', autoIncrement: true })
      }
      // Store de clave-valor para configuraciones
      if (!db.objectStoreNames.contains('settings')) {
        db.createObjectStore('settings')
      }
    }
  })
}

export const useDB = () => {
  // Comprobación segura de cliente
  const isClient = typeof window !== 'undefined'

  // Métodos de Campos
  const getAllFields = async (): Promise<FieldItem[]> => {
    if (!isClient) return []
    const db = await getDB()
    return new Promise((resolve, reject) => {
      const transaction = db.transaction('fields', 'readonly')
      const store = transaction.objectStore('fields')
      const request = store.getAll()
      request.onsuccess = () => resolve(request.result || [])
      request.onerror = () => reject(request.error)
    })
  }

  const saveFieldItem = async (field: FieldItem): Promise<number> => {
    if (!isClient) return 0
    const db = await getDB()
    return new Promise((resolve, reject) => {
      const transaction = db.transaction('fields', 'readwrite')
      const store = transaction.objectStore('fields')
      
      // Asegurarse de clonar el objeto para IndexedDB
      const dataToSave = { ...field }
      if (dataToSave.id === undefined) {
        delete dataToSave.id
      }
      
      const request = store.put(dataToSave)
      request.onsuccess = () => resolve(request.result as number)
      request.onerror = () => reject(request.error)
    })
  }

  const deleteFieldItem = async (id: number): Promise<void> => {
    if (!isClient) return
    const db = await getDB()
    return new Promise((resolve, reject) => {
      const transaction = db.transaction('fields', 'readwrite')
      const store = transaction.objectStore('fields')
      const request = store.delete(id)
      request.onsuccess = () => resolve()
      request.onerror = () => reject(request.error)
    })
  }

  // Métodos de Configuración
  const getSetting = async <T>(key: string, defaultValue: T): Promise<T> => {
    if (!isClient) return defaultValue
    const db = await getDB()
    return new Promise((resolve, reject) => {
      const transaction = db.transaction('settings', 'readonly')
      const store = transaction.objectStore('settings')
      const request = store.get(key)
      request.onsuccess = () => {
        resolve(request.result !== undefined ? request.result as T : defaultValue)
      }
      request.onerror = () => reject(request.error)
    })
  }

  const saveSetting = async <T>(key: string, value: T): Promise<void> => {
    if (!isClient) return
    const db = await getDB()
    return new Promise((resolve, reject) => {
      const transaction = db.transaction('settings', 'readwrite')
      const store = transaction.objectStore('settings')
      const request = store.put(value, key)
      request.onsuccess = () => resolve()
      request.onerror = () => reject(request.error)
    })
  }

  return {
    getAllFields,
    saveFieldItem,
    deleteFieldItem,
    getSetting,
    saveSetting
  }
}
