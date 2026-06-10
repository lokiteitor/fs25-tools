import { crops, silageCrops } from './cropData';
import type { Crop, SilageCrop } from './cropData';

// Constants from the Excel sheet Variables
export const SILAGE_PRICE = 0.121;
export const SILAGE_WEIGHT = 0.3;

export interface Field {
  name: string;
  hectares: number;
  cropName: string;
  isSilage?: boolean;
}

export interface DifficultyIncome {
  easy: number;
  normal: number;
  hard: number;
}

export interface FieldResult {
  fieldName: string;
  hectares: number;
  cropName: string;
  isSilage: boolean;
  yieldM3: number;
  yieldTons: number;
  income: {
    baseline: DifficultyIncome;
    maxSeasonal: DifficultyIncome;
  };
}

export interface CalculationResult {
  fields: FieldResult[];
  totals: {
    hectares: number;
    yieldM3: number;
    yieldTons: number;
    income: {
      baseline: DifficultyIncome;
      maxSeasonal: DifficultyIncome;
    };
  };
}

/**
 * Calculates yield in cubic meters (m3).
 * Formula: yield * hectares * 10000 * yieldBonusScalar * 0.001
 * 
 * @param yieldVal Base yield per m2 (yield from Crop or Silage Data)
 * @param hectares Number of hectares
 * @param yieldBonusScalar Yield bonus scalar (e.g. 1 + yieldBonus)
 */
export function calculateYieldM3(yieldVal: number, hectares: number, yieldBonusScalar: number): number {
  return yieldVal * hectares * 10000 * yieldBonusScalar * 0.001;
}

/**
 * Calculates yield in metric tons.
 * Formula: m3 * weight
 * 
 * @param m3 Yield in cubic meters
 * @param weight Weight per liter (equivalent to tons per m3)
 */
export function calculateYieldTons(m3: number, weight: number): number {
  return m3 * weight;
}

/**
 * Calculates economic income according to difficulty (Easy = Hard * 3, Normal = Hard * 1.8, Hard = base)
 * and price multiplier.
 * 
 * @param m3 Yield in cubic meters
 * @param price Base price per liter
 * @param priceMultiplier Price multiplier (1.0 for Baseline, maxPrice for Max Seasonal)
 */
export function calculateIncomeByDifficulty(
  m3: number,
  price: number,
  priceMultiplier: number
): DifficultyIncome {
  // m3 * 1000 converts cubic meters to liters for price conversion
  const hard = m3 * 1000 * price * priceMultiplier;
  const normal = hard * 1.8;
  const easy = hard * 3.0;
  return { easy, normal, hard };
}

// Mapa de traducción para compatibilidad con datos previamente guardados en inglés
const cropTranslationMap: Record<string, string> = {
  "barley": "Cebada",
  "beet root": "Remolacha",
  "canola": "Canola",
  "carrot": "Zanahoria",
  "corn": "Maíz",
  "cotton": "Algodón",
  "grape": "Uva",
  "green bean": "Judías Verdes",
  "oat": "Avena",
  "olive": "Oliva",
  "onion": "Cebollas",
  "onions": "Cebollas",
  "parsnip": "Chirivía",
  "pea": "Guisantes",
  "potato": "Patatas",
  "rice (long)": "Arroz (Largo)",
  "rice (short)": "Arroz (Corto)",
  "sorghum": "Sorgo",
  "soybean": "Soja",
  "spinach": "Espinacas",
  "sugarbeet": "Remolacha Azucarera",
  "sugarcane": "Caña de Azúcar",
  "sunflower": "Girasol",
  "wheat": "Trigo",
  "grass": "Hierba",
  "poplar (woodchips)": "Álamo (Astillas de Madera)",
  "poplar": "Álamo"
};

/**
 * Helper function to find a crop in the main crops list, matching case-insensitively and flexibly.
 */
export function findCrop(cropName: string): Crop | undefined {
  let cleanName = cropName.trim().toLowerCase();
  // Traducir si se proporciona un nombre en inglés
  if (cropTranslationMap[cleanName]) {
    cleanName = cropTranslationMap[cleanName].toLowerCase();
  }
  return crops.find(c => {
    const cleanCropName = c.name.trim().toLowerCase();
    return cleanName === cleanCropName || cleanName.startsWith(cleanCropName) || cleanCropName.startsWith(cleanName);
  });
}

/**
 * Helper function to find a silage crop in the silage crops list, matching case-insensitively and flexibly.
 */
export function findSilageCrop(cropName: string): SilageCrop | undefined {
  let cleanName = cropName.trim().toLowerCase();
  // Traducir si se proporciona un nombre en inglés
  if (cropTranslationMap[cleanName]) {
    cleanName = cropTranslationMap[cleanName].toLowerCase();
  }
  return silageCrops.find(c => {
    const cleanSilageName = c.name.trim().toLowerCase();
    return cleanName === cleanSilageName || cleanName.startsWith(cleanSilageName) || cleanSilageName.startsWith(cleanName);
  });
}

/**
 * Calculates results for a list of fields and a given yield bonus.
 * 
 * @param fields List of fields to calculate
 * @param yieldBonus The yield bonus as a decimal (e.g. 0.425 for 42.5% bonus). The scalar will be (1 + yieldBonus).
 */
export function calculateFields(fields: Field[], yieldBonus: number): CalculationResult {
  const yieldBonusScalar = 1 + yieldBonus;
  const fieldResults: FieldResult[] = [];

  let totalHectares = 0;
  let totalYieldM3 = 0;
  let totalYieldTons = 0;

  const totalIncomeBaseline: DifficultyIncome = { easy: 0, normal: 0, hard: 0 };
  const totalIncomeMaxSeasonal: DifficultyIncome = { easy: 0, normal: 0, hard: 0 };

  for (const field of fields) {
    const isSilage = !!field.isSilage;
    let yieldVal = 0;
    let weight = 0;
    let price = 0;
    let maxPriceMultiplier = 1.0;

    if (isSilage) {
      const silageCrop = findSilageCrop(field.cropName);
      if (!silageCrop) {
        throw new Error(`Silage crop data not found for name: ${field.cropName}`);
      }
      yieldVal = silageCrop.yield * silageCrop.chaff;
      weight = SILAGE_WEIGHT;
      price = SILAGE_PRICE;
      maxPriceMultiplier = 1.0;
    } else {
      const crop = findCrop(field.cropName);
      if (!crop) {
        throw new Error(`Crop data not found for name: ${field.cropName}`);
      }
      yieldVal = crop.yield;
      weight = crop.weight;
      price = crop.price;
      maxPriceMultiplier = crop.maxPrice;
    }

    const yieldM3 = calculateYieldM3(yieldVal, field.hectares, yieldBonusScalar);
    const yieldTons = calculateYieldTons(yieldM3, weight);

    const baselineIncome = calculateIncomeByDifficulty(yieldM3, price, 1.0);
    const maxSeasonalIncome = calculateIncomeByDifficulty(yieldM3, price, maxPriceMultiplier);

    fieldResults.push({
      fieldName: field.name,
      hectares: field.hectares,
      cropName: field.cropName,
      isSilage,
      yieldM3,
      yieldTons,
      income: {
        baseline: baselineIncome,
        maxSeasonal: maxSeasonalIncome
      }
    });

    totalHectares += field.hectares;
    totalYieldM3 += yieldM3;
    totalYieldTons += yieldTons;

    totalIncomeBaseline.easy += baselineIncome.easy;
    totalIncomeBaseline.normal += baselineIncome.normal;
    totalIncomeBaseline.hard += baselineIncome.hard;

    totalIncomeMaxSeasonal.easy += maxSeasonalIncome.easy;
    totalIncomeMaxSeasonal.normal += maxSeasonalIncome.normal;
    totalIncomeMaxSeasonal.hard += maxSeasonalIncome.hard;
  }

  return {
    fields: fieldResults,
    totals: {
      hectares: totalHectares,
      yieldM3: totalYieldM3,
      yieldTons: totalYieldTons,
      income: {
        baseline: totalIncomeBaseline,
        maxSeasonal: totalIncomeMaxSeasonal
      }
    }
  };
}
