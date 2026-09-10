import { useEffect, useMemo, useRef, useState } from 'react'
import { ChevronLeft, ChevronRight, Search, X } from 'lucide-react'
import {
  CATEGORIES,
  INGREDIENTS,
  ingredientUrl,
  matchesQuery,
  type Ingredient,
  type IngredientCategory,
} from '../data/ingredients'

/** 3 columns x 4 shelf bands = 12 ingredients per page. */
export const PAGE_SIZE = 12

interface IngredientShelfProps {
  selectedIds: string[]
  onToggle: (id: string) => void
}

export function IngredientShelf({ selectedIds, onToggle }: IngredientShelfProps) {
  const [category, setCategory] = useState<IngredientCategory>('vegetables')
  const [query, setQuery] = useState('')
  const [page, setPage] = useState(0)
  const gridRef = useRef<HTMLDivElement>(null)

  const selected = useMemo(() => new Set(selectedIds), [selectedIds])

  // Search runs across the whole pantry; picking a tab clears the query.
  const searching = query.trim().length > 0
  const visible = useMemo(() => {
    if (searching) return INGREDIENTS.filter((i) => matchesQuery(i, query))
    return INGREDIENTS.filter((i) => i.category === category)
  }, [category, query, searching])

  const pageCount = Math.max(1, Math.ceil(visible.length / PAGE_SIZE))
  const safePage = Math.min(page, pageCount - 1)
  const items = visible.slice(safePage * PAGE_SIZE, safePage * PAGE_SIZE + PAGE_SIZE)

  useEffect(() => {
    // Reset pagination whenever the result set changes.
    setPage(0)
  }, [category, query])

  const counts = useMemo(() => {
    const map = new Map<IngredientCategory, number>()
    for (const c of CATEGORIES) {
      map.set(c.id, INGREDIENTS.filter((i) => i.category === c.id).length)
    }
    return map
  }, [])

  /** Arrow-key roving focus across the shelf grid. */
  const onGridKeyDown = (event: React.KeyboardEvent<HTMLDivElement>) => {
    const keys = ['ArrowRight', 'ArrowLeft', 'ArrowDown', 'ArrowUp']
    if (!keys.includes(event.key)) return
    const grid = gridRef.current
    if (!grid) return
    const tiles = Array.from(grid.querySelectorAll<HTMLButtonElement>('button.tile'))
    if (tiles.length === 0) return
    const current = tiles.indexOf(document.activeElement as HTMLButtonElement)
    if (current < 0) return
    event.preventDefault()
    const columns = 3
    let next = current
    if (event.key === 'ArrowRight') next = Math.min(tiles.length - 1, current + 1)
    if (event.key === 'ArrowLeft') next = Math.max(0, current - 1)
    if (event.key === 'ArrowDown') next = Math.min(tiles.length - 1, current + columns)
    if (event.key === 'ArrowUp') next = Math.max(0, current - columns)
    tiles[next]?.focus()
  }

  return (
    <div className="shelf">
      <div className="shelf__toolbar">
        <div className="tabs" role="tablist" aria-label="Ingredient categories">
          {CATEGORIES.map((c) => (
            <button
              key={c.id}
              type="button"
              role="tab"
              className="tab"
              aria-selected={!searching && category === c.id}
              onClick={() => {
                setCategory(c.id)
                setQuery('')
              }}
            >
              {c.label}
              <span className="tab__count">{counts.get(c.id) ?? 0}</span>
            </button>
          ))}
        </div>
        <div className="search">
          <Search aria-hidden="true" />
          <input
            type="search"
            value={query}
            placeholder="Search ingredients"
            aria-label="Search ingredients by name"
            onChange={(e) => setQuery(e.target.value)}
          />
        </div>
        {searching && (
          <button type="button" className="btn btn--quiet btn--ghost" onClick={() => setQuery('')}>
            <X className="btn__icon" aria-hidden="true" />
            Clear
          </button>
        )}
      </div>

      <div className="shelf__grid" ref={gridRef} onKeyDown={onGridKeyDown}>
        {items.length === 0 ? (
          <p className="shelf__empty">
            Nothing matches “{query}”. Try another word, or pick a category above.
          </p>
        ) : (
          items.map((item) => (
            <IngredientTile
              key={item.id}
              ingredient={item}
              selected={selected.has(item.id)}
              onToggle={onToggle}
            />
          ))
        )}
      </div>

      <div className="pager">
        <button
          type="button"
          className="pager__btn"
          aria-label="Previous page"
          disabled={safePage === 0}
          onClick={() => setPage((p) => Math.max(0, Math.min(p, pageCount - 1) - 1))}
        >
          <ChevronLeft aria-hidden="true" />
        </button>
        <span aria-live="polite">
          Page {safePage + 1} of {pageCount}
          {searching ? ` · ${visible.length} match${visible.length === 1 ? '' : 'es'}` : ''}
        </span>
        <button
          type="button"
          className="pager__btn"
          aria-label="Next page"
          disabled={safePage >= pageCount - 1}
          onClick={() => setPage((p) => Math.min(pageCount - 1, Math.min(p, pageCount - 1) + 1))}
        >
          <ChevronRight aria-hidden="true" />
        </button>
      </div>
    </div>
  )
}

interface TileProps {
  ingredient: Ingredient
  selected: boolean
  onToggle: (id: string) => void
}

function IngredientTile({ ingredient, selected, onToggle }: TileProps) {
  return (
    <button
      type="button"
      className="tile"
      data-testid={`tile-${ingredient.id}`}
      aria-pressed={selected}
      onClick={() => onToggle(ingredient.id)}
    >
      <img
        className="tile__img"
        src={ingredientUrl(ingredient)}
        alt={`${ingredient.displayName} illustration`}
        loading="lazy"
        draggable={false}
      />
      <span className="tile__name">{ingredient.displayName}</span>
      {selected && (
        <span className="tile__check" aria-hidden="true">
          <CheckIcon />
        </span>
      )}
      <span className="sr-only">
        {selected ? `${ingredient.displayName}, selected` : ingredient.displayName}
      </span>
    </button>
  )
}

function CheckIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3.5" aria-hidden="true">
      <path d="M20 6 9 17l-5-5" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  )
}
