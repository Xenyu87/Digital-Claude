const { test, expect } = require('@playwright/test');

test('Blueprint board exposes expandable UI details', async ({ page }) => {
  await page.goto('/reports/skill-dashboard.html');
  await page.getByRole('button', { name: 'Lavagna' }).click();

  const board = page.locator('.bf-shell');
  await expect(board).toBeVisible();
  await expect(page.getByText('Dettagli UI')).toBeVisible();

  const visibleBefore = await page.locator('.react-flow__node:visible').count();
  await page.getByRole('button', { name: 'Apri tutti' }).click();
  await expect(page.locator('.bf-node-toggle').first()).toBeVisible();
  const visibleAfterOpen = await page.locator('.react-flow__node:visible').count();
  expect(visibleAfterOpen).toBeGreaterThanOrEqual(visibleBefore);

  await page.getByRole('button', { name: 'Chiudi tutti' }).click();
  const visibleAfterClose = await page.locator('.react-flow__node:visible').count();
  expect(visibleAfterClose).toBeLessThanOrEqual(visibleAfterOpen);

  await page.screenshot({ path: 'reports/playwright-blueprint-board.png', fullPage: true });
});
