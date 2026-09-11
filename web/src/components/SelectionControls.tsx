import { Search, X, ChevronRight } from 'lucide-react'
import { CATEGORIES, type IngredientCategory } from '../data/ingredients'
import type { IngredientFilter } from '../hooks/useIngredientFilter'
import { Basket } from './Basket'

interface SelectionControlsProps {
  filter: IngredientFilter
  selectedIds: string[]
  onRemove: (id: string) => void
  onClearAll: () => void
  onContinue: () => void
  onBack?: () => void
  continueDisabled: boolean
}

export function SelectionControls({
  filter,
  selectedIds,
  onRemove,
  onClearAll,
  onContinue,
  onBack,
  continueDisabled,
}: SelectionControlsProps) {
  return (
    <div className="select__panel" data-testid="selection-controls">
      <div className="select__header">
        <h1 className="select__title">What do we have?</h1>
        <p className="select__lede">
          Pick what is in your kitchen — at least two ingredients.
        </p>
      </div>

      <div className="search search--wide">
        <Search aria-hidden="true" />
        <input
          type="search"
          value={filter.query}
          placeholder="Search all 65 ingredients"
          aria-label="Search ingredients by name"
          onChange={(e) => filter.setQuery(e.target.value)}
        />
        {filter.query && (
          <button
            type="button"
            className="search__clear"
            aria-label="Clear search"
            onClick={() => filter.setQuery('')}
          >
            <X aria-hidden="true" />
          </button>
        )}
      </div>

      <div className="tabs" role="group" aria-label="Ingredient categories">
        {CATEGORIES.map((c) => (
          <button
            key={c.id}
            type="button"
            className="tab"
            aria-pressed={!filter.searching && filter.category === c.id}
            onClick={() => filter.setCategory(c.id as IngredientCategory)}
          >
            {c.label}
            <span className="tab__count">{filter.categoryCounts.get(c.id) ?? 0}</span>
          </button>
        ))}
      </div>

      <Basket selectedIds={selectedIds} onRemove={onRemove} onClearAll={onClearAll} />

      <div className="select__actions">
        <button
          type="button"
          className="btn btn--primary btn--block"
          disabled={continueDisabled}
          onClick={onContinue}
          aria-describedby={continueDisabled ? 'continue-hint' : undefined}
          data-testid="continue-button"
        >
          Continue
          <ChevronRight className="btn__icon" aria-hidden="true" />
        </button>
        {continueDisabled && (
          <p id="continue-hint" className="select__hint" data-testid="continue-hint">
            Choose at least two ingredients to continue.
          </p>
        )}
      </div>

      {onBack && (
        <button type="button" className="btn btn--ghost btn--quiet" onClick={onBack}>
          Back
        </button>
      )}
    </div>
  )
}
