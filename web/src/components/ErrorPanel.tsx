import { AlertTriangle, RefreshCw } from 'lucide-react'

interface ErrorPanelProps {
  message: string
  onRetry: () => void
  onBack: () => void
}

/** Error + retry state. The backend message is shown verbatim; nothing is invented. */
export function ErrorPanel({ message, onRetry, onBack }: ErrorPanelProps) {
  return (
    <section className="error-panel" role="alert" aria-labelledby="error-title">
      <div className="error-card">
        <AlertTriangle className="error-card__icon" aria-hidden="true" />
        <h1 className="error-card__title" id="error-title">
          The kitchen could not finish that one
        </h1>
        <p className="error-card__text">
          Nothing was invented to cover it up — here is what actually came back.
        </p>
        <pre className="error-card__detail">{message}</pre>
        <div className="error-card__actions">
          <button type="button" className="btn btn--primary" onClick={onRetry}>
            <RefreshCw className="btn__icon" aria-hidden="true" />
            Try again
          </button>
          <button type="button" className="btn btn--ghost" onClick={onBack}>
            Back to the fridge
          </button>
        </div>
      </div>
    </section>
  )
}
