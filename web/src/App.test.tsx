import { fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it } from 'vitest'
import App from './App'
import { CIE_DIMENSION_KEYS } from './types'
import { forceReducedMotion, installApiMock, makeResponse, type CapturedRequest } from './test/fixture'

let captured: CapturedRequest[] = []

/** Open the fridge and land on the ingredient-selection (open-fridge) stage. */
async function openFridge(user: ReturnType<typeof userEvent.setup>) {
  await user.click(screen.getByTestId('fridge-button'))
  await screen.findByTestId('basket-count')
}

/** Pick an ingredient by searching for it, then clicking its tile. */
async function pickIngredient(user: ReturnType<typeof userEvent.setup>, query: string, id: string) {
  // Apply the complete query in a single change event. Typing char-by-char with
  // user-event re-renders the field as soon as the "Clear search" button appears
  // (query becomes non-empty), which detaches the controlled input node mid-type
  // in jsdom and truncates the value to its first character.
  const input = screen.getByLabelText('Search ingredients by name')
  fireEvent.change(input, { target: { value: query } })
  const tile = await screen.findByTestId(`tile-${id}`)
  await user.click(tile)
}

beforeEach(() => {
  captured = []
  forceReducedMotion()
  window.localStorage.clear()
})

describe('landing and fridge', () => {
  it('starts on the closed-fridge landing state', async () => {
    installApiMock({ captured })
    render(<App />)

    const button = screen.getByTestId('fridge-button')
    expect(button).toBeInTheDocument()
    expect(document.querySelector('.fridge-frame--closed')).toHaveClass('is-active')
    expect(document.querySelector('.fridge-frame--open')).not.toHaveClass('is-active')
    expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent('What do we have?')
    // Selection controls only appear after the fridge is opened.
    expect(screen.queryByLabelText('Search ingredients by name')).not.toBeInTheDocument()
    expect(screen.queryByTestId('basket-count')).not.toBeInTheDocument()
  })

  it('opens the fridge when the refrigerator is activated', async () => {
    const user = userEvent.setup()
    installApiMock({ captured })
    render(<App />)

    await user.click(screen.getByTestId('fridge-button'))

    await waitFor(() => {
      expect(document.querySelector('.fridge-frame--open')).toHaveClass('is-active')
    })
    // The closed frame is no longer the visible base.
    expect(document.querySelector('.fridge-frame--closed')).not.toHaveClass('is-active')
    // Selection controls are now rendered.
    expect(screen.getByLabelText('Search ingredients by name')).toBeInTheDocument()
    expect(screen.getByTestId('basket-count')).toHaveTextContent('Nothing picked yet')
  })

  it('does not show preference controls during ingredient selection', async () => {
    const user = userEvent.setup()
    installApiMock({ captured })
    render(<App />)
    await openFridge(user)

    expect(screen.queryByRole('radio')).not.toBeInTheDocument()
    expect(screen.queryByTestId('preferences-panel')).not.toBeInTheDocument()
  })
})

describe('ingredient selection', () => {
  it('shows categories, supports global search, and toggles selection', async () => {
    const user = userEvent.setup()
    installApiMock({ captured })
    render(<App />)
    await openFridge(user)

    // Default category is Vegetables and the shelf is paginated (12 per page).
    expect(screen.getByRole('button', { name: /Vegetables/ })).toHaveAttribute(
      'aria-pressed',
      'true',
    )
    expect(screen.getByTestId('tile-carrot')).toBeInTheDocument()
    expect(screen.queryByTestId('tile-chicken')).not.toBeInTheDocument()

    // Search reaches across categories.
    await pickIngredient(user, 'chicken', 'chicken')
    expect(screen.getByTestId('tile-chicken')).toHaveAttribute('aria-pressed', 'true')

    // Selection survives a category change.
    await user.click(screen.getByRole('button', { name: /Protein/ }))
    expect(screen.getByTestId('tile-chicken')).toHaveAttribute('aria-pressed', 'true')

    // Toggling off works.
    await user.click(screen.getByTestId('tile-chicken'))
    expect(screen.getByTestId('tile-chicken')).toHaveAttribute('aria-pressed', 'false')
  })

  it('exposes complete ingredient names rather than abbreviations', async () => {
    const user = userEvent.setup()
    installApiMock({ captured })
    render(<App />)
    await openFridge(user)

    await pickIngredient(user, 'napa', 'napa_cabbage')
    expect(screen.getByTestId('tile-napa_cabbage')).toHaveTextContent('Napa Cabbage')
  })

  it('keeps Continue disabled until two ingredients are picked', async () => {
    const user = userEvent.setup()
    installApiMock({ captured })
    render(<App />)
    await openFridge(user)

    const continueButton = screen.getByTestId('continue-button')
    expect(continueButton).toBeDisabled()

    await pickIngredient(user, 'chicken', 'chicken')
    expect(continueButton).toBeDisabled()

    await pickIngredient(user, 'coffee', 'coffee')
    await waitFor(() => expect(continueButton).toBeEnabled())
    expect(screen.getByTestId('basket-count')).toHaveTextContent('2 ingredients picked')
  })

  it('removes an ingredient from the basket chips', async () => {
    const user = userEvent.setup()
    installApiMock({ captured })
    render(<App />)
    await openFridge(user)

    await pickIngredient(user, 'chicken', 'chicken')
    await pickIngredient(user, 'coffee', 'coffee')
    expect(screen.getByTestId('basket-count')).toHaveTextContent('2 ingredients picked')

    await user.click(screen.getByRole('button', { name: 'Remove Chicken' }))
    expect(screen.getByTestId('basket-count')).toHaveTextContent('1 ingredient picked')

    await user.click(screen.getByRole('button', { name: 'Clear all' }))
    expect(screen.getByTestId('basket-count')).toHaveTextContent('Nothing picked yet')
  })

  it('survives pagination and category changes', async () => {
    const user = userEvent.setup()
    installApiMock({ captured })
    render(<App />)
    await openFridge(user)

    await pickIngredient(user, 'chicken', 'chicken')
    await pickIngredient(user, 'coffee', 'coffee')

    // Both picks are recorded regardless of the active filter.
    expect(screen.getByTestId('basket-count')).toHaveTextContent('2 ingredients picked')

    // Switching category clears the search and shows that category's page 1.
    // The selection survives the category change even though Coffee (a Pantry
    // item) is no longer on screen — it stays reflected in the basket.
    await user.click(screen.getByRole('button', { name: /Protein/ }))
    expect(screen.getByTestId('tile-chicken')).toHaveAttribute('aria-pressed', 'true')
    expect(screen.getByTestId('tile-bacon')).toBeInTheDocument()
    const basket = screen.getByLabelText('Selected ingredients')
    expect(within(basket).getByText('Chicken')).toBeInTheDocument()
    expect(within(basket).getByText('Coffee')).toBeInTheDocument()
  })

  it('search resets pagination to page 1', async () => {
    const user = userEvent.setup()
    installApiMock({ captured })
    render(<App />)
    await openFridge(user)

    await user.click(screen.getByRole('button', { name: 'Next page' }))
    expect(screen.getByText(/Page 2 of 3/)).toBeInTheDocument()

    const input = screen.getByLabelText('Search ingredients by name')
    fireEvent.change(input, { target: { value: 'chicken' } })
    // Searching is global and resets to page 1.
    expect(screen.getByText(/Page 1 of 1/)).toBeInTheDocument()
    expect(screen.getByTestId('tile-chicken')).toBeInTheDocument()
  })
})

describe('preferences step', () => {
  async function selectTwoAndContinue(user: ReturnType<typeof userEvent.setup>) {
    await openFridge(user)
    await pickIngredient(user, 'chicken', 'chicken')
    await pickIngredient(user, 'coffee', 'coffee')
    await user.click(screen.getByTestId('continue-button'))
    await screen.findByTestId('preferences-panel')
  }

  it('Continue opens a compact preference step with Back and Make Magic', async () => {
    const user = userEvent.setup()
    installApiMock({ captured })
    render(<App />)
    await selectTwoAndContinue(user)

    expect(screen.getByTestId('back-to-ingredients')).toBeInTheDocument()
    expect(screen.getByTestId('make-magic')).toBeInTheDocument()
    // Cuisine / flavor / time options are present.
    expect(screen.getByRole('radio', { name: 'Surprise me' })).toBeInTheDocument()
    expect(screen.getByRole('radio', { name: 'Spicy' })).toBeInTheDocument()
  })

  it('Back to ingredients preserves selections and preference values', async () => {
    const user = userEvent.setup()
    installApiMock({ captured })
    render(<App />)
    await selectTwoAndContinue(user)

    await user.click(screen.getByRole('radio', { name: 'Spicy' }))
    await user.click(screen.getByRole('button', { name: 'Back to ingredients' }))

    // We're back on the selection stage with the same two picks preserved.
    expect(screen.getByTestId('basket-count')).toHaveTextContent('2 ingredients picked')
    // Selection persists in the basket regardless of the active filter — Chicken
    // (Protein) and Coffee (Pantry) live in different categories, so they are not
    // both on screen at once, but both remain selected.
    const basket = screen.getByLabelText('Selected ingredients')
    expect(within(basket).getByText('Chicken')).toBeInTheDocument()
    expect(within(basket).getByText('Coffee')).toBeInTheDocument()
  })

  it('Make Magic submits the existing generation request', async () => {
    const user = userEvent.setup()
    installApiMock({ captured })
    render(<App />)
    await selectTwoAndContinue(user)

    await user.click(screen.getByRole('radio', { name: 'Spicy' }))
    await user.click(screen.getByRole('radio', { name: 'Under 20 min' }))
    const allergies = screen.getByLabelText('Dietary needs or allergies')
    await user.type(allergies, 'nut allergy')
    const craving = screen.getByLabelText('What are you craving?')
    await user.type(craving, 'cozy')

    await user.click(screen.getByTestId('make-magic'))

    expect(captured).toHaveLength(1)
    const body = captured[0].body as {
      ingredients: string[]
      preferences: { cuisine: string; flavor: string; time: string; constraints: string }
    }
    expect(body.ingredients).toEqual(['chicken', 'coffee'])
    expect(body.preferences.cuisine).toBe('fusion')
    expect(body.preferences.flavor).toBe('spicy')
    expect(body.preferences.time).toBe('under-20')
    // The two free-text fields are composed into the backend `constraints` string.
    expect(body.preferences.constraints).toContain('nut allergy')
    expect(body.preferences.constraints).toContain('cozy')
  })
})

describe('generation flow', () => {
  it('sends ingredients and preferences, then shows the recipe', async () => {
    const user = userEvent.setup()
    installApiMock({ captured, generate: makeResponse() })
    render(<App />)
    await openFridge(user)
    await pickIngredient(user, 'chicken', 'chicken')
    await pickIngredient(user, 'coffee', 'coffee')

    await user.click(screen.getByTestId('continue-button'))
    await screen.findByTestId('preferences-panel')
    await user.click(screen.getByRole('radio', { name: 'Spicy' }))
    await user.click(screen.getByRole('radio', { name: 'Under 20 min' }))
    await user.click(screen.getByTestId('make-magic'))

    expect(captured).toHaveLength(1)
    const body = captured[0].body as {
      ingredients: string[]
      preferences: { cuisine: string; flavor: string; time: string }
    }
    expect(body.ingredients).toEqual(['chicken', 'coffee'])
    expect(body.preferences.cuisine).toBe('fusion')
    expect(body.preferences.flavor).toBe('spicy')
    expect(body.preferences.time).toBe('under-20')

    expect(await screen.findByRole('heading', { level: 1 })).toHaveTextContent(
      'Coffee-Braised Chicken with Melted Cheese Crust',
    )
  })

  it('shows a loading state with a rotating status message', async () => {
    const user = userEvent.setup()
    let resolve: ((value: Response) => void) | undefined
    const pending = new Promise<Response>((r) => {
      resolve = r
    })
    const fetchMock = async (input: RequestInfo | URL) => {
      const url = typeof input === 'string' ? input : String(input)
      if (url.includes('/api/health')) {
        return new Response(JSON.stringify({ status: 'ok', demo_mode: true }), { status: 200 })
      }
      return pending
    }
    globalThis.fetch = fetchMock as unknown as typeof fetch

    render(<App />)
    await openFridge(user)
    await pickIngredient(user, 'chicken', 'chicken')
    await pickIngredient(user, 'coffee', 'coffee')
    await user.click(screen.getByTestId('continue-button'))
    await screen.findByTestId('preferences-panel')
    await user.click(screen.getByTestId('make-magic'))

    expect(screen.getByText('Making a little kitchen magic…')).toBeInTheDocument()
    expect(screen.getByTestId('loading-status')).toHaveTextContent('Finding flavor bridges…')

    resolve!(
      new Response(JSON.stringify(makeResponse()), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      }),
    )

    expect(await screen.findByTestId('cie-panel')).toBeInTheDocument()
  })

  it('surfaces backend errors with a retry action', async () => {
    const user = userEvent.setup()
    installApiMock({
      captured,
      fail: { status: 502, detail: 'Recipe generation failed upstream: boom' },
    })
    render(<App />)
    await openFridge(user)
    await pickIngredient(user, 'chicken', 'chicken')
    await pickIngredient(user, 'coffee', 'coffee')
    await user.click(screen.getByTestId('continue-button'))
    await screen.findByTestId('preferences-panel')
    await user.click(screen.getByTestId('make-magic'))

    const alert = await screen.findByRole('alert')
    expect(alert).toHaveTextContent('Recipe generation failed upstream: boom')
    expect(screen.getByRole('button', { name: /Try again/ })).toBeInTheDocument()
  })
})

describe('recipe result', () => {
  async function renderResult(user: ReturnType<typeof userEvent.setup>) {
    installApiMock({ captured, generate: makeResponse() })
    render(<App />)
    await openFridge(user)
    await pickIngredient(user, 'chicken', 'chicken')
    await pickIngredient(user, 'coffee', 'coffee')
    await user.click(screen.getByTestId('continue-button'))
    await screen.findByTestId('preferences-panel')
    await user.click(screen.getByTestId('make-magic'))
    await screen.findByTestId('cie-panel')
  }

  it('displays all six canonical CIE dimensions exactly once', async () => {
    const user = userEvent.setup()
    await renderResult(user)

    for (const key of CIE_DIMENSION_KEYS) {
      const nodes = screen.getAllByTestId(`cie-dim-${key}`)
      expect(nodes).toHaveLength(1)
      expect(nodes[0]).toHaveTextContent('/ 5')
    }
    expect(screen.getByTestId('cie-total')).toHaveTextContent('4.25')
  })

  it('displays the six Innovation Trace stages', async () => {
    const user = userEvent.setup()
    await renderResult(user)

    const timeline = screen.getByTestId('trace-timeline')
    for (const label of [
      'Existing Culinary Context',
      'Ingredient & Technique Knowledge',
      'Innovation Delta',
      'Mechanistic Justification',
      'Creative Hypothesis',
      'Risk & Constraint',
    ]) {
      expect(within(timeline).getByText(label)).toBeInTheDocument()
    }
  })

  it('never renders a finished-dish image', async () => {
    const user = userEvent.setup()
    await renderResult(user)

    const images = Array.from(document.querySelectorAll('img'))
    expect(images.length).toBeGreaterThan(0)
    for (const img of images) {
      const src = img.getAttribute('src') ?? ''
      expect(src.startsWith('/ingredients/') || src.startsWith('/scene/')).toBe(true)
    }
  })

  it('navigates cooking mode step by step', async () => {
    const user = userEvent.setup()
    await renderResult(user)

    await user.click(screen.getByRole('button', { name: /Start Cooking/ }))
    expect(screen.getByTestId('step-counter')).toHaveTextContent('Step 1 of 3')
    expect(screen.getByTestId('cooking-step')).toHaveTextContent('Prep the given ingredients.')

    await user.click(screen.getByRole('button', { name: /Next/ }))
    expect(screen.getByTestId('step-counter')).toHaveTextContent('Step 2 of 3')

    await user.click(screen.getByRole('button', { name: /Back/ }))
    expect(screen.getByTestId('step-counter')).toHaveTextContent('Step 1 of 3')

    await user.click(screen.getByRole('button', { name: /Exit cooking mode/ }))
    expect(await screen.findByTestId('cie-panel')).toBeInTheDocument()
  })
})

describe('favorites', () => {
  it('saves, persists across remounts, and can be removed', async () => {
    const user = userEvent.setup()
    installApiMock({ captured, generate: makeResponse() })

    const first = render(<App />)
    await openFridge(user)
    await pickIngredient(user, 'chicken', 'chicken')
    await pickIngredient(user, 'coffee', 'coffee')
    await user.click(screen.getByTestId('continue-button'))
    await screen.findByTestId('preferences-panel')
    await user.click(screen.getByTestId('make-magic'))
    await screen.findByTestId('cie-panel')

    await user.click(screen.getByTestId('save-recipe'))
    expect(screen.getByTestId('save-recipe')).toBeDisabled()
    expect(screen.getByTestId('save-recipe')).toHaveTextContent('Saved')

    await user.click(screen.getByRole('button', { name: /Favorites/ }))
    expect(await screen.findByText('Coffee-Braised Chicken with Melted Cheese Crust')).toBeInTheDocument()
    expect(screen.queryByTestId('favorites-empty')).not.toBeInTheDocument()

    // Persists across a full remount.
    first.unmount()
    render(<App />)
    await user.click(screen.getByRole('button', { name: /Favorites/ }))
    expect(await screen.findByText('Coffee-Braised Chicken with Melted Cheese Crust')).toBeInTheDocument()

    // Remove with confirmation.
    await user.click(screen.getByRole('button', { name: /Remove Coffee-Braised/ }))
    const dialog = await screen.findByRole('dialog')
    await user.click(within(dialog).getByRole('button', { name: 'Remove' }))
    expect(await screen.findByTestId('favorites-empty')).toHaveTextContent(
      'No saved recipes yet.',
    )
  })

  it('shows the empty state when nothing is saved', async () => {
    const user = userEvent.setup()
    installApiMock({ captured })
    render(<App />)

    await user.click(screen.getByRole('button', { name: /Favorites/ }))
    const empty = await screen.findByTestId('favorites-empty')
    expect(empty).toHaveTextContent('No saved recipes yet.')
    expect(empty).toHaveTextContent('Your future favorites will live here.')
  })

  describe('shelf coordinate system is reused across stages', () => {
    it('keeps the same four-shelf mapping when switching to preferences', async () => {
      const user = userEvent.setup()
      installApiMock({ captured })
      render(<App />)
      await openFridge(user)
      await pickIngredient(user, 'chicken', 'chicken')
      await pickIngredient(user, 'coffee', 'coffee')
      // Clear any search so the default 12-per-page shelf mapping is what we check.
      fireEvent.change(screen.getByLabelText('Search ingredients by name'), { target: { value: '' } })
      await user.click(screen.getByTestId('continue-button'))
      await screen.findByTestId('preferences-panel')

      // The fridge must not resize or swap its coordinate system for preferences.
      const rows = screen.getAllByTestId(/^shelf-row-/)
      expect(rows).toHaveLength(4)
      expect(rows.map((r) => r.getAttribute('data-shelf')).sort()).toEqual([
        '1',
        '2',
        '3',
        '4',
      ])

      const tiles = document.querySelectorAll('.shelf__tile')
      expect(tiles.length).toBe(12)
      for (const tile of tiles) {
        // Every visible ingredient is still tied to exactly one shelf row.
        expect(tile.closest('.shelf__row')).not.toBeNull()
      }
    })
  })
})
