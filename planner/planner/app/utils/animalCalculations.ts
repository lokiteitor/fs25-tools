// app/utils/animalCalculations.ts

import { ANIMAL_CONSTANTS, ANIMAL_RATES, ANIMAL_FIELDWORK_YIELDS, COW_TMR_RATIOS, BUFFALO_TMR_RATIOS, MILK_PRICE_SCALARS } from './animalData'

// Helper para calcular yield bonus scalar
export const getYieldBonusScalar = (bonus: number) => 1 + bonus

// --- VACAS ---
export interface CowInputs {
  numCows: number
  yieldBonus: number
  grassHarvests: number
  provideStraw: boolean
  breed: 'Holstein' | 'Other'
  feedType: 'TMR' | 'Simple' | 'Hay' | 'Grass'
  difficulty: 'Easy' | 'Normal' | 'Hard'
  sellPriceType: 'Baseline' | 'MaxSeasonal'
  sellCount: number
  silageCrop: string // 'Corn' | 'Barley' | 'Wheat' | 'Sorghum' | 'Sunflower' | 'Oat' | 'Canola' | 'Soybean'
}

export const calculateCows = (inputs: CowInputs) => {
  const {
    numCows,
    yieldBonus,
    grassHarvests,
    provideStraw,
    feedType,
    difficulty,
    sellPriceType,
    sellCount,
    silageCrop
  } = inputs

  const bonusScalar = getYieldBonusScalar(yieldBonus)
  const diffScalar = ANIMAL_CONSTANTS.difficultyScalars.Cow[difficulty]

  // Productividad según alimento
  const productivityFactor = feedType === 'TMR' ? 1.0 : feedType === 'Simple' ? 1.0 : feedType === 'Hay' ? 0.8 : 0.4

  // Producción de leche
  const strawBonusFactor = provideStraw ? (1 + ANIMAL_CONSTANTS.strawBonus) : 1
  const monthlyMilkLiters = numCows * ANIMAL_RATES.Cow.milk * strawBonusFactor * productivityFactor
  const yearlyMilkLiters = monthlyMilkLiters * 12

  // Precio leche
  const milkPriceScalar = sellPriceType === 'MaxSeasonal' ? MILK_PRICE_SCALARS.max : MILK_PRICE_SCALARS.average
  const unitMilkPrice = ANIMAL_CONSTANTS.baseMilkPrice * diffScalar * milkPriceScalar
  const monthlyMilkSales = monthlyMilkLiters * unitMilkPrice
  const yearlyMilkSales = yearlyMilkLiters * unitMilkPrice

  // Consumo alimento
  const monthlyFoodLiters = numCows * Math.abs(ANIMAL_RATES.Cow.food)
  const yearlyFoodLiters = monthlyFoodLiters * 12

  // Residuos y camas
  const monthlySlurryLiters = numCows * ANIMAL_RATES.Cow.slurry
  const yearlySlurryLiters = monthlySlurryLiters * 12

  const monthlyManureLiters = provideStraw ? (numCows * ANIMAL_RATES.Cow.manure) : 0
  const yearlyManureLiters = monthlyManureLiters * 12

  const monthlyStrawLiters = provideStraw ? (numCows * Math.abs(ANIMAL_RATES.Cow.straw)) : 0
  const yearlyStrawLiters = monthlyStrawLiters * 12

  // Beef Sales
  const unitBeefPrice = 3500.0
  const yearlyBeefRevenue = unitBeefPrice * sellCount

  // Fieldwork para cama de paja
  // En el excel: Straw Bedding Hectares = straw_bedding_yearly / 5.244 / 10000
  const strawBeddingHectares = provideStraw ? (yearlyStrawLiters / 5.244 / 10000) : 0

  // Fieldwork Simple (Grass, Silage, Hay)
  const grassYield = ANIMAL_FIELDWORK_YIELDS.Grass * bonusScalar
  let simpleGrassHectares = 0
  let simpleSilageHectares = 0

  // Ensilaje Hectáreas para Simple Feed
  const silageYieldMap: Record<string, number> = {
    Corn: ANIMAL_FIELDWORK_YIELDS.Corn * ANIMAL_FIELDWORK_YIELDS.CornChaffMult,
    Barley: ANIMAL_FIELDWORK_YIELDS.Barley * ANIMAL_FIELDWORK_YIELDS.BarleyChaffMult,
    Wheat: ANIMAL_FIELDWORK_YIELDS.Wheat * ANIMAL_FIELDWORK_YIELDS.WheatChaffMult,
    Sorghum: ANIMAL_FIELDWORK_YIELDS.Sorghum * ANIMAL_FIELDWORK_YIELDS.SorghumChaffMult,
    Sunflower: ANIMAL_FIELDWORK_YIELDS.Sunflower * ANIMAL_FIELDWORK_YIELDS.SunflowerChaffMult,
    Oat: ANIMAL_FIELDWORK_YIELDS.Oat * ANIMAL_FIELDWORK_YIELDS.OatChaffMult,
    Canola: ANIMAL_FIELDWORK_YIELDS.Canola * ANIMAL_FIELDWORK_YIELDS.CanolaChaffMult,
    Soybean: ANIMAL_FIELDWORK_YIELDS.Soybean * ANIMAL_FIELDWORK_YIELDS.SoybeanChaffMult
  }

  const selectedSilageBaseYield = silageYieldMap[silageCrop] || (ANIMAL_FIELDWORK_YIELDS.Corn * ANIMAL_FIELDWORK_YIELDS.CornChaffMult)
  const selectedSilageYield = selectedSilageBaseYield * bonusScalar

  if (feedType === 'Simple') {
    simpleGrassHectares = yearlyFoodLiters / (grassHarvests * grassYield * 10000)
    simpleSilageHectares = yearlyFoodLiters / (selectedSilageYield * 10000)
  } else if (feedType === 'Grass' || feedType === 'Hay') {
    simpleGrassHectares = yearlyFoodLiters / (grassHarvests * grassYield * 10000)
    simpleSilageHectares = 0
  }

  // Fieldwork TMR
  const tmrYearlyStraw = feedType === 'TMR' ? (yearlyFoodLiters * COW_TMR_RATIOS.straw) : 0
  const tmrYearlyHay = feedType === 'TMR' ? (yearlyFoodLiters * COW_TMR_RATIOS.hay) : (feedType === 'Hay' ? yearlyFoodLiters : 0)
  const tmrYearlySilage = feedType === 'TMR' ? (yearlyFoodLiters * COW_TMR_RATIOS.silage) : 0
  const tmrYearlyMineral = feedType === 'TMR' ? (yearlyFoodLiters * COW_TMR_RATIOS.mineralFeed) : 0

  // Hectáreas para mezclas TMR
  const tmrStrawMixHectares = tmrYearlyStraw / (5.244 * 10000)
  const tmrHayMixHectares = tmrYearlyHay / (grassYield * grassHarvests * 10000)
  const tmrSilageMixHectares = tmrYearlySilage / (selectedSilageYield * 10000)

  // Mineral Feed Cost
  const monthlyMineralCost = feedType === 'TMR' ? ((monthlyFoodLiters * COW_TMR_RATIOS.mineralFeed) * ANIMAL_CONSTANTS.mineralFeedPrice) : 0
  const yearlyMineralCost = monthlyMineralCost * 12

  return {
    production: {
      milk: { monthly: monthlyMilkLiters, yearly: yearlyMilkLiters, price: unitMilkPrice, revenueMonthly: monthlyMilkSales, revenueYearly: yearlyMilkSales },
      slurry: { monthly: monthlySlurryLiters, yearly: yearlySlurryLiters },
      manure: { monthly: monthlyManureLiters, yearly: yearlyManureLiters },
      straw: { monthly: -monthlyStrawLiters, yearly: -yearlyStrawLiters },
      food: { monthly: -monthlyFoodLiters, yearly: -yearlyFoodLiters }
    },
    fieldwork: {
      strawBedding: strawBeddingHectares,
      simple: {
        grass: simpleGrassHectares,
        silage: simpleSilageHectares
      },
      tmr: {
        strawMix: tmrStrawMixHectares,
        hayMix: tmrHayMixHectares,
        silageMix: tmrSilageMixHectares,
        totalTmrHectares: tmrStrawMixHectares + tmrHayMixHectares + tmrSilageMixHectares + strawBeddingHectares
      }
    },
    tmrUsage: {
      hay: tmrYearlyHay,
      silage: tmrYearlySilage,
      straw: tmrYearlyStraw,
      mineral: tmrYearlyMineral,
      mineralCostMonthly: monthlyMineralCost,
      mineralCostYearly: yearlyMineralCost
    },
    sales: {
      beefSales: yearlyBeefRevenue
    }
  }
}

// --- GALLINAS ---
export interface ChickenInputs {
  numChx: number
  yieldBonus: number
  difficulty: 'Easy' | 'Normal' | 'Hard'
  sellPriceType: 'Baseline' | 'MaxSeasonal'
  feedBoughtPercent: number // 0 a 100
  feedType: 'Oat' | 'Wheat' // Tipo de alimento comprado o cultivado
  fieldworkCrop: 'Barley' | 'Wheat' | 'Sorghum' // Cultivo a sembrar
}

export const calculateChickens = (inputs: ChickenInputs) => {
  const { numChx, yieldBonus, difficulty, feedBoughtPercent, feedType, fieldworkCrop } = inputs

  const bonusScalar = getYieldBonusScalar(yieldBonus)
  const diffScalar = ANIMAL_CONSTANTS.difficultyScalars.Chicken[difficulty]

  // Producción de Huevos: 5 Litros de huevo por gallina al mes
  const monthlyEggs = numChx * 5
  const yearlyEggs = monthlyEggs * 12

  // Venta de huevos: egg base (1.12) * egg price scalar (1.25) * difficultyScalar
  const eggPrice = ANIMAL_CONSTANTS.baseEggPrice * ANIMAL_CONSTANTS.eggPriceScalar * diffScalar
  const monthlyRevenue = monthlyEggs * eggPrice
  const yearlyRevenue = yearlyEggs * eggPrice

  // Consumo de alimento: 60 Litros al año por gallina (5 Litros al mes)
  const monthlyFeed = numChx * 5
  const yearlyFeed = monthlyFeed * 12

  const feedBoughtLiters = (yearlyFeed * feedBoughtPercent) / 100
  const feedGrownLiters = yearlyFeed - feedBoughtLiters

  // Costo de alimento comprado
  // Oat = 1.4 por litro, Wheat = 1.5 por litro en la tienda
  const unitFeedPrice = feedType === 'Oat' ? ANIMAL_CONSTANTS.feedOatPriceScalar : ANIMAL_CONSTANTS.feedWheatPriceScalar
  const yearlyFeedCost = feedBoughtLiters * unitFeedPrice
  const monthlyFeedCost = yearlyFeedCost / 12

  // Fieldwork para alimento cultivado
  const cropYieldMap: Record<string, number> = {
    Barley: ANIMAL_FIELDWORK_YIELDS.Barley,
    Wheat: ANIMAL_FIELDWORK_YIELDS.Wheat,
    Sorghum: ANIMAL_FIELDWORK_YIELDS.Sorghum
  }
  const cropYield = (cropYieldMap[fieldworkCrop] || ANIMAL_FIELDWORK_YIELDS.Wheat) * bonusScalar
  const fieldworkHectares = feedGrownLiters > 0 ? (feedGrownLiters / (cropYield * 10000)) : 0

  const netIncomeYearly = yearlyRevenue - yearlyFeedCost
  const netIncomeMonthly = monthlyRevenue - monthlyFeedCost

  return {
    eggs: { monthly: monthlyEggs, yearly: yearlyEggs, price: eggPrice, revenueMonthly: monthlyRevenue, revenueYearly: yearlyRevenue },
    feed: {
      total: yearlyFeed,
      bought: feedBoughtLiters,
      grown: feedGrownLiters,
      costMonthly: monthlyFeedCost,
      costYearly: yearlyFeedCost
    },
    fieldwork: {
      hectares: fieldworkHectares,
      crop: fieldworkCrop
    },
    net: {
      monthly: netIncomeMonthly,
      yearly: netIncomeYearly
    }
  }
}

// --- OVEJAS ---
export interface SheepInputs {
  numSheep: number
  yieldBonus: number
  grassHarvests: number
  difficulty: 'Easy' | 'Normal' | 'Hard'
  sellPriceType: 'Baseline' | 'MaxSeasonal'
}

export const calculateSheep = (inputs: SheepInputs) => {
  const { numSheep, yieldBonus, grassHarvests, difficulty } = inputs

  const bonusScalar = getYieldBonusScalar(yieldBonus)
  const diffScalar = ANIMAL_CONSTANTS.difficultyScalars.Sheep[difficulty]
  const grassYield = ANIMAL_FIELDWORK_YIELDS.Grass * bonusScalar

  // Ovejas -> Lana
  // Producción mensual de lana por oveja: 58.8235294117647 Litros
  const monthlyWoolLiters = numSheep * 58.8235294117647
  const yearlyWoolLiters = monthlyWoolLiters * 12
  const woolPrice = ANIMAL_CONSTANTS.baseWoolPrice * ANIMAL_CONSTANTS.woolPriceScalar * diffScalar
  const monthlyWoolSales = monthlyWoolLiters * woolPrice
  const yearlyWoolSales = yearlyWoolLiters * woolPrice

  // Consumo de comida (Pasto/Heno)
  // Oveja: 48.5588235294117 Litros al mes
  const monthlySheepFeed = numSheep * 48.5588235294117
  const yearlySheepFeed = monthlySheepFeed * 12

  // Fieldwork Hectáreas (Pasto)
  const sheepHectares = yearlySheepFeed / (grassYield * grassHarvests * 10000)

  return {
    wool: { monthly: monthlyWoolLiters, yearly: yearlyWoolLiters, price: woolPrice, revenueMonthly: monthlyWoolSales, revenueYearly: yearlyWoolSales },
    feed: {
      monthly: monthlySheepFeed,
      yearly: yearlySheepFeed,
      totalYearly: yearlySheepFeed
    },
    fieldwork: {
      hectares: sheepHectares,
      totalHectares: sheepHectares
    }
  }
}

// --- CABRAS ---
export interface GoatInputs {
  numGoats: number
  yieldBonus: number
  grassHarvests: number
  difficulty: 'Easy' | 'Normal' | 'Hard'
  sellPriceType: 'Baseline' | 'MaxSeasonal'
}

export const calculateGoats = (inputs: GoatInputs) => {
  const { numGoats, yieldBonus, grassHarvests, difficulty } = inputs

  const bonusScalar = getYieldBonusScalar(yieldBonus)
  const diffScalar = ANIMAL_CONSTANTS.difficultyScalars.Sheep[difficulty]
  const grassYield = ANIMAL_FIELDWORK_YIELDS.Grass * bonusScalar

  // Cabras -> Leche de cabra
  // Producción mensual por cabra: 25 Litros
  const monthlyGoatMilkLiters = numGoats * 25
  const yearlyGoatMilkLiters = monthlyGoatMilkLiters * 12
  const goatMilkPrice = ANIMAL_CONSTANTS.baseGoatMilkPrice * ANIMAL_CONSTANTS.goatMilkPriceScalar * diffScalar
  const monthlyGoatMilkSales = monthlyGoatMilkLiters * goatMilkPrice
  const yearlyGoatMilkSales = yearlyGoatMilkLiters * goatMilkPrice

  // Consumo de comida (Pasto/Heno)
  // Cabra: 50 Litros al mes
  const monthlyGoatFeed = numGoats * 50
  const yearlyGoatFeed = monthlyGoatFeed * 12

  // Fieldwork Hectáreas (Pasto)
  const goatHectares = yearlyGoatFeed / (grassYield * grassHarvests * 10000)

  return {
    goatMilk: { monthly: monthlyGoatMilkLiters, yearly: yearlyGoatMilkLiters, price: goatMilkPrice, revenueMonthly: monthlyGoatMilkSales, revenueYearly: yearlyGoatMilkSales },
    feed: {
      monthly: monthlyGoatFeed,
      yearly: yearlyGoatFeed,
      totalYearly: yearlyGoatFeed
    },
    fieldwork: {
      hectares: goatHectares,
      totalHectares: goatHectares
    }
  }
}

// --- CERDOS ---
export interface PigInputs {
  numPigs: number
  yieldBonus: number
  difficulty: 'Easy' | 'Normal' | 'Hard'
  sellPriceType: 'Baseline' | 'MaxSeasonal'
  sellCount: number
  provideStraw: boolean
  // Ratios para cultivos dentro de cada categoría
  baseCrop: 'Corn' | 'Sorghum'
  grainCrop: 'Wheat' | 'Barley'
  proteinCrop: 'Soy' | 'Canola' | 'Sunflower'
  rootCrop: 'Potato' | 'Sugarbeet' | 'Redbeet' | 'Parsnip' | 'Carrot'
}

export const calculatePigs = (inputs: PigInputs) => {
  const { numPigs, yieldBonus, sellCount, provideStraw, baseCrop, grainCrop, proteinCrop, rootCrop } = inputs

  const bonusScalar = getYieldBonusScalar(yieldBonus)

  // Residuos y camas
  const yearlySlurry = 65 * numPigs * 12
  const yearlyStraw = provideStraw ? (20 * numPigs * 12) : 0
  const yearlyManure = provideStraw ? (35 * numPigs * 12) : 0

  // Ventas de cerdos (2500 por cerdo)
  const yearlySales = sellCount * 2500.0

  // Alimento anual total
  // Base: 30 L/cerdo/mes, Grain: 15 L/cerdo/mes, Protein: 12 L/cerdo/mes, Root: 3 L/cerdo/mes
  const baseLiters = numPigs * 1.0 * 30 * 12
  const grainLiters = numPigs * 1.0 * 15 * 12
  const proteinLiters = numPigs * 1.0 * 12 * 12
  const rootLiters = numPigs * 1.0 * 3 * 12
  const totalFeedLiters = baseLiters + grainLiters + proteinLiters + rootLiters

  // Rendimiento cultivos (del sheet Yield)
  const yields: Record<string, number> = {
    Corn: ANIMAL_FIELDWORK_YIELDS.Corn,
    Sorghum: ANIMAL_FIELDWORK_YIELDS.Sorghum,
    Wheat: ANIMAL_FIELDWORK_YIELDS.Wheat,
    Barley: ANIMAL_FIELDWORK_YIELDS.Barley,
    Soy: ANIMAL_FIELDWORK_YIELDS.Soybean,
    Canola: ANIMAL_FIELDWORK_YIELDS.Canola,
    Sunflower: ANIMAL_FIELDWORK_YIELDS.Sunflower,
    Potato: ANIMAL_FIELDWORK_YIELDS.Potato,
    'Sugar Beet': ANIMAL_FIELDWORK_YIELDS.Sugarbeet,
    'Red Beet': ANIMAL_FIELDWORK_YIELDS.Redbeet,
    Parsnip: ANIMAL_FIELDWORK_YIELDS.Parsnip,
    Carrot: ANIMAL_FIELDWORK_YIELDS.Carrot
  }

  // Mapear crops
  const getCropYield = (c: string) => {
    let name = c
    if (c === 'Sugarbeet') name = 'Sugar Beet'
    if (c === 'Redbeet') name = 'Red Beet'
    return yields[name] || 1.0
  }

  // Fieldwork Hectáreas
  const baseHectares = baseLiters / (getCropYield(baseCrop) * bonusScalar * 10000)
  const grainHectares = grainLiters / (getCropYield(grainCrop) * bonusScalar * 10000)
  const proteinHectares = proteinLiters / (getCropYield(proteinCrop) * bonusScalar * 10000)
  const rootHectares = rootLiters / (getCropYield(rootCrop) * bonusScalar * 10000)

  return {
    production: {
      slurry: yearlySlurry,
      straw: -yearlyStraw,
      manure: yearlyManure,
      totalFeed: totalFeedLiters
    },
    feedBreakdown: {
      base: { liters: baseLiters, crop: baseCrop, hectares: baseHectares },
      grain: { liters: grainLiters, crop: grainCrop, hectares: grainHectares },
      protein: { liters: proteinLiters, crop: proteinCrop, hectares: proteinHectares },
      root: { liters: rootLiters, crop: rootCrop, hectares: rootHectares },
      totalHectares: baseHectares + grainHectares + proteinHectares + rootHectares
    },
    sales: {
      porkSales: yearlySales
    }
  }
}

// --- CABALLOS ---
export interface HorseInputs {
  numHorses: number
  yieldBonus: number
  grassHarvests: number
  sellCount: number
  provideStraw: boolean
  baseCrop: 'Oat' | 'Sorghum'
  rootCrop: 'Potato' | 'Sugarbeet' | 'Redbeet' | 'Parsnip' | 'Carrot'
}

export const calculateHorses = (inputs: HorseInputs) => {
  const { numHorses, yieldBonus, grassHarvests, sellCount, provideStraw, baseCrop, rootCrop } = inputs

  const bonusScalar = getYieldBonusScalar(yieldBonus)

  // Residuos y camas
  const yearlyStraw = provideStraw ? (80 * numHorses * 12) : 0
  const yearlyManure = provideStraw ? (200 * numHorses * 12) : 0

  // Ventas de caballos
  const yearlySales = sellCount * 5000.0

  // Consumos
  // Base (Oat/Sorghum): 95.25 L/mes/caballo
  // Hay: 285.75 L/mes/caballo
  // Root: 19.0625 L/mes/caballo
  const baseLiters = numHorses * 95.25 * 12
  const hayLiters = numHorses * 285.75 * 12
  const rootLiters = numHorses * 19.0625 * 12
  const totalFeedLiters = baseLiters + hayLiters + rootLiters

  // Rendimientos (del sheet Yield con Horse Yield Scalar en Var B53 = 1.425 por defecto, aquí usamos el de inputs)
  const yields: Record<string, number> = {
    Oat: ANIMAL_FIELDWORK_YIELDS.Oat,
    Sorghum: ANIMAL_FIELDWORK_YIELDS.Sorghum,
    Grass: ANIMAL_FIELDWORK_YIELDS.Grass,
    Potato: ANIMAL_FIELDWORK_YIELDS.Potato,
    'Sugar Beet': ANIMAL_FIELDWORK_YIELDS.Sugarbeet,
    'Red Beet': ANIMAL_FIELDWORK_YIELDS.Redbeet,
    Parsnip: ANIMAL_FIELDWORK_YIELDS.Parsnip,
    Carrot: ANIMAL_FIELDWORK_YIELDS.Carrot
  }

  const getCropYield = (c: string) => {
    let name = c
    if (c === 'Sugarbeet') name = 'Sugar Beet'
    if (c === 'Redbeet') name = 'Red Beet'
    return yields[name] || 1.0
  }

  // Fieldwork Hectares
  // Base: (Liters / (yield * bonusScalar * 10000))
  // Hay: (Liters / (yieldGrass * bonusScalar * grassHarvests * 10000))
  const baseHectares = baseLiters / (getCropYield(baseCrop) * bonusScalar * 10000)
  const hayHectares = hayLiters / (getCropYield('Grass') * bonusScalar * grassHarvests * 10000)
  const rootHectares = rootLiters / (getCropYield(rootCrop) * bonusScalar * 10000)

  return {
    production: {
      straw: -yearlyStraw,
      manure: yearlyManure,
      totalFeed: totalFeedLiters
    },
    feedBreakdown: {
      base: { liters: baseLiters, crop: baseCrop, hectares: baseHectares },
      hay: { liters: hayLiters, crop: 'Hay', hectares: hayHectares },
      root: { liters: rootLiters, crop: rootCrop, hectares: rootHectares },
      totalHectares: baseHectares + hayHectares + rootHectares
    },
    sales: {
      horseSales: yearlySales
    }
  }
}

// --- BÚFALOS DE AGUA ---
export interface BuffaloInputs {
  numBuffaloes: number
  yieldBonus: number
  grassHarvests: number
  provideStraw: boolean
  feedType: 'TMR' | 'Hay' | 'Grass'
  difficulty: 'Easy' | 'Normal' | 'Hard'
  sellPriceType: 'Baseline' | 'MaxSeasonal'
  sellCount: number
  percentProductive: number
  silageCrop: string
}

export const calculateBuffaloes = (inputs: BuffaloInputs) => {
  const {
    numBuffaloes,
    yieldBonus,
    grassHarvests,
    provideStraw,
    feedType,
    difficulty,
    sellPriceType,
    sellCount,
    percentProductive,
    silageCrop
  } = inputs

  const bonusScalar = getYieldBonusScalar(yieldBonus)
  const diffScalar = ANIMAL_CONSTANTS.difficultyScalars.Buffalo[difficulty]

  // Productividad según alimento
  const productivityFactor = feedType === 'TMR' ? 1.0 : feedType === 'Hay' ? 0.8 : 0.4

  // Producción de leche (leche de búfala es 5 veces más cara que vaca, base buffalo milk price es 3.5 en ANIMAL_CONSTANTS)
  // base prod rate is 4100 L/mes
  const monthlyMilkLiters = numBuffaloes * ANIMAL_RATES.Buffalo.milk * (percentProductive / 100) * productivityFactor
  const yearlyMilkLiters = monthlyMilkLiters * 12

  // Precio leche
  const milkPriceScalar = sellPriceType === 'MaxSeasonal' ? MILK_PRICE_SCALARS.max : MILK_PRICE_SCALARS.average
  const unitMilkPrice = ANIMAL_CONSTANTS.baseBuffaloMilkPrice * diffScalar * milkPriceScalar
  const monthlyMilkSales = monthlyMilkLiters * unitMilkPrice
  const yearlyMilkSales = yearlyMilkLiters * unitMilkPrice

  // Consumo alimento
  // Tasa de alimento base: 10,500 L/mes.
  const monthlyFoodRate = Math.abs(ANIMAL_RATES.Buffalo.food)
  const monthlyFoodLiters = numBuffaloes * monthlyFoodRate
  const yearlyFoodLiters = monthlyFoodLiters * 12

  // Residuos y camas
  // Con Paja: genera Purín (80 L/día = 2400 L/mes) y Estiércol (120 L/día = 3600 L/mes)
  // Sin Paja: todo Purín (180 L/día = 5400 L/mes)
  const monthlySlurryLiters = provideStraw 
    ? (numBuffaloes * ANIMAL_RATES.Buffalo.slurry) 
    : (numBuffaloes * 5400)
  const yearlySlurryLiters = monthlySlurryLiters * 12

  const monthlyManureLiters = provideStraw 
    ? (numBuffaloes * ANIMAL_RATES.Buffalo.manure) 
    : 0
  const yearlyManureLiters = monthlyManureLiters * 12

  const monthlyStrawLiters = provideStraw 
    ? (numBuffaloes * Math.abs(ANIMAL_RATES.Buffalo.straw)) 
    : 0
  const yearlyStrawLiters = monthlyStrawLiters * 12

  // Buffalo Sales (precio unitario de venta estimado $3,000)
  const unitBuffaloPrice = 3000.0
  const yearlyBuffaloRevenue = unitBuffaloPrice * sellCount

  // Fieldwork para cama de paja
  const strawBeddingHectares = provideStraw ? (yearlyStrawLiters / 5.244 / 10000) : 0

  // Fieldwork para alimentación
  const grassYield = ANIMAL_FIELDWORK_YIELDS.Grass * bonusScalar
  let fieldworkGrassHectares = 0
  let fieldworkHayHectares = 0
  let fieldworkSilageHectares = 0

  // TMR components
  const tmrYearlyStraw = feedType === 'TMR' ? (yearlyFoodLiters * BUFFALO_TMR_RATIOS.straw) : 0
  const tmrYearlyHay = feedType === 'TMR' ? (yearlyFoodLiters * BUFFALO_TMR_RATIOS.hay) : (feedType === 'Hay' ? yearlyFoodLiters : 0)
  const tmrYearlySilage = feedType === 'TMR' ? (yearlyFoodLiters * BUFFALO_TMR_RATIOS.silage) : 0
  const tmrYearlyMineral = feedType === 'TMR' ? (yearlyFoodLiters * BUFFALO_TMR_RATIOS.mineralFeed) : 0

  const silageYieldMap: Record<string, number> = {
    Corn: ANIMAL_FIELDWORK_YIELDS.Corn * ANIMAL_FIELDWORK_YIELDS.CornChaffMult,
    Barley: ANIMAL_FIELDWORK_YIELDS.Barley * ANIMAL_FIELDWORK_YIELDS.BarleyChaffMult,
    Wheat: ANIMAL_FIELDWORK_YIELDS.Wheat * ANIMAL_FIELDWORK_YIELDS.WheatChaffMult,
    Sorghum: ANIMAL_FIELDWORK_YIELDS.Sorghum * ANIMAL_FIELDWORK_YIELDS.SorghumChaffMult,
    Sunflower: ANIMAL_FIELDWORK_YIELDS.Sunflower * ANIMAL_FIELDWORK_YIELDS.SunflowerChaffMult,
    Oat: ANIMAL_FIELDWORK_YIELDS.Oat * ANIMAL_FIELDWORK_YIELDS.OatChaffMult,
    Canola: ANIMAL_FIELDWORK_YIELDS.Canola * ANIMAL_FIELDWORK_YIELDS.CanolaChaffMult,
    Soybean: ANIMAL_FIELDWORK_YIELDS.Soybean * ANIMAL_FIELDWORK_YIELDS.SoybeanChaffMult
  }
  const selectedSilageBaseYield = silageYieldMap[silageCrop] || (ANIMAL_FIELDWORK_YIELDS.Corn * ANIMAL_FIELDWORK_YIELDS.CornChaffMult)
  const selectedSilageYield = selectedSilageBaseYield * bonusScalar

  // Hectáreas para mezclas y alimentación directa
  const tmrStrawMixHectares = tmrYearlyStraw / (5.244 * 10000)
  
  if (feedType === 'Grass') {
    // Si comen pasto directo
    fieldworkGrassHectares = yearlyFoodLiters / (grassHarvests * grassYield * 10000)
  } else if (feedType === 'Hay') {
    // Si comen heno directo
    fieldworkHayHectares = yearlyFoodLiters / (grassHarvests * grassYield * 10000)
  } else {
    // TMR Mixes
    fieldworkHayHectares = tmrYearlyHay / (grassYield * grassHarvests * 10000)
    fieldworkSilageHectares = tmrYearlySilage / (selectedSilageYield * 10000)
  }

  // Costo alimento mineral en TMR
  const monthlyMineralCost = (monthlyFoodLiters * BUFFALO_TMR_RATIOS.mineralFeed) * ANIMAL_CONSTANTS.mineralFeedPrice
  const yearlyMineralCost = monthlyMineralCost * 12

  return {
    production: {
      milk: { monthly: monthlyMilkLiters, yearly: yearlyMilkLiters, price: unitMilkPrice, revenueMonthly: monthlyMilkSales, revenueYearly: yearlyMilkSales },
      slurry: { monthly: monthlySlurryLiters, yearly: yearlySlurryLiters },
      manure: { monthly: monthlyManureLiters, yearly: yearlyManureLiters },
      straw: { monthly: -monthlyStrawLiters, yearly: -yearlyStrawLiters },
      food: { monthly: -monthlyFoodLiters, yearly: -yearlyFoodLiters }
    },
    fieldwork: {
      strawBedding: strawBeddingHectares,
      tmr: {
        strawMix: tmrStrawMixHectares,
        hayMix: fieldworkHayHectares,
        silageMix: fieldworkSilageHectares,
        totalTmrHectares: tmrStrawMixHectares + fieldworkHayHectares + fieldworkSilageHectares + strawBeddingHectares
      },
      simple: {
        grass: fieldworkGrassHectares,
        silage: fieldworkSilageHectares
      }
    },
    tmrUsage: {
      hay: tmrYearlyHay,
      silage: tmrYearlySilage,
      straw: tmrYearlyStraw,
      mineral: tmrYearlyMineral,
      mineralCostMonthly: feedType === 'TMR' ? monthlyMineralCost : 0,
      mineralCostYearly: feedType === 'TMR' ? yearlyMineralCost : 0
    },
    sales: {
      buffaloSales: yearlyBuffaloRevenue
    }
  }
}
