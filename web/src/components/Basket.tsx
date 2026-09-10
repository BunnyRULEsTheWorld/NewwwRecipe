import { ShoppingBasket, X } from 'lucide-react'
import { SCENE, findIngredient, ingredientUrl } from '../data/ingredients'

interface BasketProps {
  selectedIds: string[]
  onRemove: (id: string) => void
  onClearAll: () => void
}

/** Selected-ingredient basket anchored next to `basket_empty.png`. */
export function Basket({ selectedIds, onRemove, onClearAll }: BasketProps) {
  const items = selectedIds
    .map((id) => findIngredient(id))
    .filter((i): i is NonNullable<typeof i> => Boolean(i))

  const count = items.length

  return (
    <section className="card" aria-labelledby="basket-title">
      <h2 className="card__title" id="basket-title">
        <ShoppingBasket aria-hidden="true" />
        Your basket
      </h2>
      <div className="basket">
        <figure className="basket__figure">
          <img src={SCENE.basket} alt="An empty market basket" />
        </figure>
        <div className="basket__body">
          <p className="basket__count" data-testid="basket-count">
            {count === 0
              ? 'Nothing picked yet'
              : `${count} ingredient${count === 1 ? '' : 's'} picked`}
          </p>
          {count === 0 ? (
            <p className="basket__empty">Tap what you have — pick at least two to cook.</p>
          ) : (
            <ul className="basket__chips">
              {items.map((item) => (
                <li key={item.id}>
                  <span className="chip">
                    <img src={ingredientUrl(item)} alt="" aria-hidden="true" />
                    {item.displayName}
                    <button
                      type="button"
                      className="chip__remove"
                      aria-label={`Remove ${item.displayName}`}
                      onClick={() => onRemove(item.id)}
                    >
                      <X aria-hidden="true" />
                    </button>
                  </span>
                </li>
              ))}
            </ul>
          )}
          {count > 0 && (
            <button type="button" className="btn btn--quiet btn--ghost" onClick={onClearAll}>
              Clear all
            </button>
          )}
        </div>
      </div>
    </section>
  )
}
