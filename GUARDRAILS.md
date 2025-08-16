# Guardrails

This repository hosts the **blackroad-io** front‑end project. Development is coordinated across ten feature branches (`feature/agent-01` … `feature/agent-10`).

## File scope map
Each agent may only touch the files listed for their scope.

| Agent | Scope |
|-------|-------|
|1|project scaffold, config, brand tokens: `lib/brand.ts`, `app/layout.tsx`, `app/globals.css`, config files, `components/Logo.tsx`|
|2|UI kit and utilities: `components/ui/*`, `components/Topbar.tsx`, `hooks/*`, `lib/seo.ts`, `app/(dev)/ui/*`|
|3|Hub: `app/(public)/page.tsx`|
|4|Login page: `app/login/page.tsx` (+ tiny util) |
|5|CoCode IDE: `app/cocode/page.tsx` (+ tiny local components) |
|6|Placeholder portals: `app/roadview/page.tsx`, `app/roadcoin/page.tsx`, `app/roadchain/page.tsx`, `app/roadie/page.tsx`, `app/lucidia/page.tsx`, `app/codex/page.tsx`|
|7|Topbar: `components/Topbar.tsx` and minimal edit to `app/layout.tsx`|
|8|A11Y/SEO: route metadata, `public/robots.txt`, `public/sitemap.xml`, `public/og-default.png`, minor a11y fixes|
|9|DX/README: `package.json` scripts, lint/prettier ignores, `README.md`, optional `.github/workflows/lint.yml`|
|10|Integration & smoke tests: `tests/smoke.md`, `scripts/health-check.js`, `MERGE_PLAN.md`|

## Merge policy
* Branch naming: `feature/agent-XX`.
* Auto‑merge if PR adds new files only or edits only in additive way.
* `package.json` script additions are merged by union; conflicting values keep Agent 9’s value and append the alternative as a comment.
* `tailwind.config.ts` plugin/content arrays merged by union.
* `app/layout.tsx`: keep Agent 1 base; append Topbar import and usage from Agent 7 under existing imports and above `{children}`.
* `app/globals.css`: append new CSS variable blocks; existing tokens from Agent 1 remain unchanged.
* UI components live under unique file names to avoid collisions.
* Conflicts that cannot be auto‑resolved are documented in `CONFLICT.md` with exact hunks and suggested resolution.

## Acceptance gates
* `npm run build` succeeds.
* `npm run lint` and `npm run typecheck` succeed.
* `/login` Lighthouse accessibility ≥ 90.
* `/cocode` responsive and keyboard accessible.
* All six placeholder portals exist and link back to the hub.
* Topbar visible and mobile menu keyboard navigable.
* `node scripts/health-check.js` returns 200 for `/` and `/login`.

