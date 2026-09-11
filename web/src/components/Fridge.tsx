import type { ReactNode } from 'react'
import { SCENE } from '../data/ingredients'

export type FridgeFrame = 'closed' | 'ajar' | 'open'

interface FridgeProps {
  frame: FridgeFrame
  /** When true the fridge itself is the interactive control (landing state). */
  interactive: boolean
  onActivate?: () => void
  /** Overlay rendered inside the open refrigerator cavity (the ingredient shelf). */
  children?: ReactNode
}

function frameClass(kind: FridgeFrame, frame: FridgeFrame): string {
  return `fridge-frame fridge-frame--${kind}${frame === kind ? ' is-active' : ''}`
}

/**
 * The refrigerator.
 *
 * All three frames are always mounted so they are preloaded. They share one
 * bottom-centre anchor, which keeps the closed → ajar → open sequence free of
 * any visible jump. The ingredient overlay is clipped to the interior cavity
 * and only reachable once the fridge is open.
 */
export function Fridge({ frame, interactive, onActivate, children }: FridgeProps) {
  const isOpen = frame === 'open'
  const interiorVisible = frame === 'open' || frame === 'ajar'

  const frames = (
    <>
      <img
        className={frameClass('closed', frame)}
        src={SCENE.fridgeClosed}
        alt={frame === 'closed' ? 'A closed refrigerator' : ''}
        draggable={false}
      />
      <img
        className={frameClass('ajar', frame)}
        src={SCENE.fridgeAjar}
        alt=""
        draggable={false}
      />
      <img
        className={frameClass('open', frame)}
        src={SCENE.fridgeOpen}
        alt={isOpen ? 'An open refrigerator with empty shelves' : ''}
        draggable={false}
      />
      <div
        className={`fridge__interior${interiorVisible ? ' is-visible' : ''}`}
        aria-hidden={!isOpen}
      >
        {children}
      </div>
    </>
  )

  if (!interactive) {
    return (
      <div className="fridge-button is-open" data-testid="fridge-open">
        {frames}
      </div>
    )
  }

  return (
    <button
      type="button"
      className="fridge-button"
      data-testid="fridge-button"
      aria-label="Open the fridge and choose ingredients"
      onClick={onActivate}
    >
      {frames}
    </button>
  )
}
