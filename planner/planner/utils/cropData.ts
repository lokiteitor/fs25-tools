export interface Crop {
  name: string;
  yield: number;
  price: number;
  maxPrice: number;
  seed: number;
  weight: number;
}

export interface SilageCrop {
  name: string;
  yield: number;
  chaff: number;
}

export const crops: Crop[] = [
  {
    name: "Barley",
    yield: 0.96,
    price: 0.313,
    maxPrice: 1.21,
    seed: 0.0265,
    weight: 0.68
  },
  {
    name: "Beet Root",
    yield: 5.78,
    price: 0.122,
    maxPrice: 1.15,
    seed: 0.004,
    weight: 0.52
  },
  {
    name: "Canola",
    yield: 0.58,
    price: 0.603,
    maxPrice: 1.21,
    seed: 0.0049,
    weight: 0.6
  },
  {
    name: "Carrot",
    yield: 7.7,
    price: 0.132,
    maxPrice: 1.15,
    seed: 0.001,
    weight: 0.64
  },
  {
    name: "Corn",
    yield: 0.92,
    price: 0.38,
    maxPrice: 1.33,
    seed: 0.0053,
    weight: 0.8
  },
  {
    name: "Cotton",
    yield: 0.497,
    price: 1.252,
    maxPrice: 1.11,
    seed: 0.005,
    weight: 0.23
  },
  {
    name: "Grape",
    yield: 1.84,
    price: 0.603,
    maxPrice: 1.2,
    seed: 0.0,
    weight: 0.6
  },
  {
    name: "Green Bean",
    yield: 0.6975,
    price: 0.72,
    maxPrice: 1.05,
    seed: 0.028,
    weight: 0.42
  },
  {
    name: "Oat",
    yield: 0.57,
    price: 0.532,
    maxPrice: 1.21,
    seed: 0.034,
    weight: 0.5
  },
  {
    name: "Olive",
    yield: 1.84,
    price: 0.603,
    maxPrice: 1.2,
    seed: 0.0,
    weight: 0.6
  },
  {
    name: "Onion",
    yield: 7.0,
    price: 0.75,
    maxPrice: 3.0,
    seed: 0.0005,
    weight: 1.0
  },
  {
    name: "Parsnip",
    yield: 6.95,
    price: 0.131,
    maxPrice: 1.15,
    seed: 0.001,
    weight: 0.58
  },
  {
    name: "Pea",
    yield: 0.96,
    price: 1.04,
    maxPrice: 1.1,
    seed: 0.025,
    weight: 0.72
  },
  {
    name: "Potato",
    yield: 4.13,
    price: 0.222,
    maxPrice: 1.15,
    seed: 0.3733,
    weight: 0.75
  },
  {
    name: "Rice (Long)",
    yield: 0.9,
    price: 0.53,
    maxPrice: 1.05,
    seed: 0.05,
    weight: 0.77
  },
  {
    name: "Rice (Short)",
    yield: 0.66,
    price: 1.1,
    maxPrice: 1.05,
    seed: 0.015625,
    weight: 0.79
  },
  {
    name: "Sorghum",
    yield: 0.82,
    price: 0.43,
    maxPrice: 1.22,
    seed: 0.0035,
    weight: 0.85
  },
  {
    name: "Soybean",
    yield: 0.45,
    price: 0.778,
    maxPrice: 1.59,
    seed: 0.0214,
    weight: 0.7
  },
  {
    name: "Spinach",
    yield: 2.31,
    price: 0.22,
    maxPrice: 1.05,
    seed: 0.001,
    weight: 0.13
  },
  {
    name: "Sugarbeet",
    yield: 5.78,
    price: 0.172,
    maxPrice: 1.15,
    seed: 0.0034,
    weight: 0.7
  },
  {
    name: "Sugarcane",
    yield: 11.34,
    price: 0.119,
    maxPrice: 1.05,
    seed: 1.2,
    weight: 0.18
  },
  {
    name: "Sunflower",
    yield: 0.52,
    price: 0.673,
    maxPrice: 1.2,
    seed: 0.0143,
    weight: 0.35
  },
  {
    name: "Wheat",
    yield: 0.89,
    price: 0.337,
    maxPrice: 1.21,
    seed: 0.0308,
    weight: 0.78
  },
  {
    name: "Grass",
    yield: 4.37,
    price: 0.045,
    maxPrice: 1.11,
    seed: 0.012,
    weight: 0.3
  },
  {
    name: "Poplar (Woodchips)",
    yield: 19.881,
    price: 0.32,
    maxPrice: 1.69,
    seed: 0.15,
    weight: 0.35
  }
];

export const silageCrops: SilageCrop[] = [
  {
    name: "Barley",
    yield: 0.96,
    chaff: 4.0
  },
  {
    name: "Canola",
    yield: 0.58,
    chaff: 4.0
  },
  {
    name: "Corn",
    yield: 0.92,
    chaff: 7.8
  },
  {
    name: "Oat",
    yield: 0.57,
    chaff: 4.0
  },
  {
    name: "Sorghum",
    yield: 0.82,
    chaff: 4.0
  },
  {
    name: "Soybean",
    yield: 0.45,
    chaff: 4.0
  },
  {
    name: "Sunflower",
    yield: 0.52,
    chaff: 6.0
  },
  {
    name: "Wheat",
    yield: 0.89,
    chaff: 4.0
  },
  {
    name: "Grass",
    yield: 4.37,
    chaff: 1.0
  },
  {
    name: "Poplar",
    yield: 6.627,
    chaff: 3.0
  }
];
