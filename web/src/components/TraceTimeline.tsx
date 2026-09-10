import { ChevronRight } from 'lucide-react'
import type { TracePayload, TraceStageContent } from '../types'

interface TraceTimelineProps {
  trace: TracePayload
}

/** Human label for a raw trace field key (snake_case -> Title Case). */
function fieldLabel(key: string): string {
  return key.replace(/_/g, ' ')
}

function isPrimitive(value: unknown): boolean {
  return typeof value === 'string' || typeof value === 'number' || typeof value === 'boolean'
}

function renderList(items: unknown[]): string {
  return items.map((i) => (typeof i === 'string' ? i : JSON.stringify(i))).join(', ')
}

/** Renders one stage body without ever dumping raw JSON at the user. */
function StageBody({ stage }: { stage: TraceStageContent }) {
  const entries = Object.entries(stage.content)

  return (
    <div className="trace__body">
      {entries.map(([key, value]) => {
        if (value === null || value === undefined || value === '') return null

        if (Array.isArray(value)) {
          const objects = value.filter(
            (v) => v && typeof v === 'object' && !Array.isArray(v),
          ) as Record<string, unknown>[]
          if (objects.length > 0) {
            return (
              <div key={key} className="trace__row">
                <div className="trace__key">{fieldLabel(key)}</div>
                <ul>
                  {objects.map((obj, i) => (
                    <li key={i} className="trace__value">
                      {Object.entries(obj)
                        .filter(([, v]) => v !== null && v !== undefined && v !== '')
                        .map(([k, v]) => (
                          <span key={k}>
                            <strong>{fieldLabel(k)}: </strong>
                            {String(v)}{' '}
                          </span>
                        ))}
                    </li>
                  ))}
                </ul>
              </div>
            )
          }
          return (
            <div key={key} className="trace__row">
              <div className="trace__key">{fieldLabel(key)}</div>
              <div className="trace__value">{renderList(value)}</div>
            </div>
          )
        }

        if (typeof value === 'object') {
          return (
            <div key={key} className="trace__row">
              <div className="trace__key">{fieldLabel(key)}</div>
              {Object.entries(value as Record<string, unknown>)
                .filter(([, v]) => v !== null && v !== undefined && v !== '')
                .map(([k, v]) => (
                  <div key={k} className="trace__value">
                    <strong>{fieldLabel(k)}: </strong>
                    {Array.isArray(v) ? renderList(v) : String(v)}
                  </div>
                ))}
            </div>
          )
        }

        if (!isPrimitive(value)) return null
        return (
          <div key={key} className="trace__row">
            <div className="trace__key">{fieldLabel(key)}</div>
            <div className="trace__value">{String(value)}</div>
          </div>
        )
      })}
    </div>
  )
}

/** The canonical six-stage Innovation Trace as an expandable vertical timeline. */
export function TraceTimeline({ trace }: TraceTimelineProps) {
  if (!trace.stages.length) return null

  return (
    <section className="trace" aria-labelledby="trace-title" data-testid="trace-timeline">
      <h3 className="section__title" id="trace-title">
        Innovation Trace
      </h3>
      <ol>
        {trace.stages.map((stage) => (
          <li key={stage.key} className="trace__item">
            <span className="trace__dot" aria-hidden="true">
              {stage.index}
            </span>
            <details>
              <summary className="trace__toggle">
                <ChevronRight aria-hidden="true" />
                <span>{stage.label}</span>
                <span className="trace__summary">{stage.summary}</span>
              </summary>
              <StageBody stage={stage} />
            </details>
          </li>
        ))}
      </ol>
    </section>
  )
}
