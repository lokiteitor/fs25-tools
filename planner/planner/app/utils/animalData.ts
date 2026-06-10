// app/utils/animalData.ts

export interface AnimalConstant {
  yieldBonusScalar: number
  strawBonus: number
  baseProdRate: number
  difficultyScalars: {
    Cow: { Easy: number; Normal: number; Hard: number }
    Chicken: { Easy: number; Normal: number; Hard: number }
    Sheep: { Easy: number; Normal: number; Hard: number }
    Pig: { Easy: number; Normal: number; Hard: number }
    Horse: { Easy: number; Normal: number; Hard: number }
    Buffalo: { Easy: number; Normal: number; Hard: number }
  }
  baseMilkPrice: number
  baseEggPrice: number
  baseWoolPrice: number
  baseGoatMilkPrice: number
  baseBuffaloMilkPrice: number
  eggPriceScalar: number
  woolPriceScalar: number
  goatMilkPriceScalar: number
  mineralFeedPrice: number
  feedOatPriceScalar: number // precio compra Oat
  feedWheatPriceScalar: number // precio compra Wheat
}

export const ANIMAL_CONSTANTS: AnimalConstant = {
  yieldBonusScalar: 1.425,
  strawBonus: 0.11111111,
  baseProdRate: 1,
  difficultyScalars: {
    Cow: { Easy: 3.0, Normal: 1.8, Hard: 1.0 },
    Chicken: { Easy: 3.0, Normal: 1.8, Hard: 1.0 },
    Sheep: { Easy: 3.0, Normal: 1.8, Hard: 1.0 },
    Pig: { Easy: 3.0, Normal: 1.8, Hard: 1.0 },
    Horse: { Easy: 3.0, Normal: 1.8, Hard: 1.0 },
    Buffalo: { Easy: 3.0, Normal: 1.8, Hard: 1.0 }
  },
  baseMilkPrice: 0.7,
  baseEggPrice: 1.12,
  baseWoolPrice: 0.94,
  baseGoatMilkPrice: 2.82,
  baseBuffaloMilkPrice: 3.5, // Buffalo milk is 5x standard cow milk (0.7 * 5 = 3.5)
  eggPriceScalar: 1.25, // da 1.4
  woolPriceScalar: 1.29, // da 3.6378 en easy (0.94 * 1.29 * 3)
  goatMilkPriceScalar: 1.08, // da 9.1368 en easy (2.82 * 1.08 * 3)
  mineralFeedPrice: 0.9523809524,
  feedOatPriceScalar: 1.4,
  feedWheatPriceScalar: 1.5
}

// Multiplicadores de precio mensual para leche
export const MILK_MONTHLY_SCALARS = [
  { month: 1, name: 'MAR', value: 1.06 },
  { month: 2, name: 'APR', value: 1.01 },
  { month: 3, name: 'MAY', value: 0.96 },
  { month: 4, name: 'JUN', value: 0.90 },
  { month: 5, name: 'JUL', value: 0.95 },
  { month: 6, name: 'AGU', value: 0.95 },
  { month: 7, name: 'SEP', value: 1.03 },
  { month: 8, name: 'OCT', value: 1.09 },
  { month: 9, name: 'NOV', value: 0.98 },
  { month: 10, name: 'DEC', value: 0.96 },
  { month: 11, name: 'JAN', value: 1.08 },
  { month: 12, name: 'FEB', value: 1.07 }
]

// Promedios y máximos de la leche
export const MILK_PRICE_SCALARS = {
  average: 1.003333333,
  max: 1.09
}

// Tasas mensuales base por animal (Rate sheet)
export const ANIMAL_RATES = {
  Cow: {
    milk: 135,
    food: -350,
    slurry: 250,
    manure: 200,
    straw: -95
  },
  Buffalo: {
    milk: 4100, // 4,100 L/month
    food: -10500, // 10,500 L/month TMR
    slurry: 2400, // with straw: 80 L/day * 30
    manure: 3600, // with straw: 120 L/day * 30
    straw: -200 // straw bedding consumed per month
  },
  Pig: {
    slurry: 65,
    straw: -20,
    manure: 35
  },
  Horse: {
    straw: -80,
    manure: 200
  }
}

// Ratios por defecto del TMR de Vacas y Búfalos
export const COW_TMR_RATIOS = {
  hay: 0.3744,
  silage: 0.3744,
  straw: 0.2032,
  mineralFeed: 0.048
}

export const BUFFALO_TMR_RATIOS = {
  hay: 0.3744,
  silage: 0.3744,
  straw: 0.2032,
  mineralFeed: 0.048
}

// Rendimientos base por m2 usados para fieldwork (del Yield sheet)
export const ANIMAL_FIELDWORK_YIELDS = {
  Grass: 4.37,
  Corn: 0.92,
  CornChaffMult: 7.8, // da 7.176 chaff yield
  Barley: 0.96,
  BarleyChaffMult: 4.0, // da 3.84
  Wheat: 0.89,
  WheatChaffMult: 4.0,
  Sorghum: 0.82,
  SorghumChaffMult: 4.0,
  Sunflower: 0.52,
  SunflowerChaffMult: 6.0,
  Oat: 0.57,
  OatChaffMult: 4.0,
  Canola: 0.58,
  CanolaChaffMult: 4.0,
  Soybean: 0.45,
  SoybeanChaffMult: 4.0,
  Potato: 4.13,
  Sugarbeet: 5.78,
  Redbeet: 5.78,
  Parsnip: 6.95,
  Carrot: 7.7
}
