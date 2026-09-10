import { render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it } from 'vitest'
import App from './App'
import { CIE_DIMENSION_KEYS } from './types'
import { forceReducedMotion, installApiMock, makeResponse, type CapturedRequest } from './test/fixture'

let captured: CapturedRequest[] = []

async function openFridge(user: ReturnType<typeof userEvent.setup>) {
  await user.click(screen.getByTestId('fridge-button'))
  await screen.findByTestId('basket-count')
}

async function pickIngredient(user: ReturnType<typeof userEvent.setup>, query: string, id: string) {
  const input = screen.getByLabelText('Search ingredients by name')
  await user.clear(input)
  await user.type(input, query)
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
    expect(document.querySelector('.fridge-frame--closed')).not.toHaveClass('is-active')
    expect(screen.getByTestId('basket-count')).toHaveTextContent('Nothing picked yet')
  })
})

describe('ingredient selection', () => {
  it('shows categories, supports search, and toggles selection', async () => {
    const user = userEvent.setup()
    installApiMock({ captured })
    render(<App />)
    await openFridge(user)

    // Default category is Vegetables and the shelf is paginated (12 per page).
    expect(screen.getByRole('tab', { name: /Vegetables/ })).toHaveAttribute(
      'aria-selected',
      'true',
    )
    expect(screen.getByTestId('tile-carrot')).toBeInTheDocument()
    expect(screen.queryByTestId('tile-chicken')).not.toBeInTheDocument()

    // Search reaches across categories.
    await pickIngredient(user, 'chicken', 'chicken')
    expect(screen.getByTestId('tile-chicken')).toHaveAttribute('aria-pressed', 'true')

    // Selection survives a category change.
    await user.click(screen.getByRole('tab', { name: /Protein/ }))
    expect(screen.getByTestId('tile-chicken')).toHaveAttribute('aria-pressed', 'true')

    // Toggling off works.
    await user.click(screen.getByTestId('tile-chicken'))
    expect(screen.getByTestId('tile-chicken')).toHaveAttribute('aria-pressed', 'false')
  })

  it('keeps Make Magic disabled until two ingredients are picked', async () => {
    const user = userEvent.setup()
    installApiMock({ captured })
    render(<App />)
    await openFridge(user)

    const makeMagic = screen.getByTestId('make-magic')
    expect(makeMagic).toBeDisabled()

    await pickIngredient(user, 'chicken', 'chicken')
    expect(screen.getByTestId('make-magic')).toBeDisabled()

    await pickIngredient(user, 'coffee', 'coffee')
    await waitFor(() => expect(screen.getByTestId('make-magic')).toBeEnabled())
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
})

describe('generation flow', () => {
  it('sends ingredients and preferences, then shows the recipe', async () => {
    const user = userEvent.setup()
    installApiMock({ captured, generate: makeResponse() })
    render(<App />)
    await openFridge(user)

    await pickIngredient(user, 'chicken', 'chicken')
    await pickIngredient(user, 'coffee', 'coffee')

    // Change a preference away from the default so propagation is observable.
    await user.click(screen.getByRole('radio', { name: 'Spicy' }))
    await user.click(screen.getByRole('radio', { name: 'Under 20 min' }))

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
    await user.click(screen.getByTestId('make-magic'))
    await screen.findByTestId('cie-panel')

    await user.click(screen.getByTestId('save-recipe'))
    expect(screen.getByTestId('save-recipe')).toBeDisabled()
    expect(screen.getByTestId('save-recipe')).toHaveTextContent('Saved')

    await user.click(screen.getByRole('button', { name: /Saved recipes \(1\)/ }))
    expect(await screen.findByText('Coffee-Braised Chicken with Melted Cheese Crust')).toBeInTheDocument()
    expect(screen.queryByTestId('favorites-empty')).not.toBeInTheDocument()

    // Persists across a full remount.
    first.unmount()
    render(<App />)
    await user.click(screen.getByRole('button', { name: /Saved recipes \(1\)/ }))
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

    await user.click(screen.getByRole('button', { name: /Saved recipes \(0\)/ }))
    const empty = await screen.findByTestId('favorites-empty')
    expect(empty).toHaveTextContent('No saved recipes yet.')
    expect(empty).toHaveTextContent('Your future favorites will live here.')
  })
})
