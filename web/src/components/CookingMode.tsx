import { useMemo, useState } from 'react'
import { ArrowLeft, ArrowRight, Check, PartyPopper, X } from 'lucide-react'
import { SCENE } from '../data/ingredients'
import type { RecipePayload } from '../types'

interface CookingModeProps {
  recipe: RecipePayload
  onExit: () => void
}

/**
 * Text-only cooking mode. One step at a time, no photos, no timers (the backend does not provide
 * reliable timing). Ingredient quantities are shown only when the step actually mentions them.
 */
export function CookingMode({ recipe, onExit }: CookingModeProps) {
  const [index, setIndex] = useState(0)
  const steps = recipe.steps
  const total = steps.length
  const [done, setDone] = useState(false)

  const current = steps[Math.min(index, total - 1)] ?? ''

  const mentioned = useMemo(() => {
    if (!current) return []
    const haystack = current.toLowerCase()
    const pool = [...recipe.ingredients, ...recipe.seasonings]
    return pool.filter((ing) => {
      const name = ing.name.toLowerCase().trim()
      return name.length > 2 && haystack.includes(name)
    })
  }, [current, recipe.ingredients, recipe.seasonings])

  const progress = total === 0 ? 0 : ((Math.min(index, total - 1) + 1) / total) * 100

  if (done || total === 0) {
    return (
      <section className="cooking" aria-labelledby="cooking-done">
        <div className="cooking__inner">
          <div className="cooking__body cooking__done">
            <img src={SCENE.recipeBook} alt="An open, blank recipe book" />
            <h1 className="cooking__title" id="cooking-done">
              Nicely done.
            </h1>
            <p className="prose" style={{ marginTop: 10 }}>
              That was every step. Taste it, adjust the seasoning, and tell us what you would change.
            </p>
            <div className="cooking__nav" style={{ justifyContent: 'center' }}>
              <button type="button" className="btn btn--primary" onClick={onExit}>
                Back to the recipe
              </button>
            </div>
          </div>
        </div>
      </section>
    )
  }

  return (
    <section className="cooking" aria-labelledby="cooking-title">
      <div className="cooking__inner">
        <div className="cooking__head">
          <h1 className="cooking__title" id="cooking-title">
            {recipe.name}
          </h1>
          <p className="cooking__counter" data-testid="step-counter">
            Step {index + 1} of {total}
          </p>
          <button type="button" className="btn btn--quiet btn--ghost" onClick={onExit}>
            <X className="btn__icon" aria-hidden="true" />
            Exit cooking mode
          </button>
        </div>

        <div
          className="progress"
          role="progressbar"
          aria-valuemin={0}
          aria-valuemax={total}
          aria-valuenow={index + 1}
          aria-label="Cooking progress"
        >
          <div className="progress__fill" style={{ width: `${progress}%` }} />
        </div>

        <div className="cooking__body">
          <p className="cooking__stepnum">Step {index + 1}</p>
          <p className="cooking__step" data-testid="cooking-step">
            {current}
          </p>

          {mentioned.length > 0 && (
            <div className="cooking__ings">
              {mentioned.map((ing, i) => (
                <span className="meta-pill" key={`${ing.name}-${i}`}>
                  {ing.name}
                  {ing.quantity ? ` · ${ing.quantity}` : ''}
                </span>
              ))}
            </div>
          )}
        </div>

        <div className="cooking__nav">
          <button
            type="button"
            className="btn"
            onClick={() => setIndex((i) => Math.max(0, i - 1))}
            disabled={index === 0}
          >
            <ArrowLeft className="btn__icon" aria-hidden="true" />
            Back
          </button>
          {index < total - 1 ? (
            <button
              type="button"
              className="btn btn--primary"
              onClick={() => setIndex((i) => Math.min(total - 1, i + 1))}
            >
              Next
              <ArrowRight className="btn__icon" aria-hidden="true" />
            </button>
          ) : (
            <button type="button" className="btn btn--primary" onClick={() => setDone(true)}>
              <Check className="btn__icon" aria-hidden="true" />
              Finish
            </button>
          )}
        </div>

        {index === total - 1 && (
          <p className="select__note" style={{ textAlign: 'center', marginTop: 10 }}>
            <PartyPopper
              aria-hidden="true"
              style={{ width: 14, height: 14, verticalAlign: '-2px', marginRight: 4 }}
            />
            Last step — then you are done.
          </p>
        )}
      </div>
    </section>
  )
}
