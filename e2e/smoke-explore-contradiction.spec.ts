import { test, expect } from "@playwright/test";

/**
 * Smoke Test 2: Explore page loads with tab structure and contradiction tab.
 *
 * Flow: Navigate to Explore page -> verify 3-tab layout (socratic, contradictions, cld)
 *       -> click contradictions tab -> verify it activates.
 */

const PROJECT_ID = "00000000-0000-0000-0000-000000000001";

test.describe("Explore -> Contradiction", () => {
  test("explore page renders with three tabs", async ({ page }) => {
    await page.goto(`/projects/${PROJECT_ID}/explore`);

    const url = page.url();
    if (url.includes("/auth")) {
      test.info().annotations.push({
        type: "skip-reason",
        description: "Redirected to /auth — no session.",
      });
      return;
    }

    // Page heading
    await expect(page.locator("h1")).toContainText("Explore");

    // Three tabs should be present
    await expect(page.getByRole("tab", { name: /蘇格拉底問答/ })).toBeVisible();
    await expect(page.getByRole("tab", { name: /矛盾識別/ })).toBeVisible();
    await expect(page.getByRole("tab", { name: /因果迴路圖/ })).toBeVisible();
  });

  test("clicking contradictions tab activates it", async ({ page }) => {
    await page.goto(`/projects/${PROJECT_ID}/explore`);

    const url = page.url();
    if (url.includes("/auth")) return;

    const contradictionTab = page.getByRole("tab", { name: /矛盾識別/ });
    await contradictionTab.click();

    // The tab should now have data-state="active"
    await expect(contradictionTab).toHaveAttribute("data-state", "active");
  });

  test("explore page can be reached via hash tab", async ({ page }) => {
    await page.goto(`/projects/${PROJECT_ID}/explore#contradictions`);

    const url = page.url();
    if (url.includes("/auth")) return;

    // The contradictions tab should be active by default from hash
    const contradictionTab = page.getByRole("tab", { name: /矛盾識別/ });
    await expect(contradictionTab).toHaveAttribute("data-state", "active");
  });
});
