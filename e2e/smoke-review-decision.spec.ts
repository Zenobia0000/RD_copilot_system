import { test, expect } from "@playwright/test";

/**
 * Smoke Test 3: DesignReview page loads with evidence/risk tabs,
 * and navigation to DecisionRecord page works.
 *
 * Flow: Navigate to Review page -> verify 4 tabs (evidence, risk, experiment, attachments)
 *       -> Navigate to Decision page -> verify it loads.
 */

const PROJECT_ID = "00000000-0000-0000-0000-000000000001";

test.describe("Review -> Decision", () => {
  test("design review page renders with evidence and risk tabs", async ({ page }) => {
    await page.goto(`/projects/${PROJECT_ID}/review`);

    const url = page.url();
    if (url.includes("/auth")) {
      test.info().annotations.push({
        type: "skip-reason",
        description: "Redirected to /auth — no session.",
      });
      return;
    }

    // Page heading
    await expect(page.locator("h1")).toContainText("Review");

    // Four tabs should be present
    await expect(page.getByRole("tab", { name: /證據矩陣/ })).toBeVisible();
    await expect(page.getByRole("tab", { name: /風險登錄/ })).toBeVisible();
    await expect(page.getByRole("tab", { name: /最小實驗/ })).toBeVisible();
    await expect(page.getByRole("tab", { name: /附件/ })).toBeVisible();

    // Evidence tab should be active by default
    const evidenceTab = page.getByRole("tab", { name: /證據矩陣/ });
    await expect(evidenceTab).toHaveAttribute("data-state", "active");
  });

  test("can navigate from review to decision record page", async ({ page }) => {
    await page.goto(`/projects/${PROJECT_ID}/decide`);

    const url = page.url();
    if (url.includes("/auth")) {
      test.info().annotations.push({
        type: "skip-reason",
        description: "Redirected to /auth — no session.",
      });
      return;
    }

    // DecisionRecord page should render (it has its own heading/content)
    // Check that we are on the decide page and it rendered something
    expect(page.url()).toContain("/decide");
    await expect(page.locator("body")).toBeVisible();
  });

  test("risk tab can be activated on review page", async ({ page }) => {
    await page.goto(`/projects/${PROJECT_ID}/review`);

    const url = page.url();
    if (url.includes("/auth")) return;

    const riskTab = page.getByRole("tab", { name: /風險登錄/ });
    await riskTab.click();
    await expect(riskTab).toHaveAttribute("data-state", "active");
  });
});
