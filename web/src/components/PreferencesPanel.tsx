import { SlidersHorizontal } from 'lucide-react'
import type { CuisineDirection, FlavorPreference, Preferences, TimePreference } from '../types'

interface Option<T extends string> {
  value: T
  label: string
}

const CUISINE: Option<CuisineDirection>[] = [
  { value: 'surprise-me', label: 'Surprise me' },
  { value: 'chinese', label: 'Chinese-inspired' },
  { value: 'western', label: 'Western-inspired' },
  { value: 'fusion', label: 'East–West Fusion' },
]

const FLAVOR: Option<FlavorPreference>[] = [
  { value: 'balanced', label: 'Balanced' },
  { value: 'savory', label: 'Savory' },
  { value: 'spicy', label: 'Spicy' },
  { value: 'fresh', label: 'Fresh' },
  { value: 'rich', label: 'Rich' },
]

const TIME: Option<TimePreference>[] = [
  { value: 'any', label: 'Any' },
  { value: 'under-20', label: 'Under 20 min' },
  { value: 'under-40', label: 'Under 40 min' },
  { value: 'weekend', label: 'Weekend project' },
]

interface PreferencesPanelProps {
  value: Preferences
  onChange: (next: Preferences) => void
}

/** Compact, friendly preference entry — deliberately not a long form. */
export function PreferencesPanel({ value, onChange }: PreferencesPanelProps) {
  return (
    <section className="card" aria-labelledby="prefs-title">
      <h2 className="card__title" id="prefs-title">
        <SlidersHorizontal aria-hidden="true" />
        A few preferences
      </h2>

      <div className="prefs__group">
        <div className="prefs__legend" id="cuisine-label">
          Cuisine direction
        </div>
        <div className="options" role="radiogroup" aria-labelledby="cuisine-label">
          {CUISINE.map((o) => (
            <button
              key={o.value}
              type="button"
              role="radio"
              className="option"
              aria-checked={value.cuisine === o.value}
              onClick={() => onChange({ ...value, cuisine: o.value })}
            >
              {o.label}
            </button>
          ))}
        </div>
      </div>

      <div className="prefs__group">
        <div className="prefs__legend" id="flavor-label">
          Flavor
        </div>
        <div className="options" role="radiogroup" aria-labelledby="flavor-label">
          {FLAVOR.map((o) => (
            <button
              key={o.value}
              type="button"
              role="radio"
              className="option"
              aria-checked={value.flavor === o.value}
              onClick={() => onChange({ ...value, flavor: o.value })}
            >
              {o.label}
            </button>
          ))}
        </div>
      </div>

      <div className="prefs__group">
        <div className="prefs__legend" id="time-label">
          Cooking time
        </div>
        <div className="options" role="radiogroup" aria-labelledby="time-label">
          {TIME.map((o) => (
            <button
              key={o.value}
              type="button"
              role="radio"
              className="option"
              aria-checked={value.time === o.value}
              onClick={() => onChange({ ...value, time: o.value })}
            >
              {o.label}
            </button>
          ))}
        </div>
      </div>

      <div className="prefs__group">
        <label className="prefs__legend" htmlFor="constraints">
          Anything else?
        </label>
        <textarea
          id="constraints"
          className="prefs__text"
          placeholder="Allergies, dietary needs, mood…"
          value={value.constraints}
          maxLength={400}
          onChange={(e) => onChange({ ...value, constraints: e.target.value })}
        />
      </div>
    </section>
  )
}
