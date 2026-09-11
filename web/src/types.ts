/**
 * Frontend transport types.
 *
 * These mirror the backend Pydantic models (`src/creative_recipe/web/models.py`) one-to-one and
 * must stay aligned with the canonical CIE v3 contract:
 *   - six canonical dimension KEYS (never the old Stage-A/Stage-B names),
 *   - integer scores 1-5,
 *   - one direct six-dimension weighted total produced by the backend.
 * The frontend never recomputes the total.
 */

export type CuisineDirection = 'surprise-me' | 'chinese' | 'western' | 'fusion'
export type FlavorPreference = 'balanced' | 'savory' | 'spicy' | 'fresh' | 'rich'
export type TimePreference = 'any' | 'under-20' | 'under-40' | 'weekend'

export interface Preferences {
  cuisine: CuisineDirection
  flavor: FlavorPreference
  time: TimePreference
  /** Dietary needs or allergies (free text). */
  allergies: string
  /** Mood / craving notes (free text). */
  craving: string
}

export const DEFAULT_PREFERENCES: Preferences = {
  cuisine: 'fusion',
  flavor: 'balanced',
  time: 'any',
  allergies: '',
  craving: '',
}

/** The six canonical CIE v3 dimension keys, ordered by descending weight. */
export const CIE_DIMENSION_KEYS = [
  'innovation_delta_quality',
  'mechanistic_plausibility',
  'culinary_knowledge_grounding',
  'existing_culinary_precedent_analysis',
  'innovation_value',
  'realization_quality',
] as const

export type CieDimensionKey = (typeof CIE_DIMENSION_KEYS)[number]

/** Human-facing labels for the six canonical dimensions. */
export const CIE_DIMENSION_LABELS: Record<CieDimensionKey, string> = {
  culinary_knowledge_grounding: 'Culinary Knowledge Grounding',
  existing_culinary_precedent_analysis: 'Existing Culinary Precedent Analysis',
  innovation_delta_quality: 'Innovation Delta Quality',
  mechanistic_plausibility: 'Mechanistic Plausibility',
  innovation_value: 'Innovation Value',
  realization_quality: 'Realization Quality',
}

/** Short labels for compact meter rows. */
export const CIE_DIMENSION_SHORT: Record<CieDimensionKey, string> = {
  culinary_knowledge_grounding: 'Knowledge Grounding',
  existing_culinary_precedent_analysis: 'Precedent Analysis',
  innovation_delta_quality: 'Innovation Delta',
  mechanistic_plausibility: 'Mechanistic Plausibility',
  innovation_value: 'Innovation Value',
  realization_quality: 'Realization Quality',
}

export interface DimensionScore {
  key: string
  label: string
  weight: number
  score: number
  reason: string
  stage: string
  explanation: string
}

export interface CiePayload {
  total_score: number
  scale_min: number
  scale_max: number
  dimensions: DimensionScore[]
  stage_a_score: number
  stage_b_score: number
  weights: Record<string, number>
}

export interface TraceStageContent {
  key: string
  index: number
  label: string
  summary: string
  content: Record<string, unknown>
}

export interface TracePayload {
  stages: TraceStageContent[]
  creative_hypothesis: string | null
  risk_notes: string | null
}

export interface RecipeIngredient {
  name: string
  quantity: string | null
  note: string | null
}

export interface RecipePayload {
  name: string
  ingredients: RecipeIngredient[]
  seasonings: RecipeIngredient[]
  steps: string[]
  creative_explanation: string
  creative_hypothesis: string | null
  concept_name: string | null
  servings: string | null
  estimated_time: string | null
  difficulty: string | null
}

export interface ConceptPayload {
  name: string
  ingredients: string[]
  creative_angle: string
  core_idea: string
}

export interface GenerationMeta {
  provider: string
  demo_mode: boolean
  model: string
  requested_ingredients: string[]
  requested_preferences: Preferences
  concept_count: number
  recipe_count: number
  rank: number | null
}

export interface GenerateResponse {
  recipe: RecipePayload
  concept: ConceptPayload | null
  trace: TracePayload | null
  cie: CiePayload | null
  meta: GenerationMeta
}

export interface GenerateRequest {
  ingredients: string[]
  preferences: Preferences
  avoid?: string[]
  demo?: boolean
}

export interface HealthResponse {
  status: string
  demo_mode: boolean
  provider: string
  model: string
  ingredient_count: number
  scene_asset_count: number
  missing_ingredient_files: string[]
  missing_scene_files: string[]
}

/** A saved favorite (localStorage, versioned). */
export interface SavedRecipe {
  id: string
  savedAt: string
  title: string
  concept: string | null
  ingredientIds: string[]
  preferences: Preferences
  response: GenerateResponse
}
