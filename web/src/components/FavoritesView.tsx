import { useState } from 'react'
import { ArrowLeft, BookOpen, Trash2 } from 'lucide-react'
import { SCENE, findIngredient, ingredientUrl } from '../data/ingredients'
import type { SavedRecipe } from '../types'
import { ConfirmDialog } from './ConfirmDialog'

interface FavoritesViewProps {
  favorites: SavedRecipe[]
  onOpen: (favorite: SavedRecipe) => void
  onRemove: (id: string) => void
  onBack: () => void
}

const EMPTY_COPY = 'No saved recipes yet.\nYour future favorites will live here.'

export function FavoritesView({ favorites, onOpen, onRemove, onBack }: FavoritesViewProps) {
  const [pending, setPending] = useState<SavedRecipe | null>(null)

  return (
    <section className="favorites" aria-labelledby="favorites-title">
      <div className="favorites__inner">
        <div className="result__actions">
          <button type="button" className="btn btn--ghost" onClick={onBack}>
            <ArrowLeft className="btn__icon" aria-hidden="true" />
            Back
          </button>
        </div>

        <h1 className="cooking__title" id="favorites-title" style={{ marginBottom: 16 }}>
          Saved recipes
        </h1>

        {favorites.length === 0 ? (
          <div className="favorites__empty" data-testid="favorites-empty">
            <img src={SCENE.favoritesBox} alt="An empty recipe box" />
            <p>{EMPTY_COPY}</p>
          </div>
        ) : (
          <ul className="fav-grid">
            {favorites.map((fav) => (
              <li className="fav-card" key={fav.id}>
                <h2 className="fav-card__title">{fav.title}</h2>
                {fav.concept && <p className="fav-card__meta">{fav.concept}</p>}
                <div className="fav-card__thumbs">
                  {fav.ingredientIds
                    .map((id) => findIngredient(id))
                    .filter((i): i is NonNullable<typeof i> => Boolean(i))
                    .map((item) => (
                      <img
                        key={item.id}
                        src={ingredientUrl(item)}
                        alt={`${item.displayName} illustration`}
                      />
                    ))}
                </div>
                <p className="fav-card__meta">
                  Saved {new Date(fav.savedAt).toLocaleDateString()}
                </p>
                <div className="fav-card__actions">
                  <button type="button" className="btn btn--quiet" onClick={() => onOpen(fav)}>
                    <BookOpen className="btn__icon" aria-hidden="true" />
                    Open
                  </button>
                  <button
                    type="button"
                    className="btn btn--quiet btn--ghost"
                    aria-label={`Remove ${fav.title}`}
                    onClick={() => setPending(fav)}
                  >
                    <Trash2 className="btn__icon" aria-hidden="true" />
                    Remove
                  </button>
                </div>
              </li>
            ))}
          </ul>
        )}
      </div>

      <ConfirmDialog
        open={pending !== null}
        title="Remove this recipe?"
        message={pending ? `“${pending.title}” will be removed from your saved recipes.` : ''}
        confirmLabel="Remove"
        cancelLabel="Keep it"
        onConfirm={() => {
          if (pending) onRemove(pending.id)
          setPending(null)
        }}
        onCancel={() => setPending(null)}
      />
    </section>
  )
}
