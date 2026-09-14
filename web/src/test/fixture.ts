import type { GenerateResponse, HealthResponse } from '../types'

/**
 * Canonical CIE v3 fixture mirroring the backend response shape.
 * Six dimension keys, integer scores 1-5, six trace stages.
 */
export const HEALTH: HealthResponse = {
  status: 'ok',
  demo_mode: true,
  provider: 'demo',
  model: 'demo-offline',
  ingredient_count: 65,
  scene_asset_count: 8,
  missing_ingredient_files: [],
  missing_scene_files: [],
}

export function makeResponse(title = 'Coffee-Braised Chicken with Melted Cheese Crust'): GenerateResponse {
  return {
    recipe: {
      name: title,
      ingredients: [
        { name: 'Chicken', quantity: '200g', note: null },
        { name: 'Coffee', quantity: '1 cup', note: null },
        { name: 'Cheese', quantity: '1 cup', note: null },
      ],
      seasonings: [
        { name: 'salt', quantity: 'to taste', note: null },
        { name: 'black pepper', quantity: 'to taste', note: null },
      ],
      steps: [
        'Pat the chicken dry, season it with salt and black pepper, and let it stand for 5 minutes.',
        'Heat a small oven-safe skillet over medium-high heat, add a little oil, and sear the chicken about 2 minutes per side.',
        'Lower the heat, add the brewed coffee gradually, cover, and simmer gently for 8-10 minutes.',
        'Uncover, spoon the liquid over the chicken, and cook until the thickest part reaches 74 C / 165 F.',
        'Sprinkle the cheese over the chicken and broil briefly for 1-2 minutes until melted and bubbling.',
        'Rest for 3 minutes before serving.',
      ],
      creative_explanation:
        'Coffee replaces wine as the braising liquid, then a cheese crust finishes the dish.',
      creative_hypothesis:
        'Replace wine/stock with coffee as the braise liquid, then cap with melted cheese.',
      concept_name: 'coffee-braise',
      servings: null,
      estimated_time: null,
      difficulty: null,
    },
    concept: {
      name: 'coffee-braise',
      ingredients: ['chicken', 'coffee', 'cheese'],
      creative_angle: 'Coffee as a savory braising liquid, finished with a bubbling cheese crust.',
      core_idea: 'Slow-braise chicken in strong black coffee, then broil under cheese.',
    },
    trace: {
      stages: [
        {
          key: 'existing_culinary_context',
          index: 1,
          label: 'Existing Culinary Context',
          summary: 'What already exists that this idea departs from.',
          content: {
            precedents: ['coq au vin (wine-braised chicken)', 'coffee-rubbed brisket'],
            relationship: 'Inherits the braise template but swaps wine for coffee.',
          },
        },
        {
          key: 'ingredient_and_technique_knowledge',
          index: 2,
          label: 'Ingredient & Technique Knowledge',
          summary: 'The ingredient and technique knowledge it leans on.',
          content: {
            ingredient_knowledge: [
              { ingredient: 'chicken', property: 'collagen converts to gelatin when slow-cooked' },
            ],
            technique_knowledge: [
              { technique: 'braising', principle: 'low moist heat dissolves collagen' },
            ],
          },
        },
        {
          key: 'innovation_delta',
          index: 3,
          label: 'Innovation Delta',
          summary: 'The concrete before → after change.',
          content: {
            before: 'Chicken braised in wine/stock.',
            after: 'Chicken braised in reduced black coffee.',
            change_type: ['ingredient substitution', 'flavor architecture'],
            magnitude: 3,
          },
        },
        {
          key: 'mechanistic_justification',
          index: 4,
          label: 'Mechanistic Justification',
          summary: 'Why the change should work, in cooking terms.',
          content: {
            flavor_mechanism: 'Roast pyrazines echo toasted wine-reduction notes.',
            texture_mechanism: 'Collagen-to-gelatin keeps the meat succulent.',
            chemical_or_culinary_basis: 'Maillard plus pyrazine bitterness; remains unproven.',
            strength: 'medium',
          },
        },
        {
          key: 'creative_hypothesis',
          index: 5,
          label: 'Creative Hypothesis',
          summary: 'The novel idea being proposed.',
          content: { text: 'Replace stock with coffee, then cap with melted cheese.' },
        },
        {
          key: 'risk_and_constraint',
          index: 6,
          label: 'Risk & Constraint',
          summary: 'What could fail, what is traded away, and how to judge failure.',
          content: {
            risk: 'Coffee turns acrid if reduced too hard.',
            tradeoff: 'Loses the bright acidity wine gives.',
            failure_condition: 'The braising liquid reduces to a burnt-bitter syrup.',
          },
        },
      ],
      creative_hypothesis: 'Replace stock with coffee, then cap with melted cheese.',
      risk_notes:
        'Risk: Coffee turns acrid if reduced too hard. Tradeoff: Loses the bright acidity wine gives. Failure condition: The braising liquid reduces to a burnt-bitter syrup.',
    },
    cie: {
      total_score: 4.25,
      scale_min: 1,
      scale_max: 5,
      dimensions: [
        {
          key: 'innovation_delta_quality',
          label: 'Innovation Delta Quality',
          weight: 0.25,
          score: 5,
          reason: 'A concrete, well-specified change.',
          stage: 'A',
          explanation: 'Is the actual change meaningful?',
        },
        {
          key: 'mechanistic_plausibility',
          label: 'Mechanistic Plausibility',
          weight: 0.2,
          score: 4,
          reason: 'Mechanisms are named but partly unproven.',
          stage: 'A',
          explanation: 'Is there a real cooking mechanism?',
        },
        {
          key: 'culinary_knowledge_grounding',
          label: 'Culinary Knowledge Grounding',
          weight: 0.15,
          score: 4,
          reason: 'Ingredient knowledge is accurate with limits.',
          stage: 'A',
          explanation: 'Does it use real ingredient knowledge?',
        },
        {
          key: 'existing_culinary_precedent_analysis',
          label: 'Existing Culinary Precedent Analysis',
          weight: 0.15,
          score: 4,
          reason: 'Precedents are specific and correct.',
          stage: 'A',
          explanation: 'Are the closest existing dishes identified?',
        },
        {
          key: 'innovation_value',
          label: 'Innovation Value',
          weight: 0.15,
          score: 4,
          reason: 'Worth trying beyond novelty.',
          stage: 'A',
          explanation: 'Is the exploration worth trying?',
        },
        {
          key: 'realization_quality',
          label: 'Realization Quality',
          weight: 0.1,
          score: 4,
          reason: 'Plan is complete and consistent. [plan-level cap]',
          stage: 'B',
          explanation: 'Plan-level completeness and cookability.',
        },
      ],
      stage_a_score: 4.25,
      stage_b_score: 4,
      weights: {
        culinary_knowledge_grounding: 0.15,
        existing_culinary_precedent_analysis: 0.15,
        innovation_delta_quality: 0.25,
        mechanistic_plausibility: 0.2,
        innovation_value: 0.15,
        realization_quality: 0.1,
      },
    },
    meta: {
      provider: 'demo',
      demo_mode: true,
      model: 'demo-offline',
      requested_ingredients: ['chicken', 'coffee', 'cheese'],
      requested_preferences: {
        cuisine: 'fusion',
        flavor: 'balanced',
        time: 'any',
        allergies: '',
        craving: '',
      },
      concept_count: 3,
      recipe_count: 1,
      rank: 1,
    },
  }
}

export interface CapturedRequest {
  url: string
  init?: RequestInit
  body?: unknown
}

/** Installs a fake fetch for /api/* and records POST bodies. */
export function installApiMock(options: {
  generate?: GenerateResponse | (() => GenerateResponse)
  fail?: { status: number; detail: string }
  captured: CapturedRequest[]
}) {
  const fetchMock = async (input: RequestInfo | URL, init?: RequestInit) => {
    const url = typeof input === 'string' ? input : String(input)
    if (url.includes('/api/health')) {
      return new Response(JSON.stringify(HEALTH), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      })
    }
    if (url.includes('/api/recipes/generate')) {
      const body = init?.body ? JSON.parse(String(init.body)) : undefined
      options.captured.push({ url, init, body })
      if (options.fail) {
        return new Response(JSON.stringify({ detail: options.fail.detail }), {
          status: options.fail.status,
          headers: { 'Content-Type': 'application/json' },
        })
      }
      const payload =
        typeof options.generate === 'function' ? options.generate() : (options.generate ?? makeResponse())
      return new Response(JSON.stringify(payload), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      })
    }
    return new Response('Not found', { status: 404 })
  }

  globalThis.fetch = fetchMock as unknown as typeof fetch
  return fetchMock
}

/** Force reduced motion so the fridge opens synchronously in tests. */
export function forceReducedMotion() {
  window.matchMedia = ((query: string) => ({
    matches: query.includes('prefers-reduced-motion'),
    media: query,
    onchange: null,
    addListener: () => {},
    removeListener: () => {},
    addEventListener: () => {},
    removeEventListener: () => {},
    dispatchEvent: () => false,
  })) as unknown as typeof window.matchMedia
}
