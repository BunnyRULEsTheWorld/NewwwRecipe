import { ChevronLeft, ChevronRight } from 'lucide-react'
import type { IngredientFilter } from '../hooks/useIngredientFilter'

interface PaginationProps {
  filter: IngredientFilter
}

export function Pagination({ filter }: PaginationProps) {
  const { safePage, pageCount, previousPage, nextPage, visible, searching } = filter

  if (pageCount <= 1 && !searching) return null

  return (
    <div className="pager" aria-label="Ingredient pagination">
      <button
        type="button"
        className="pager__btn"
        aria-label="Previous page"
        disabled={safePage === 0}
        onClick={previousPage}
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
        onClick={nextPage}
      >
        <ChevronRight aria-hidden="true" />
      </button>
    </div>
  )
}
