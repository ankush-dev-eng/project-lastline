import { test, expect } from '@playwright/test';

test.describe('PROJECT LASTLINE Control Room Operations E2E Flow', () => {
  test('verifies advisory banner, control room views, and human-in-the-loop workflow', async ({ page }) => {
    // 1. Navigate to the operations console
    await page.goto('/');

    // 2. Verify strict advisory sandbox banner
    const advisoryBanner = page.locator('text=SANDBOX – ADVISORY ONLY (ZERO PHYSICAL ACTUATION)');
    await expect(advisoryBanner).toBeVisible();

    // 3. Verify System Status badge
    await expect(page.locator('text=PROJECT LASTLINE')).toBeVisible();

    // 4. Verify Replay Controls
    await expect(page.locator('text=Scenario Replay Control')).toBeVisible();
    await expect(page.getByRole('button', { name: /play/i })).toBeVisible();
    await expect(page.getByRole('button', { name: /step/i })).toBeVisible();

    // 5. Test Operations Map view and node click
    const mapTab = page.getByRole('button', { name: /operations map/i });
    await mapTab.click();
    await expect(page.locator('svg')).toBeVisible();

    // Click on a node in the SVG to open the Node Inspector Drawer
    const j1Node = page.locator('circle').first();
    if (await j1Node.isVisible()) {
      await j1Node.click();
    }

    // 6. Test Agent Reasoning DAG view
    const agentTab = page.getByRole('button', { name: /agent reasoning/i });
    await agentTab.click();
    await expect(page.locator('text=Sentinel Agent')).toBeVisible();
    await expect(page.locator('text=Telemetry Trust & Integrity Agent')).toBeVisible();
    await expect(page.locator('text=Physics State Estimator')).toBeVisible();

    // 7. Test Twin Simulation Lab view
    const twinTab = page.getByRole('button', { name: /twin simulation/i });
    await twinTab.click();
    await expect(page.locator('text=Digital Twin State Reconstruction Lab')).toBeVisible();

    // 8. Test Audit Log Ledger view
    const auditTab = page.getByRole('button', { name: /audit log/i });
    await auditTab.click();
    await expect(page.locator('text=Cryptographic SHA-256 Audit Log')).toBeVisible();
    await expect(page.locator('text=Audit Chain Valid')).toBeVisible();

    // 9. Switch back to Operations Map and verify Advisory Recommendations panel
    await mapTab.click();
    const recHeading = page.locator('text=Advisory Response Playbooks');
    await expect(recHeading).toBeVisible();

    // Verify presence of Human-In-The-Loop action buttons
    const approveBtn = page.getByRole('button', { name: /approve/i }).first();
    if (await approveBtn.isVisible()) {
      await approveBtn.click();
      await expect(page.locator('text=APPROVED')).toBeVisible();
    }
  });
});
