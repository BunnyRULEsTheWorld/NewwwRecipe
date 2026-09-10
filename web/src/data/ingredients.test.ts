import { describe, expect, it } from 'vitest'
import {
  CATEGORIES,
  EXPECTED_INGREDIENT_COUNT,
  INGREDIENTS,
  ingredientsByCategory,
  ingredientUrl,
  matchesQuery,
} from './ingredients'

describe('ingredient manifest', () => {
  it('exposes exactly 65 unique ingredients', () => {
    expect(INGREDIENTS).toHaveLength(EXPECTED_INGREDIENT_COUNT)
    const ids = INGREDIENTS.map((i) => i.id)
    expect(new Set(ids).size).toBe(65)
    const files = INGREDIENTS.map((i) => i.filename)
    expect(new Set(files).size).toBe(65)
  })

  it('uses snake_case ids matching the PNG filenames', () => {
    for (const item of INGREDIENTS) {
      expect(item.id).toMatch(/^[a-z][a-z_]*$/)
      expect(item.filename).toBe(`${item.id}.png`)
      expect(item.displayName.trim()).not.toBe('')
    }
  })

  it('places every ingredient in a known category', () => {
    const known = new Set(CATEGORIES.map((c) => c.id))
    for (const item of INGREDIENTS) {
      expect(known.has(item.category)).toBe(true)
    }
    const total = CATEGORIES.reduce((sum, c) => sum + ingredientsByCategory(c.id).length, 0)
    expect(total).toBe(65)
  })

  it('derives asset urls from the manifest', () => {
    expect(ingredientUrl({ filename: 'coffee.png' })).toBe('/ingredients/coffee.png')
  })

  it('searches by display name, id and alias', () => {
    const courgette = INGREDIENTS.find((i) => i.id === 'zucchini')!
    expect(matchesQuery(courgette, 'courgette')).toBe(true)
    expect(matchesQuery(courgette, 'zucch')).toBe(true)
    expect(matchesQuery(courgette, 'ZUCCHINI')).toBe(true)
    expect(matchesQuery(courgette, 'potato')).toBe(false)
  })
})
