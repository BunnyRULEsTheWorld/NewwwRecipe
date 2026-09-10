import { useState } from 'react'
import { Info } from 'lucide-react'
import type { CiePayload, DimensionScore } from '../types'

interface CieScorePanelProps {
  cie: CiePayload
}

function formatTotal(value: number): string {
  return Number.isFinite(value) ? value.toFixed(2) : '—'
}

/**
 * Accessible CIE presentation.
 *
 * The total is the backend's canonical direct six-dimension weighted sum — the frontend never
 * recomputes it. Numeric values are always shown, so colour is never the only channel.
 */
export function CieScorePanel({ cie }: CieScorePanelProps) {
  const [expanded, setExpanded] = useState<Record<string, boolean>>({})

  const dimensions: DimensionScore[] = cie.dimensions ?? []

  return (
    <section className="cie-card" aria-labelledby="cie-title" data-testid="cie-panel">
      <h2 className="card__title" id="cie-title">
        CIE quality check
      </h2>

      <p className="cie-total">
        <span className="cie-total__value" data-testid="cie-total">
          {formatTotal(cie.total_score)}
        </span>
        <span className="cie-total__scale">
          / {cie.scale_max}
        </span>
      </p>
      <p className="cie-total__caption">
        Weighted total across the six canonical CIE dimensions (1–5 scale).
      </p>

      <div className="cie-meters">
        {dimensions.map((dim) => {
          const pct = ((dim.score - cie.scale_min) / (cie.scale_max - cie.scale_min)) * 100
          const isOpen = Boolean(expanded[dim.key])
          return (
            <div key={dim.key} data-testid={`cie-dim-${dim.key}`}>
              <div className="meter__head">
                <span className="meter__label">{dim.label}</span>
                <span className="meter__weight">{Math.round(dim.weight * 100)}%</span>
                <span className="meter__score">
                  {dim.score} / {cie.scale_max}
                </span>
              </div>
              <div
                className="meter__track"
                role="meter"
                aria-valuenow={dim.score}
                aria-valuemin={cie.scale_min}
                aria-valuemax={cie.scale_max}
                aria-label={`${dim.label}: ${dim.score} out of ${cie.scale_max}, weight ${Math.round(
                  dim.weight * 100,
                )} percent`}
              >
                <div className="meter__fill" style={{ width: `${pct}%` }} />
                <div className="meter__ticks" aria-hidden="true">
                  <span className="meter__tick" />
                  <span className="meter__tick" />
                  <span className="meter__tick" />
                  <span className="meter__tick" />
                  <span className="meter__tick" />
                </div>
              </div>
              <button
                type="button"
                className="meter__help"
                aria-expanded={isOpen}
                onClick={() => setExpanded((prev) => ({ ...prev, [dim.key]: !prev[dim.key] }))}
              >
                <Info
                  aria-hidden="true"
                  style={{ width: 13, height: 13, verticalAlign: '-2px', marginRight: 4 }}
                />
                What this measures
              </button>
              {isOpen && (
                <>
                  <p className="meter__reason">{dim.explanation}</p>
                  <p className="meter__reason">
                    <strong>Why this score: </strong>
                    {dim.reason}
                  </p>
                </>
              )}
            </div>
          )
        })}
      </div>

      <p className="cie-note">
        CIE judges the idea and the written plan, not a cooked dish. Realization Quality is a
        plan-level estimate and is capped at 4 — level 5 is reserved for a future empirical
        pipeline.
      </p>
    </section>
  )
}
