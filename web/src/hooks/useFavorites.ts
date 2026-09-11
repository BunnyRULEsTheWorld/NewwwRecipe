import { useCallback, useEffect, useMemo, useState } from 'react'
import type { GenerateResponse, Preferences, SavedRecipe } from '../types'

const STORAGE_KEY = 'newwwrecipe.favorites.v1'

/** Shape guard: localStorage can hold anything (old versions, manual edits, other apps). */
function isSavedRecipe(value: unknown): value is SavedRecipe {
  if (!value || typeof value !== 'object') return false
  const v = value as Partial<SavedRecipe>
  if (typeof v.id !== 'string' || !v.id) return false
  if (typeof v.title !== 'string') return false
  if (!v.response || typeof v.response !== 'object') return false
  if (!v.response.recipe || typeof v.response.recipe.name !== 'string') return false
  if (!Array.isArray(v.response.recipe.steps)) return false
  return true
}

function readStorage(): SavedRecipe[] {
  if (typeof window === 'undefined' || !window.localStorage) return []
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY)
    if (!raw) return []
    const parsed: unknown = JSON.parse(raw)
    if (!Array.isArray(parsed)) return []
    // Drop anything that does not match the current shape instead of crashing the app.
    return parsed.filter(isSavedRecipe)
  } catch {
    return []
  }
}

function writeStorage(items: SavedRecipe[]): void {
  if (typeof window === 'undefined' || !window.localStorage) return
  try {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(items))
  } catch {
    // Quota / private-mode failures must not break the UI.
  }
}

/** Stable fingerprint so the same recipe is not saved twice by accident. */
export function favoriteKey(
  title: string,
  ingredientIds: string[],
  preferences: Preferences,
): string {
  return [
    title.trim().toLowerCase(),
    [...ingredientIds].sort().join('+'),
    preferences.cuisine,
    preferences.flavor,
    preferences.time,
    preferences.allergies.trim().toLowerCase(),
    preferences.craving.trim().toLowerCase(),
  ].join('|')
}

export interface UseFavorites {
  favorites: SavedRecipe[]
  isSaved: (key: string) => boolean
  save: (input: {
    response: GenerateResponse
    ingredientIds: string[]
    preferences: Preferences
  }) => SavedRecipe | null
  remove: (id: string) => void
  clearAll: () => void
}

export function useFavorites(): UseFavorites {
  const [favorites, setFavorites] = useState<SavedRecipe[]>(() => readStorage())

  useEffect(() => {
    // Re-read on mount only (guards against SSR-ish/empty first render).
    setFavorites(readStorage())
  }, [])

  const persist = useCallback((next: SavedRecipe[]) => {
    setFavorites(next)
    writeStorage(next)
  }, [])

  const isSaved = useCallback(
    (key: string) => favorites.some((f) => f.id === key),
    [favorites],
  )

  const save = useCallback<UseFavorites['save']>(
    ({ response, ingredientIds, preferences }) => {
      const title = response.recipe.name
      const id = favoriteKey(title, ingredientIds, preferences)
      if (favorites.some((f) => f.id === id)) return null
      const entry: SavedRecipe = {
        id,
        savedAt: new Date().toISOString(),
        title,
        concept: response.concept?.creative_angle ?? null,
        ingredientIds: [...ingredientIds],
        preferences,
        response,
      }
      persist([entry, ...favorites])
      return entry
    },
    [favorites, persist],
  )

  const remove = useCallback(
    (id: string) => persist(favorites.filter((f) => f.id !== id)),
    [favorites, persist],
  )

  const clearAll = useCallback(() => persist([]), [persist])

  return useMemo(
    () => ({ favorites, isSaved, save, remove, clearAll }),
    [favorites, isSaved, save, remove, clearAll],
  )
}
