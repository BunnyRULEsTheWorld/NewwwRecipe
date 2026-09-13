import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { IngredientShelf } from './IngredientShelf'
import { INGREDIENTS } from '../data/ingredients'

const FIRST_PAGE = INGREDIENTS.slice(0, 12)

describe('ingredient shelf — coordinate model', () => {
  it('renders exactly four shelf rows anchored by named data-shelf attributes', () => {
    render(<IngredientShelf items={FIRST_PAGE} selectedIds={[]} onToggle={() => {}} />)

    const rows = screen.getAllByTestId(/^shelf-row-/)
    expect(rows).toHaveLength(4)
    expect(rows.map((r) => r.getAttribute('data-shelf'))).toEqual(['1', '2', '3', '4'])

    // Rows carry no inline style — their position comes from centralized CSS
    // custom properties, never ad hoc per-item coordinates.
    for (const row of rows) {
      expect(row.getAttribute('style')).toBeNull()
      expect(row).toHaveClass('shelf__row')
    }
  })

  it('keeps all 12 visible items associated with exactly one shelf row', () => {
    render(<IngredientShelf items={FIRST_PAGE} selectedIds={[]} onToggle={() => {}} />)

    const rows = screen.getAllByTestId(/^shelf-row-/)
    const tilesPerRow = rows.map((r) => r.querySelectorAll('.shelf__tile').length)
    expect(tilesPerRow).toEqual([3, 3, 3, 3])

    const allTiles = document.querySelectorAll('.shelf__tile')
    expect(allTiles).toHaveLength(12)

    // Every tile lives inside exactly one shelf row (never floating free).
    for (const tile of allTiles) {
      expect(tile.closest('.shelf__row')).not.toBeNull()
    }
  })

  it('keeps selected and unselected tiles in the identical structural box', () => {
    const selectedId = FIRST_PAGE[0].id
    const otherId = FIRST_PAGE[1].id
    render(
      <IngredientShelf items={FIRST_PAGE} selectedIds={[selectedId]} onToggle={() => {}} />,
    )

    const selected = screen.getByTestId(`tile-${selectedId}`)
    const other = screen.getByTestId(`tile-${otherId}`)

    // Same base class and same inner structure regardless of selection state.
    for (const tile of [selected, other]) {
      expect(tile).toHaveClass('shelf__tile')
      expect(tile.querySelector('.shelf__tile-art')).not.toBeNull()
      expect(tile.querySelector('.shelf__tile-name')).not.toBeNull()
      // Geometry is identical: no inline style alters the box.
      expect(tile.getAttribute('style')).toBeNull()
    }

    // Only the selected tile gains the is-selected state + pressed semantics.
    expect(selected).toHaveClass('is-selected')
    expect(selected).toHaveAttribute('aria-pressed', 'true')
    expect(other).not.toHaveClass('is-selected')
    expect(other).toHaveAttribute('aria-pressed', 'false')
  })

  it('centralizes shelf positions in CSS custom properties (bottom-anchored, not old top bands)', () => {
    const css = readFileSync(resolve(process.cwd(), 'src/styles/global.css'), 'utf8')

    // Measured, full-image-percentage shelf anchors must be present.
    expect(css).toContain('--cavity-left: 9%')
    expect(css).toContain('--shelf-1-y: 36.20%')
    expect(css).toContain('--shelf-2-y: 51.69%')
    expect(css).toContain('--shelf-3-y: 69.27%')
    expect(css).toContain('--shelf-4-y: 85.16%')

    // Rows must be bottom-anchored to those named anchors...
    expect(css).toContain('bottom: calc(100% - var(--shelf-1-y)')
    expect(css).toContain('bottom: calc(100% - var(--shelf-2-y)')
    expect(css).toContain('bottom: calc(100% - var(--shelf-3-y)')
    expect(css).toContain('bottom: calc(100% - var(--shelf-4-y)')

    // ...and the old ad-hoc per-band top values must be gone from the shelf rows.
    expect(css).not.toContain('top: 17.2%')
    expect(css).not.toContain('top: 31.7%')
    expect(css).not.toContain('top: 53.5%')
    expect(css).not.toContain('top: 77.5%')
  })
})
