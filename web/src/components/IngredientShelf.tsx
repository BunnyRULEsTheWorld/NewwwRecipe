import { useEffect, useMemo, useRef } from 'react'
import { ingredientUrl, type Ingredient } from '../data/ingredients'

interface IngredientShelfProps {
  items: Ingredient[]
  selectedIds: string[]
  onToggle: (id: string) => void
}

/**
 * Ingredient grid rendered inside the open refrigerator.
 *
 * The parent Fridge component provides a percentage-based overlay that matches
 * the illustrated cavity, so ingredients appear to sit on the four drawn
 * shelves. The grid is 3 columns × 4 rows = 12 items per page.
 */
export function IngredientShelf({ items, selectedIds, onToggle }: IngredientShelfProps) {
  const selected = useMemo(() => new Set(selectedIds), [selectedIds])
  const gridRef = useRef<HTMLDivElement>(null)

  // When the page changes, move focus to the first tile so keyboard users stay
  // oriented without losing their place in the document.
  useEffect(() => {
    const grid = gridRef.current
    if (!grid) return
    const first = grid.querySelector<HTMLButtonElement>('button.shelf__tile')
    first?.focus({ preventScroll: true })
  }, [items])

  /** Arrow-key roving focus across the 3×4 shelf grid. */
  const onGridKeyDown = (event: React.KeyboardEvent<HTMLDivElement>) => {
    const keys = ['ArrowRight', 'ArrowLeft', 'ArrowDown', 'ArrowUp']
    if (!keys.includes(event.key)) return
    const grid = gridRef.current
    if (!grid) return
    const tiles = Array.from(grid.querySelectorAll<HTMLButtonElement>('button.shelf__tile'))
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

  const rows = useMemo(() => {
    const out: Ingredient[][] = [[], [], [], []]
    for (let i = 0; i < items.length; i++) {
      out[Math.floor(i / 3)].push(items[i])
    }
    return out
  }, [items])

  return (
    <div className="shelf" ref={gridRef} onKeyDown={onGridKeyDown}>
      {items.length === 0 ? (
        <p className="shelf__empty">Nothing matches your search.</p>
      ) : (
        rows.map((row, rowIndex) => (
          <div
            key={rowIndex}
            className="shelf__row"
            role="group"
            aria-label={`Shelf ${rowIndex + 1}`}
            data-shelf={rowIndex + 1}
            data-testid={`shelf-row-${rowIndex + 1}`}
          >
            {row.map((item) => (
              <IngredientTile
                key={item.id}
                ingredient={item}
                selected={selected.has(item.id)}
                onToggle={onToggle}
              />
            ))}
          </div>
        ))
      )}
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
      className={`shelf__tile${selected ? ' is-selected' : ''}`}
      data-testid={`tile-${ingredient.id}`}
      aria-pressed={selected}
      onClick={() => onToggle(ingredient.id)}
    >
      <span className="shelf__tile-art">
        <img
          src={ingredientUrl(ingredient)}
          alt={`${ingredient.displayName} illustration`}
          loading="lazy"
          draggable={false}
        />
        {selected && (
          <span className="shelf__tile-check" aria-hidden="true">
            <CheckIcon />
          </span>
        )}
      </span>
      <span className="shelf__tile-name">{ingredient.displayName}</span>
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
