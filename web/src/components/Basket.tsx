import { ShoppingBasket, X } from 'lucide-react'
import { SCENE, findIngredient, ingredientUrl } from '../data/ingredients'

interface BasketProps {
  selectedIds: string[]
  onRemove: (id: string) => void
  onClearAll: () => void
}

/**
 * Compact selected-ingredient summary.
 *
 * The empty state uses `basket_empty.png` at a restrained size. Selected items
 * show a thumbnail and full name, with a clear remove control.
 */
export function Basket({ selectedIds, onRemove, onClearAll }: BasketProps) {
  const items = selectedIds
    .map((id) => findIngredient(id))
    .filter((i): i is NonNullable<typeof i> => Boolean(i))

  const count = items.length

  return (
    <section className="basket-summary" aria-labelledby="basket-title">
      <div className="basket-summary__head">
        <ShoppingBasket aria-hidden="true" />
        <span id="basket-title">Your basket</span>
      </div>

      {count === 0 ? (
        <div className="basket-summary__empty">
          <figure className="basket-summary__figure">
            <img src={SCENE.basket} alt="" aria-hidden="true" />
          </figure>
          <div className="basket-summary__body">
            <p className="basket-summary__count" data-testid="basket-count">
              Nothing picked yet
            </p>
            <p className="basket-summary__hint">
              Choose what you have — pick at least two ingredients.
            </p>
          </div>
        </div>
      ) : (
        <div className="basket-summary__body">
          <p className="basket-summary__count" data-testid="basket-count">
            {count} ingredient{count === 1 ? '' : 's'} picked
          </p>
          <ul className="basket-summary__chips" aria-label="Selected ingredients">
            {items.map((item) => (
              <li key={item.id} className="basket-summary__chip">
                <img src={ingredientUrl(item)} alt="" aria-hidden="true" />
                <span className="basket-summary__chip-name">{item.displayName}</span>
                <button
                  type="button"
                  className="basket-summary__remove"
                  aria-label={`Remove ${item.displayName}`}
                  onClick={() => onRemove(item.id)}
                >
                  <X aria-hidden="true" />
                </button>
              </li>
            ))}
          </ul>
          <button
            type="button"
            className="btn btn--quiet btn--ghost"
            onClick={onClearAll}
          >
            Clear all
          </button>
        </div>
      )}
    </section>
  )
}
