import { test } from "@playwright/test";

test("로그인 상태 저장", async ({ page }) => {
    await page.goto("/login");

    await page.fill('input[name="email"]', "admin@example.com");
    await page.fill('input[name="password"]', "your-password");
    await page.click('button[type="submit"]');

    // 로그인 성공 여부 확인 (대시보드 도달)
    await page.waitForURL(/\/dashboard/);

    // storage 저장
    await page.context().storageState({ path: "storageState.json" });
});
