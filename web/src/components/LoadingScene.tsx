import { SCENE } from '../data/ingredients'
import { LOADING_MESSAGES } from '../hooks/useRecipeGeneration'

interface LoadingSceneProps {
  messageIndex: number
  onCancel?: () => void
}

const SPARKLE_POSITIONS = [
  { top: '6%', left: '12%', delay: '0s' },
  { top: '18%', left: '78%', delay: '0.4s' },
  { top: '52%', left: '4%', delay: '0.9s' },
  { top: '70%', left: '88%', delay: '1.3s' },
  { top: '34%', left: '92%', delay: '1.8s' },
  { top: '84%', left: '22%', delay: '2.1s' },
]

/** Generation / loading state. No fake percentage — just a restrained sparkle loop. */
export function LoadingScene({ messageIndex, onCancel }: LoadingSceneProps) {
  const message = LOADING_MESSAGES[messageIndex % LOADING_MESSAGES.length]

  return (
    <section className="loading" aria-labelledby="loading-title">
      <div className="loading__bowl">
        <img src={SCENE.mixingBowl} alt="A mixing bowl stirring itself" />
        <div className="sparkles" aria-hidden="true">
          {SPARKLE_POSITIONS.map((p, i) => (
            <span
              key={i}
              className="sparkle"
              style={{ top: p.top, left: p.left, animationDelay: p.delay }}
            >
              <svg viewBox="0 0 24 24" fill="currentColor">
                <path d="M12 0l2.2 7.3L21.5 9.5 14.2 12l1.1 7.6L12 15.7 4.7 19.6 5.8 12 .5 9.5l7.3-2.2z" />
              </svg>
            </span>
          ))}
        </div>
      </div>

      <h2 className="loading__title" id="loading-title">
        Making a little kitchen magic…
      </h2>
      <p className="loading__status" role="status" aria-live="polite" data-testid="loading-status">
        {message}
      </p>

      {onCancel && (
        <button type="button" className="btn btn--quiet" onClick={onCancel}>
          Cancel
        </button>
      )}
    </section>
  )
}
