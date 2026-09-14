import { createReadStream, existsSync } from 'node:fs'
import { cp } from 'node:fs/promises'
import path from 'node:path'
import { fileURLToPath } from 'node:url'
import type { Plugin } from 'vite'
import react from '@vitejs/plugin-react'
import { defineConfig } from 'vitest/config'

const _dirname = path.dirname(fileURLToPath(import.meta.url))

/** Repository root (one level above `web/`). */
const repoRoot = path.resolve(_dirname, '..')

/**
 * Illustration directories live at the repository root and are shared with the Python backend.
 * They are served under the SAME url prefixes in dev and in the production build, so no asset is
 * ever duplicated or recompressed:
 *
 *   /ingredients/<file>.png  ->  <repo>/ingredient/<file>.png
 *   /scene/<file>.png        ->  <repo>/fronted asset/<file>.png
 *
 * In dev a tiny middleware streams them from disk; at build time they are copied verbatim into
 * `dist/`. FastAPI mounts the same prefixes, so the built bundle also works behind the backend.
 */
function repoIllustrationAssets(): Plugin {
  const mappings = [
    { prefix: '/ingredients/', dir: path.resolve(repoRoot, 'ingredient') },
    { prefix: '/scene/', dir: path.resolve(repoRoot, 'fronted asset') },
  ]
  let outDir = path.resolve(_dirname, 'dist')

  return {
    name: 'newwwrecipe-repo-illustrations',

    configResolved(config) {
      outDir = path.resolve(config.root, config.build.outDir)
    },

    configureServer(server) {
      server.middlewares.use((req, res, next) => {
        const url = (req.url || '').split('?')[0]
        for (const m of mappings) {
          if (!url.startsWith(m.prefix)) continue
          const rel = decodeURIComponent(url.slice(m.prefix.length))
          // Never allow path traversal outside the mapped directory.
          if (rel.includes('..') || rel.includes('/') || rel.includes('\\')) {
            res.statusCode = 403
            res.end('Forbidden')
            return
          }
          const file = path.resolve(m.dir, rel)
          if (file !== path.join(m.dir, rel) || !existsSync(file)) {
            res.statusCode = 404
            res.end('Not found')
            return
          }
          res.setHeader('Content-Type', 'image/png')
          res.setHeader('Cache-Control', 'no-cache')
          createReadStream(file).pipe(res)
          return
        }
        next()
      })
    },

    async closeBundle() {
      if (process.env.VITEST) return
      for (const m of mappings) {
        if (!existsSync(m.dir)) continue
        await cp(m.dir, path.resolve(outDir, m.prefix.replace(/\//g, '')), { recursive: true })
      }
    },
  }
}

const BACKEND = process.env.NEWWWRECIPE_API ?? 'http://127.0.0.1:8000'

export default defineConfig({
  plugins: [react(), repoIllustrationAssets()],
  server: {
    host: '127.0.0.1',
    port: 5173,
    strictPort: false,
    proxy: {
      // No proxy timeout: the /api/recipes/generate call can take several minutes for a real
      // Hy3 (reasoning-class) generation, and a default 120s proxyTimeout would abort it.
      '/api': { target: BACKEND, changeOrigin: true, timeout: 0, proxyTimeout: 0 },
    },
  },
  preview: {
    port: 4173,
    proxy: {
      '/api': { target: BACKEND, changeOrigin: true, timeout: 0, proxyTimeout: 0 },
    },
  },
  build: {
    outDir: 'dist',
    emptyOutDir: true,
    sourcemap: false,
  },
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: ['./src/test/setup.ts'],
    css: true,
    include: ['src/**/*.{test,spec}.{ts,tsx}'],
    restoreMocks: true,
  },
})
