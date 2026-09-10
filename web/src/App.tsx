import { useCallback, useEffect, useMemo, useRef, useState, type CSSProperties } from 'react'
import { ArrowRight, Heart, Sparkles } from 'lucide-react'
import { fetchHealth } from './api/client'
import { Basket } from './components/Basket'
import { CookingMode } from './components/CookingMode'
import { ErrorPanel } from './components/ErrorPanel'
import { FavoritesView } from './components/FavoritesView'
import { Fridge, type FridgeFrame } from './components/Fridge'
import { IngredientShelf } from './components/IngredientShelf'
import { LoadingScene } from './components/LoadingScene'
import { PreferencesPanel } from './components/PreferencesPanel'
import { RecipeResult } from './components/RecipeResult'
import { DEFAULT_PREFERENCES, type GenerateResponse, type Preferences, type SavedRecipe } from './types'
import { SCENE } from './data/ingredients'
import { favoriteKey, useFavorites } from './hooks/useFavorites'
import { usePrefersReducedMotion } from './hooks/usePrefersReducedMotion'
import { useRecipeGeneration } from './hooks/useRecipeGeneration'

type Stage = 'landing' | 'select' | 'loading' | 'result' | 'cooking' | 'favorites' | 'error'

const AJAR_MS = 380
const OPEN_MS = 620

export default function App() {
  const reducedMotion = usePrefersReducedMotion()

  const [stage, setStage] = useState<Stage>('landing')
  const [frame, setFrame] = useState<FridgeFrame>('closed')
  const [selectedIds, setSelectedIds] = useState<string[]>([])
  const [preferences, setPreferences] = useState<Preferences>(DEFAULT_PREFERENCES)
  const [viewingFavorite, setViewingFavorite] = useState<GenerateResponse | null>(null)
  const [demoMode, setDemoMode] = useState(false)

  const generation = useRecipeGeneration()
  const favorites = useFavorites()
  const timers = useRef<number[]>([])

  useEffect(() => () => timers.current.forEach(window.clearTimeout), [])

  // --- backend status (demo-mode badge) --------------------------------------------
  useEffect(() => {
    const controller = new AbortController()
    fetchHealth(controller.signal)
      .then((health) => setDemoMode(health.demo_mode))
      .catch(() => setDemoMode(false))
    return () => controller.abort()
  }, [])

  // --- fridge opening sequence ------------------------------------------------------
  const openFridge = useCallback(() => {
    if (reducedMotion) {
      setFrame('open')
      setStage('select')
      return
    }
    setFrame('ajar')
    timers.current.push(
      window.setTimeout(() => setFrame('open'), AJAR_MS),
      window.setTimeout(() => setStage('select'), OPEN_MS),
    )
  }, [reducedMotion])

  // --- selection --------------------------------------------------------------------
  const toggleIngredient = useCallback((id: string) => {
    setSelectedIds((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id],
    )
  }, [])

  const removeIngredient = useCallback((id: string) => {
    setSelectedIds((prev) => prev.filter((x) => x !== id))
  }, [])

  const clearSelection = useCallback(() => setSelectedIds([]), [])

  // --- generation -------------------------------------------------------------------
  const runGeneration = useCallback(
    (avoid: string[] = []) => {
      setViewingFavorite(null)
      setStage('loading')
      generation.start({
        ingredients: selectedIds,
        preferences,
        ...(avoid.length ? { avoid } : {}),
      })
    },
    [generation, preferences, selectedIds],
  )

  // Follow the request lifecycle into the result / error stage.
  useEffect(() => {
    if (stage !== 'loading') return
    if (generation.status === 'success') setStage('result')
    if (generation.status === 'error') setStage('error')
  }, [generation.status, stage])

  const activeResponse = viewingFavorite ?? generation.data

  const savedKey = useMemo(
    () =>
      activeResponse
        ? favoriteKey(activeResponse.recipe.name, selectedIds, preferences)
        : '',
    [activeResponse, selectedIds, preferences],
  )

  const onSave = useCallback(() => {
    if (!activeResponse) return
    favorites.save({ response: activeResponse, ingredientIds: selectedIds, preferences })
  }, [activeResponse, favorites, preferences, selectedIds])

  const onTryAnother = useCallback(() => {
    if (!activeResponse) return
    runGeneration([activeResponse.recipe.name])
  }, [activeResponse, runGeneration])

  const openFavorite = useCallback((fav: SavedRecipe) => {
    setSelectedIds(fav.ingredientIds)
    setPreferences(fav.preferences)
    setViewingFavorite(fav.response)
    setStage('result')
  }, [])

  const backToFridge = useCallback(() => {
    generation.reset()
    setViewingFavorite(null)
    setStage('select')
  }, [generation])

  return (
    <div className="app">
      <header className="app-header">
        <div className="brand">
          <span className="brand__mark">NewwwRecipe</span>
          <span className="brand__tag">creative cooking from what you already have</span>
        </div>
        <div className="app-header__spacer" />
        <div className="header-actions">
          {demoMode && (
            <span className="demo-badge" data-testid="demo-badge">
              <Sparkles aria-hidden="true" />
              Demo mode
            </span>
          )}
          <button type="button" className="btn btn--quiet" onClick={() => setStage('favorites')}>
            <Heart className="btn__icon" aria-hidden="true" />
            Saved<span className="sr-only"> recipes</span> ({favorites.favorites.length})
          </button>
        </div>
      </header>

      <main className="app-main">
        {(stage === 'landing' || stage === 'select') && (
          <section
            className={`scene ${stage === 'select' ? 'scene--select' : 'scene--landing'}`}
            style={{ '--scene-kitchen': SCENE.kitchenBackground } as CSSProperties}
          >
            <div className="scene__aside">
              {stage === 'landing' ? (
                <div className="landing__copy">
                  <span className="landing__eyebrow">Fridge first, ideas second</span>
                  <h1 className="landing__title">
                    What do <em>we</em> have?
                  </h1>
                  <p className="landing__lede">
                    Pick what’s in your kitchen. We’ll turn it into something unexpectedly
                    delicious.
                  </p>
                  <p className="landing__hint">
                    <ArrowRight aria-hidden="true" />
                    Tap the fridge to open it
                  </p>
                </div>
              ) : (
                <div className="select__panel">
                  <Basket
                    selectedIds={selectedIds}
                    onRemove={removeIngredient}
                    onClearAll={clearSelection}
                  />
                  <PreferencesPanel value={preferences} onChange={setPreferences} />
                  <div className="select__actions">
                    <button
                      type="button"
                      className="btn btn--primary"
                      disabled={selectedIds.length < 2}
                      onClick={() => runGeneration()}
                      data-testid="make-magic"
                    >
                      <Sparkles className="btn__icon" aria-hidden="true" />
                      Make Magic
                    </button>
                    <button
                      type="button"
                      className="btn btn--ghost"
                      onClick={() => {
                        setFrame('closed')
                        setStage('landing')
                      }}
                    >
                      Close the fridge
                    </button>
                  </div>
                  <p className="select__note">
                    {selectedIds.length < 2
                      ? 'Pick at least two ingredients to start cooking.'
                      : `${selectedIds.length} ingredients selected — preferences are optional.`}
                  </p>
                </div>
              )}
            </div>

            <div className="fridge-stage">
              <Fridge
                frame={frame}
                interactive={stage === 'landing'}
                onActivate={openFridge}
              >
                {stage === 'select' && (
                  <IngredientShelf selectedIds={selectedIds} onToggle={toggleIngredient} />
                )}
              </Fridge>
            </div>
          </section>
        )}

        {stage === 'loading' && (
          <LoadingScene messageIndex={generation.messageIndex} onCancel={generation.cancel} />
        )}

        {stage === 'error' && (
          <ErrorPanel
            message={generation.error ?? 'Unknown error'}
            onRetry={generation.retry}
            onBack={backToFridge}
          />
        )}

        {stage === 'result' && activeResponse && (
          <RecipeResult
            response={activeResponse}
            ingredientIds={selectedIds}
            preferences={preferences}
            saved={favorites.isSaved(savedKey)}
            onSave={onSave}
            onTryAnother={onTryAnother}
            onStartCooking={() => setStage('cooking')}
            onBackToFridge={backToFridge}
          />
        )}

        {stage === 'cooking' && activeResponse && (
          <CookingMode recipe={activeResponse.recipe} onExit={() => setStage('result')} />
        )}

        {stage === 'favorites' && (
          <FavoritesView
            favorites={favorites.favorites}
            onOpen={openFavorite}
            onRemove={favorites.remove}
            onBack={() => setStage(activeResponse ? 'result' : 'select')}
          />
        )}
      </main>
    </div>
  )
}
