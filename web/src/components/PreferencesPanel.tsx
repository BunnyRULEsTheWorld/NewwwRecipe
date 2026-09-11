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

/**
 * Compact preference entry — deliberately not a long form. Two free-text fields are kept separate
 * (allergies vs. craving) and surfaced to the backend as a single `constraints` string.
 */
export function PreferencesPanel({ value, onChange }: PreferencesPanelProps) {
  return (
    <section className="prefs" aria-labelledby="prefs-title">
      <h2 className="prefs__title" id="prefs-title">
        <SlidersHorizontal aria-hidden="true" />
        A few preferences
      </h2>

      <fieldset className="prefs__group">
        <legend className="prefs__legend">Cuisine direction</legend>
        <div className="options options--wrap" role="radiogroup" aria-labelledby="prefs-title">
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
      </fieldset>

      <fieldset className="prefs__group">
        <legend className="prefs__legend">Flavor</legend>
        <div className="options options--wrap" role="radiogroup" aria-labelledby="prefs-title">
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
      </fieldset>

      <fieldset className="prefs__group">
        <legend className="prefs__legend">Cooking time</legend>
        <div className="options options--wrap" role="radiogroup" aria-labelledby="prefs-title">
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
      </fieldset>

      <fieldset className="prefs__group">
        <legend className="prefs__legend">Dietary needs or allergies</legend>
        <textarea
          id="prefs-allergies"
          className="prefs__text"
          aria-label="Dietary needs or allergies"
          placeholder="Vegetarian, nut allergy, lactose-free…"
          value={value.allergies}
          maxLength={400}
          onChange={(e) => onChange({ ...value, allergies: e.target.value })}
        />
      </fieldset>

      <fieldset className="prefs__group">
        <legend className="prefs__legend">What are you craving?</legend>
        <textarea
          id="prefs-craving"
          className="prefs__text"
          aria-label="What are you craving?"
          placeholder="Something cozy, light, adventurous…"
          value={value.craving}
          maxLength={400}
          onChange={(e) => onChange({ ...value, craving: e.target.value })}
        />
      </fieldset>

      <p className="prefs__safety">
        Please verify ingredients carefully if you have a severe allergy.
      </p>
    </section>
  )
}
