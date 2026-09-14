import {
  ArrowLeft,
  BookOpen,
  ChefHat,
  Clock,
  Heart,
  RefreshCw,
  Sparkles,
  TriangleAlert,
  Users,
} from 'lucide-react'
import { SCENE, findIngredient, ingredientUrl } from '../data/ingredients'
import type { GenerateResponse, Preferences } from '../types'
import { CieScorePanel } from './CieScorePanel'
import { TraceTimeline } from './TraceTimeline'

interface RecipeResultProps {
  response: GenerateResponse
  ingredientIds: string[]
  preferences: Preferences
  saved: boolean
  onSave: () => void
  onTryAnother: () => void
  onStartCooking: () => void
  onBackToFridge: () => void
}

const TIME_LABEL: Record<Preferences['time'], string> = {
  any: 'Flexible',
  'under-20': 'Under 20 min',
  'under-40': 'Under 40 min',
  weekend: 'Weekend project',
}

const CUISINE_LABEL: Record<Preferences['cuisine'], string> = {
  'surprise-me': 'Surprise me',
  chinese: 'Chinese-inspired',
  western: 'Western-inspired',
  fusion: 'East–West Fusion',
}

const FLAVOR_LABEL: Record<Preferences['flavor'], string> = {
  balanced: 'Balanced',
  savory: 'Savory',
  spicy: 'Spicy',
  fresh: 'Fresh',
  rich: 'Rich',
}

export function RecipeResult({
  response,
  ingredientIds,
  preferences,
  saved,
  onSave,
  onTryAnother,
  onStartCooking,
  onBackToFridge,
}: RecipeResultProps) {
  const { recipe, concept, trace, cie } = response

  const thumbnails = ingredientIds
    .map((id) => findIngredient(id))
    .filter((i): i is NonNullable<typeof i> => Boolean(i))

  return (
    <section className="result" aria-labelledby="result-title">
      <div className="result__inner">
        <div>
          <div className="result__actions">
            <button type="button" className="btn" onClick={onTryAnother}>
              <RefreshCw className="btn__icon" aria-hidden="true" />
              Try Another
            </button>
            <button
              type="button"
              className="btn btn--coral"
              onClick={onSave}
              disabled={saved}
              data-testid="save-recipe"
            >
              <Heart className="btn__icon" aria-hidden="true" />
              {saved ? 'Saved' : 'Save'}
            </button>
            <button type="button" className="btn btn--primary" onClick={onStartCooking}>
              <ChefHat className="btn__icon" aria-hidden="true" />
              Start Cooking
            </button>
            <button type="button" className="btn btn--ghost" onClick={onBackToFridge}>
              <ArrowLeft className="btn__icon" aria-hidden="true" />
              Back to Fridge
            </button>
          </div>

          <article className="recipe-card">
            <img className="recipe-card__decor" src={SCENE.recipeBook} alt="" aria-hidden="true" />

            <h1 className="recipe-card__title" id="result-title">
              {recipe.name}
            </h1>
            <p className="recipe-card__concept">
              {concept?.creative_angle || recipe.creative_explanation}
            </p>

            <div className="recipe-meta">
              {recipe.servings && (
                <span className="meta-pill">
                  <Users aria-hidden="true" />
                  {recipe.servings}
                </span>
              )}
              {recipe.estimated_time && (
                <span className="meta-pill">
                  <Clock aria-hidden="true" />
                  {recipe.estimated_time}
                </span>
              )}
              {recipe.difficulty && (
                <span className="meta-pill">
                  <ChefHat aria-hidden="true" />
                  {recipe.difficulty}
                </span>
              )}
              <span className="meta-pill">
                <Clock aria-hidden="true" />
                Cooking time: {TIME_LABEL[preferences.time]}
              </span>
              <span className="meta-pill">
                <Sparkles aria-hidden="true" />
                {CUISINE_LABEL[preferences.cuisine]} · {FLAVOR_LABEL[preferences.flavor]}
              </span>
            </div>

            {thumbnails.length > 0 && (
              <div className="constellation-wrap">
                <h2 className="section__title constellation__title" data-testid="starting-ingredients">
                  YOUR STARTING INGREDIENTS
                </h2>
                <div className="constellation" aria-label="Ingredients you picked">
                  {thumbnails.map((item) => (
                    <img
                      key={item.id}
                      className="constellation__item"
                      src={ingredientUrl(item)}
                      alt={`${item.displayName} illustration`}
                    />
                  ))}
                </div>
              </div>
            )}

            <div className="section">
              <h2 className="section__title">Ingredients</h2>
              <ul className="ing-list">
                {recipe.ingredients.map((ing, i) => (
                  <li className="ing-item" key={`${ing.name}-${i}`}>
                    <span className="ing-item__dot" aria-hidden="true" />
                    <span className="ing-item__name">{ing.name}</span>
                    {ing.quantity && <span className="ing-item__qty">{ing.quantity}</span>}
                  </li>
                ))}
              </ul>
            </div>

            {recipe.seasonings.length > 0 && (
              <div className="section">
                <h2 className="section__title">Seasonings</h2>
                <ul className="ing-list">
                  {recipe.seasonings.map((ing, i) => (
                    <li className="ing-item ing-item--seasoning" key={`${ing.name}-${i}`}>
                      <span className="ing-item__dot" aria-hidden="true" />
                      <span className="ing-item__name">{ing.name}</span>
                      {ing.quantity && <span className="ing-item__qty">{ing.quantity}</span>}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            <div className="section">
              <h2 className="section__title">Steps</h2>
              <ol className="steps">
                {recipe.steps.map((step, i) => (
                  <li className="step" key={i}>
                    <span className="step__num" aria-hidden="true">
                      {i + 1}
                    </span>
                    <span className="step__text">{step}</span>
                  </li>
                ))}
              </ol>
            </div>

            <div className="section">
              <h2 className="section__title">
                <BookOpen aria-hidden="true" />
                Why this works
              </h2>
              <p className="prose">{recipe.creative_explanation}</p>
              {recipe.creative_hypothesis && (
                <p className="prose" style={{ marginTop: 8 }}>
                  <strong>Creative hypothesis: </strong>
                  {recipe.creative_hypothesis}
                </p>
              )}
            </div>

            {trace && <TraceTimeline trace={trace} />}
          </article>
        </div>

        <aside>
          {cie && <CieScorePanel cie={cie} />}

          {trace?.risk_notes && (
            <div className="risk-note" style={{ marginTop: 16 }} data-testid="risk-note">
              <TriangleAlert aria-hidden="true" />
              <div>
                <strong>Before you cook:</strong> {trace.risk_notes}
              </div>
            </div>
          )}

          {response.meta.demo_mode && (
            <p className="cie-note" style={{ marginTop: 16 }}>
              Generated offline with the repository DemoProvider — no live model was called.
            </p>
          )}

          {response.meta.fallback_reason && (
            <p className="cie-note cie-note--fallback" style={{ marginTop: 16 }} data-testid="fallback-note">
              {response.meta.fallback_reason}
            </p>
          )}
        </aside>
      </div>
    </section>
  )
}
