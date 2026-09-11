import { useCallback, useEffect, useMemo, useState } from 'react'
import {
  CATEGORIES,
  INGREDIENTS,
  matchesQuery,
  type Ingredient,
  type IngredientCategory,
} from '../data/ingredients'

/** 3 ingredients across × 4 shelf bands = 12 ingredients per page. */
export const PAGE_SIZE = 12

export interface IngredientFilter {
  /** Currently active category (ignored while searching). */
  category: IngredientCategory
  /** Search query applied across all 65 ingredient names, ids and aliases. */
  query: string
  /** Whether a non-empty query is active. */
  searching: boolean
  /** All ingredients matching the current filter. */
  visible: Ingredient[]
  /** Total number of pages available. */
  pageCount: number
  /** Zero-based current page, guaranteed to be within range. */
  safePage: number
  /** Ingredients shown on the current page. */
  items: Ingredient[]
  /** Switch category and clear the search query. */
  setCategory: (category: IngredientCategory) => void
  /** Update the search query (resets pagination automatically). */
  setQuery: (query: string) => void
  /** Move to a specific page. */
  setPage: (page: number) => void
  /** Move one page backward. */
  previousPage: () => void
  /** Move one page forward. */
  nextPage: () => void
  /** Count of ingredients in each category. */
  categoryCounts: Map<IngredientCategory, number>
}

/**
 * Shared filter state for the ingredient-selection page.
 *
 * Search is global across the whole catalog; selecting a category clears the
 * query. Pagination resets whenever the query or category changes.
 */
export function useIngredientFilter(): IngredientFilter {
  const [category, setCategoryState] = useState<IngredientCategory>('vegetables')
  const [query, setQueryState] = useState('')
  const [page, setPageState] = useState(0)

  const searching = query.trim().length > 0

  const visible = useMemo(() => {
    if (searching) return INGREDIENTS.filter((i) => matchesQuery(i, query))
    return INGREDIENTS.filter((i) => i.category === category)
  }, [category, query, searching])

  const pageCount = Math.max(1, Math.ceil(visible.length / PAGE_SIZE))
  const safePage = Math.min(page, pageCount - 1)
  const items = useMemo(
    () => visible.slice(safePage * PAGE_SIZE, safePage * PAGE_SIZE + PAGE_SIZE),
    [safePage, visible],
  )

  // Reset to page 1 whenever the result set changes.
  useEffect(() => {
    setPageState(0)
  }, [category, query])

  const setCategory = useCallback((next: IngredientCategory) => {
    setCategoryState(next)
    setQueryState('')
  }, [])

  const setQuery = useCallback((next: string) => {
    setQueryState(next)
  }, [])

  const setPage = useCallback((next: number) => {
    setPageState(next)
  }, [])

  const previousPage = useCallback(() => {
    setPageState((p) => Math.max(0, p - 1))
  }, [])

  const nextPage = useCallback(() => {
    setPageState((p) => p + 1)
  }, [])

  const categoryCounts = useMemo(() => {
    const map = new Map<IngredientCategory, number>()
    for (const c of CATEGORIES) {
      map.set(c.id, INGREDIENTS.filter((i) => i.category === c.id).length)
    }
    return map
  }, [])

  return {
    category,
    query,
    searching,
    visible,
    pageCount,
    safePage,
    items,
    setCategory,
    setQuery,
    setPage,
    previousPage,
    nextPage,
    categoryCounts,
  }
}
