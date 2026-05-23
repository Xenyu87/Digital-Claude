const { test, expect } = require('@playwright/test');

test('Blueprint board exposes expandable UI details', async ({ page }) => {
  await page.goto('/reports/skill-dashboard.html');
  await page.getByRole('button', { name: 'Lavagna' }).click();

  const board = page.locator('.bf-shell');
  await expect(board).toBeVisible();
  await expect(page.getByText('Dettagli UI')).toBeVisible();
  const preview = page.frameLocator('iframe[title="Preview frontend progetto"]');
  await expect(preview.getByText('Preview frontend generata')).toBeVisible();

  const visibleBefore = await page.locator('.react-flow__node:visible').count();
  await page.getByRole('button', { name: 'Tutto' }).click();
  await page.getByRole('button', { name: 'Apri tutti' }).click();
  await expect(page.locator('.bf-node-toggle').first()).toBeVisible();
  const parentNode = page.locator('.react-flow__node:has-text("Screen/Component: AdminDashboard")').first();
  const childNode = page.locator('.react-flow__node:has-text("Button: Salva ordine")').first();
  await expect(parentNode).toBeVisible();
  await expect(childNode).toBeVisible();
  const parentBox = await parentNode.boundingBox();
  const childBox = await childNode.boundingBox();
  expect(parentBox).not.toBeNull();
  expect(childBox).not.toBeNull();
  expect(childBox.x).toBeGreaterThan(parentBox.x + 40);
  expect(Math.abs(childBox.y - parentBox.y)).toBeLessThan(260);
  await page.locator('[data-id="button-salva-ordine"]').evaluate((element) => {
    element.dispatchEvent(new MouseEvent('click', { bubbles: true, cancelable: true }));
  });
  await expect(preview.locator('.is-highlighted').filter({ hasText: 'Button: Salva ordine' })).toBeVisible();
  await preview.getByRole('button', { name: /Button: Apri report/ }).click();
  await expect(page.locator('.bf-detail h3')).toContainText('Button: Apri report');
  const visibleAfterOpen = await page.locator('.react-flow__node:visible').count();
  expect(visibleAfterOpen).toBeGreaterThanOrEqual(visibleBefore);

  await page.getByRole('button', { name: 'Chiudi tutti' }).click();
  const visibleAfterClose = await page.locator('.react-flow__node:visible').count();
  expect(visibleAfterClose).toBeLessThanOrEqual(visibleAfterOpen);

  await page.screenshot({ path: 'reports/playwright-blueprint-board.png', fullPage: true });
});
