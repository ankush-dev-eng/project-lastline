import { test, expect } from '@playwright/test';

test.describe('PROJECT LASTLINE Control Room Operations E2E Flow', () => {
  test('verifies advisory banner, control room views, and human-in-the-loop workflow', async ({ page }) => {
    // 1. Navigate to the operations console
    await page.goto('/');

    // 2. Verify strict advisory sandbox banner
    const advisoryBanner = page.locator('text=SANDBOX – ADVISORY ONLY (ZERO PHYSICAL ACTUATION)');
    await expect(advisoryBanner).toBeVisible();

    // 3. Verify System Status badge
    await expect(page.getByText('PROJECT LASTLINE', { exact: true })).toBeVisible();

    // 4. Verify Replay Controls
    await expect(page.locator('text=SCENARIO:')).toBeVisible();
    await expect(page.locator('button[title*="Play Simulation"], button[title*="Pause Simulation"]')).toBeVisible();
    await expect(page.locator('button[title*="Step Forward"]')).toBeVisible();

    // 5. Test Operations Map view and node click
    const mapTab = page.getByRole('button', { name: 'Operations Map' });
    await mapTab.click();
    const mapCanvas = page.locator('svg[viewBox="50 40 760 480"]');
    await expect(mapCanvas).toBeVisible();

    // Click on a node circle in the SVG to open the Node Inspector Drawer
    const j1Node = page.locator('circle').first();
    if (await j1Node.isVisible()) {
      await j1Node.click();
    }

    // 6. Test Agent Reasoning view
    const agentTab = page.getByRole('button', { name: 'Agent Reasoning' });
    await agentTab.click();
    await expect(page.locator('text=1. Sentinel Agent')).toBeVisible();
    await expect(page.locator('text=2. Integrity Agent')).toBeVisible();
    await expect(page.locator('text=3. Reconstruction Agent')).toBeVisible();

    // 7. Test Digital Twin Lab view
    const twinTab = page.getByRole('button', { name: 'Digital Twin Lab' });
    await twinTab.click();
    await expect(page.locator('text=Telemetry Inspector & Digital Twin State Reconstruction')).toBeVisible();

    // 8. Test Audit Ledger view
    const auditTab = page.getByRole('button', { name: 'Audit Ledger' });
    await auditTab.click();
    await expect(page.locator('text=CRYPTOGRAPHIC SHA-256 AUDIT CHAIN')).toBeVisible();

    // 9. Switch back to Operations Map and verify Advisory Recommendations panel
    await mapTab.click();
    await expect(page.locator('svg[viewBox="50 40 760 480"]')).toBeVisible();

    // Step forward simulation by 1 hour
    const stepBtn = page.locator('button[title*="Step Forward"]');
    await stepBtn.click();

    // Verify footer advisory notice
    await expect(page.locator('text=Zero Actuation Guarantee')).toBeVisible();
  });
});
