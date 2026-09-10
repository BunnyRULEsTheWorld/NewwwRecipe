import type { ReactNode } from 'react'
import { SCENE } from '../data/ingredients'

export type FridgeFrame = 'closed' | 'ajar' | 'open'

interface FridgeProps {
  frame: FridgeFrame
  /** When true the fridge is a real button (landing state). */
  interactive: boolean
  onActivate?: () => void
  /** Overlay rendered inside the open fridge (the ingredient shelf). */
  children?: ReactNode
}

function frameClass(kind: FridgeFrame, frame: FridgeFrame): string {
  return `fridge-frame fridge-frame--${kind}${frame === kind ? ' is-active' : ''}`
}

/**
 * The refrigerator. All three frames are always mounted (so they are preloaded) and share one
 * bottom-centre anchor, which keeps the closed -> ajar -> open sequence free of any jump.
 */
export function Fridge({ frame, interactive, onActivate, children }: FridgeProps) {
  const openImg = (
    <img
      className={frameClass('open', frame)}
      src={SCENE.fridgeOpen}
      alt={frame === 'open' ? 'An open refrigerator with empty shelves' : ''}
      draggable={false}
    />
  )

  if (!interactive) {
    return (
      <div className="fridge-button is-open" data-testid="fridge-open">
        <img className={frameClass('closed', frame)} src={SCENE.fridgeClosed} alt="" draggable={false} />
        <img className={frameClass('ajar', frame)} src={SCENE.fridgeAjar} alt="" draggable={false} />
        {openImg}
        {children}
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
      <img
        className={frameClass('closed', frame)}
        src={SCENE.fridgeClosed}
        alt={frame === 'closed' ? 'A closed refrigerator' : ''}
        draggable={false}
      />
      <img className={frameClass('ajar', frame)} src={SCENE.fridgeAjar} alt="" draggable={false} />
      {openImg}
      {children}
    </button>
  )
}
