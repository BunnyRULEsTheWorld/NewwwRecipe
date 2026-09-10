/**
 * Typed ingredient manifest — the single source of truth for the frontend.
 *
 * Every ingredient tile, thumbnail and result-page constellation derives its asset URL from this
 * manifest; there are no hand-written per-ingredient <img> tags.
 *
 * The 65 ids/filenames mirror the backend catalog `src/creative_recipe/web/ingredient_catalog.py`
 * (a test asserts the two never drift apart) and the PNGs shipped in the repository `ingredient/`
 * directory. Illustration binaries are never modified, renamed or recompressed.
 */

export type IngredientCategory =
  | 'vegetables'
  | 'fruits'
  | 'protein'
  | 'dairy-eggs'
  | 'grains'
  | 'pantry'

export interface Ingredient {
  /** Canonical snake_case id, also the PNG stem. */
  id: string
  /** English display name shown under every tile. */
  displayName: string
  /** File name inside `ingredient/`. */
  filename: string
  category: IngredientCategory
  /** Extra search terms (never shown as the primary label). */
  aliases?: string[]
}

export interface Category {
  id: IngredientCategory
  label: string
}

export const CATEGORIES: Category[] = [
  { id: 'vegetables', label: 'Vegetables' },
  { id: 'fruits', label: 'Fruits' },
  { id: 'protein', label: 'Protein' },
  { id: 'dairy-eggs', label: 'Dairy & Eggs' },
  { id: 'grains', label: 'Grains & Staples' },
  { id: 'pantry', label: 'Pantry & Flavor' },
]

/** Public URL prefix. Mirrors the FastAPI mount and the Vite dev middleware. */
export const INGREDIENT_URL_PREFIX = '/ingredients'

/** Public URL prefix for the eight scene illustrations. */
export const SCENE_URL_PREFIX = '/scene'

export const SCENE = {
  kitchenBackground: `${SCENE_URL_PREFIX}/kitchen_background_wide.png`,
  fridgeClosed: `${SCENE_URL_PREFIX}/fridge_closed.png`,
  fridgeAjar: `${SCENE_URL_PREFIX}/fridge_ajar.png`,
  fridgeOpen: `${SCENE_URL_PREFIX}/fridge_open_empty.png`,
  basket: `${SCENE_URL_PREFIX}/basket_empty.png`,
  mixingBowl: `${SCENE_URL_PREFIX}/magic_mixing_bowl.png`,
  recipeBook: `${SCENE_URL_PREFIX}/recipe_book_open_blank.png`,
  favoritesBox: `${SCENE_URL_PREFIX}/favorites_recipe_box_empty.png`,
} as const

const RAW: Array<[string, string, IngredientCategory, string[]?]> = [
  // Vegetables
  ['bell_pepper', 'Bell Pepper', 'vegetables', ['capsicum', 'sweet pepper']],
  ['bok_choy', 'Bok Choy', 'vegetables', ['pak choi']],
  ['broccoli', 'Broccoli', 'vegetables'],
  ['cabbage', 'Cabbage', 'vegetables'],
  ['carrot', 'Carrot', 'vegetables'],
  ['cauliflower', 'Cauliflower', 'vegetables'],
  ['celery', 'Celery', 'vegetables'],
  ['corn', 'Corn', 'vegetables', ['sweetcorn', 'maize']],
  ['cucumber', 'Cucumber', 'vegetables'],
  ['daikon_radish', 'Daikon Radish', 'vegetables', ['daikon', 'white radish']],
  ['eggplant', 'Eggplant', 'vegetables', ['aubergine']],
  ['garlic', 'Garlic', 'vegetables'],
  ['ginger', 'Ginger', 'vegetables'],
  ['green_beans', 'Green Beans', 'vegetables', ['string beans']],
  ['lettuce', 'Lettuce', 'vegetables'],
  ['lotus_root', 'Lotus Root', 'vegetables', ['renkon']],
  ['mushroom', 'Mushroom', 'vegetables'],
  ['napa_cabbage', 'Napa Cabbage', 'vegetables', ['chinese cabbage']],
  ['onion', 'Onion', 'vegetables'],
  ['potato', 'Potato', 'vegetables'],
  ['pumpkin', 'Pumpkin', 'vegetables', ['squash']],
  ['scallion', 'Scallion', 'vegetables', ['green onion', 'spring onion']],
  ['spinach', 'Spinach', 'vegetables'],
  ['sweet_potato', 'Sweet Potato', 'vegetables', ['yam']],
  ['tomato', 'Tomato', 'vegetables'],
  ['zucchini', 'Zucchini', 'vegetables', ['courgette']],
  // Fruits
  ['apple', 'Apple', 'fruits'],
  ['avocado', 'Avocado', 'fruits'],
  ['banana', 'Banana', 'fruits'],
  ['lemon', 'Lemon', 'fruits'],
  ['orange', 'Orange', 'fruits'],
  ['pear', 'Pear', 'fruits'],
  ['strawberry', 'Strawberry', 'fruits'],
  // Protein
  ['bacon', 'Bacon', 'protein'],
  ['beef', 'Beef', 'protein'],
  ['chicken', 'Chicken', 'protein'],
  ['chickpeas', 'Chickpeas', 'protein', ['garbanzo']],
  ['pork', 'Pork', 'protein'],
  ['salmon', 'Salmon', 'protein'],
  ['shrimp', 'Shrimp', 'protein', ['prawn']],
  ['squid', 'Squid', 'protein', ['calamari']],
  ['tofu', 'Tofu', 'protein', ['bean curd']],
  ['white_fish', 'White Fish', 'protein', ['cod', 'tilapia']],
  // Dairy & Eggs
  ['butter', 'Butter', 'dairy-eggs'],
  ['cheese', 'Cheese', 'dairy-eggs'],
  ['cream', 'Cream', 'dairy-eggs'],
  ['egg', 'Egg', 'dairy-eggs', ['eggs']],
  ['milk', 'Milk', 'dairy-eggs'],
  ['yogurt', 'Yogurt', 'dairy-eggs', ['yoghurt']],
  // Grains & Staples
  ['bread', 'Bread', 'grains'],
  ['flour', 'Flour', 'grains'],
  ['noodles', 'Noodles', 'grains'],
  ['oats', 'Oats', 'grains'],
  ['pasta', 'Pasta', 'grains'],
  ['rice', 'Rice', 'grains'],
  ['tortilla', 'Tortilla', 'grains', ['wrap']],
  // Pantry & Flavor
  ['chili_pepper', 'Chili Pepper', 'pantry', ['chilli', 'hot pepper']],
  ['cilantro', 'Cilantro', 'pantry', ['coriander leaf']],
  ['coffee', 'Coffee', 'pantry', ['espresso']],
  ['curry_paste', 'Curry Paste', 'pantry'],
  ['dark_chocolate', 'Dark Chocolate', 'pantry', ['chocolate']],
  ['honey', 'Honey', 'pantry'],
  ['kimchi', 'Kimchi', 'pantry'],
  ['miso', 'Miso', 'pantry'],
  ['soy_sauce', 'Soy Sauce', 'pantry', ['shoyu']],
]

export const INGREDIENTS: Ingredient[] = RAW.map(([id, displayName, category, aliases]) => ({
  id,
  displayName,
  filename: `${id}.png`,
  category,
  aliases: aliases ?? [],
}))

/** Number of ingredients the manifest is expected to expose (asserted by tests). */
export const EXPECTED_INGREDIENT_COUNT = 65

export function ingredientUrl(ingredient: Pick<Ingredient, 'filename'>): string {
  return `${INGREDIENT_URL_PREFIX}/${ingredient.filename}`
}

export function ingredientsByCategory(category: IngredientCategory): Ingredient[] {
  return INGREDIENTS.filter((i) => i.category === category)
}

export function findIngredient(id: string): Ingredient | undefined {
  return INGREDIENTS.find((i) => i.id === id)
}

/** Case-insensitive match on display name, id and aliases. */
export function matchesQuery(ingredient: Ingredient, query: string): boolean {
  const q = query.trim().toLowerCase()
  if (!q) return true
  if (ingredient.displayName.toLowerCase().includes(q)) return true
  if (ingredient.id.toLowerCase().includes(q)) return true
  return (ingredient.aliases ?? []).some((a) => a.toLowerCase().includes(q))
}
