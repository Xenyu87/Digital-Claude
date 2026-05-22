# Visual Testing

## Purpose

Playwright is used for dashboard-level visual checks that cannot be covered by Python smoke tests alone. The current target is the Lavagna React Flow board.

## Installed Tooling

- Package: `@playwright/test`
- Browser: Playwright Chromium
- Config: `playwright.config.js`
- Test folder: `tests/visual`
- Fixture project: `tests/fixtures/visual-blueprint-app`

## Setup Commands

```bash
npm install --save-dev @playwright/test
npx playwright install chromium
npx playwright install-deps chromium
```

`install-deps` is needed on minimal Linux hosts because Chromium requires system libraries such as `libnspr4`, `libnss3`, font packages, and X/GTK accessibility dependencies.

## Run Commands

```bash
npm run build:blueprint-flow
npm run test:visual
```

The Playwright config starts the dashboard server on `127.0.0.1:3102` with `scripts/serve_dashboard.py` and points it at the deterministic visual fixture. The fixture has a frontend component with four buttons and one chart so the scanner always produces component children for expand/collapse validation.

## Current Coverage

`tests/visual/blueprint-board.spec.js` verifies that:

- the dashboard opens and the Lavagna tab loads;
- the React Flow board is visible;
- the `Dettagli UI` controls are present;
- `Apri tutti` and `Chiudi tutti` change the visible node set without breaking the canvas;
- a screenshot is written to `reports/playwright-blueprint-board.png` for manual inspection.

## When To Add More

Add Playwright coverage when changing:

- React Flow node rendering, layout, or filters;
- Lavagna expand/collapse behavior;
- dashboard tabs or first-screen navigation;
- visual states that Python smoke tests cannot inspect.
