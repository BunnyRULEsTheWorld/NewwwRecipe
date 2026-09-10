# NewwwRecipe — Interactive Fridge Frontend

React + TypeScript + Vite frontend for the NewwwRecipe creative-recipe pipeline.

## Commands

```bash
npm install          # install dependencies
npm run dev          # start Vite dev server (http://127.0.0.1:5173/)
npm run build        # production build (outputs dist/)
npm run typecheck    # TypeScript --noEmit
npm run lint         # ESLint
npm test             # Vitest unit tests
```

## Development proxy

`vite.config.ts` proxies `/api`, `/ingredients`, and `/scene` to the FastAPI backend at `http://127.0.0.1:8000`. Start the backend first, then run `npm run dev`.

## Asset strategy

- `ingredient/` (project root) — 65 PNG cutouts.
- `fronted asset/` (project root) — scene illustrations.

In development the Vite dev server rewrites requests for these paths to the backend static mounts. In production the FastAPI app serves `web/dist/` directly and uses `staticfiles` mounts for `/ingredients` and `/scene`, so the same URLs work without duplicating assets.

## Key packages

- `lucide-react` — small SVG icon set.
- No large component library; all styles are hand-written CSS variables in `src/styles/` to keep the picture-book look.

## Accessibility

- Semantic `<button>` controls, visible focus rings.
- `aria-live` status for generation.
- Reduced-motion support respects `prefers-reduced-motion`.
- Numeric CIE scores shown alongside meters (colour is never the only channel).
