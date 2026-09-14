import { useCallback, useEffect, useMemo, useRef, useState, type CSSProperties } from 'react'
import { Heart, Sparkles } from 'lucide-react'
import { fetchHealth } from './api/client'
import { CookingMode } from './components/CookingMode'
import { ErrorPanel } from './components/ErrorPanel'
import { FavoritesView } from './components/FavoritesView'
import { Fridge, type FridgeFrame } from './components/Fridge'
import { IngredientShelf } from './components/IngredientShelf'
import { LoadingScene } from './components/LoadingScene'
import { Pagination } from './components/Pagination'
import { PreferencesPanel } from './components/PreferencesPanel'
import { RecipeResult } from './components/RecipeResult'
import { SelectionControls } from './components/SelectionControls'
import { DEFAULT_PREFERENCES, type GenerateResponse, type Preferences, type SavedRecipe } from './types'
import { SCENE } from './data/ingredients'
import { favoriteKey, useFavorites } from './hooks/useFavorites'
import { usePrefersReducedMotion } from './hooks/usePrefersReducedMotion'
import { useIngredientFilter } from './hooks/useIngredientFilter'
import { useRecipeGeneration } from './hooks/useRecipeGeneration'

type Stage =
  | 'landing'
  | 'select'
  | 'preferences'
  | 'loading'
  | 'result'
  | 'cooking'
  | 'favorites'
  | 'error'

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

  const filter = useIngredientFilter()
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

  const selectedCount = selectedIds.length
  const continueDisabled = selectedCount < 2

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

  const goToPreferences = useCallback(() => {
    if (selectedCount >= 2) setStage('preferences')
  }, [selectedCount])

  const backToIngredients = useCallback(() => setStage('select'), [])

  const backToLanding = useCallback(() => {
    setFrame('closed')
    setStage('landing')
  }, [])

  const sceneStage = stage === 'landing' ? 'landing' : stage === 'preferences' ? 'preferences' : 'select'

  return (
    <div className="app">
      <header className="app-header">
        <div className="brand">
          <span className="brand__mark">NewwwRecipe</span>
          <span className="brand__tag">creative cooking from what you already have</span>
        </div>
        <div className="app-header__spacer" />
        <div className="header-actions">
          {(() => {
            const genMeta = generation.data?.meta
            const mode: 'demo' | 'live' | 'fallback' = genMeta
              ? genMeta.fallback_reason
                ? 'fallback'
                : genMeta.demo_mode
                  ? 'demo'
                  : 'live'
              : demoMode
                ? 'demo'
                : 'live'
            const label =
              mode === 'fallback' ? 'Demo fallback' : mode === 'live' ? 'Live · Hy3' : 'Demo mode'
            const title =
              mode === 'fallback'
                ? genMeta?.fallback_reason ?? 'Live generation failed; showing a demo result.'
                : mode === 'live'
                  ? 'Using the live Hy3 model'
                  : 'Running without a live model'
            return (
              <span
                className={`demo-badge demo-badge--${mode}`}
                data-testid="demo-badge"
                data-mode={mode}
                title={title}
              >
                <Sparkles aria-hidden="true" />
                {label}
              </span>
            )
          })()}
          <button type="button" className="btn btn--quiet" onClick={() => setStage('favorites')}>
            <Heart className="btn__icon" aria-hidden="true" />
            Favorites · {favorites.favorites.length}
          </button>
        </div>
      </header>

      <main className="app-main">
        {(stage === 'landing' || stage === 'select' || stage === 'preferences') && (
          <section
            className={`scene scene--${sceneStage}`}
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
                    Open the fridge and pick what’s inside. We’ll turn it into something
                    unexpectedly delicious.
                  </p>
                  <p className="landing__hint">
                    <Sparkles aria-hidden="true" />
                    Open the fridge to begin
                  </p>
                </div>
              ) : stage === 'select' ? (
                <SelectionControls
                  filter={filter}
                  selectedIds={selectedIds}
                  onRemove={removeIngredient}
                  onClearAll={clearSelection}
                  onContinue={goToPreferences}
                  onBack={backToLanding}
                  continueDisabled={continueDisabled}
                />
              ) : (
                <div className="prefs__panel" data-testid="preferences-panel">
                  <h1 className="prefs__heading">Almost there</h1>
                  <p className="prefs__lede">
                    {selectedCount} ingredient{selectedCount === 1 ? '' : 's'} chosen — tweak the
                    vibe, then make magic.
                  </p>
                  <div className="prefs__scroll">
                    <PreferencesPanel value={preferences} onChange={setPreferences} />
                  </div>
                  <div className="prefs__actions">
                    <button
                      type="button"
                      className="btn btn--ghost"
                      onClick={backToIngredients}
                      data-testid="back-to-ingredients"
                    >
                      Back to ingredients
                    </button>
                    <button
                      type="button"
                      className="btn btn--primary btn--block"
                      onClick={() => runGeneration()}
                      data-testid="make-magic"
                    >
                      <Sparkles className="btn__icon" aria-hidden="true" />
                      Make Magic
                    </button>
                  </div>
                </div>
              )}
            </div>

            <div className="fridge-stage">
              <Fridge
                frame={frame}
                interactive={stage === 'landing'}
                onActivate={openFridge}
              >
                {stage !== 'landing' && (
                  <IngredientShelf
                    items={filter.items}
                    selectedIds={selectedIds}
                    onToggle={toggleIngredient}
                  />
                )}
              </Fridge>
              {(stage === 'select' || stage === 'preferences') && <Pagination filter={filter} />}
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
