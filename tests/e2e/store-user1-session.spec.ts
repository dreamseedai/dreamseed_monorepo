import { test } from "@playwright/test";

test("사용자1 로그인 상태 저장", async ({ page }) => {
    await page.goto("/login");
    await page.fill('input[name="email"]', "user1@example.com");
    await page.fill('input[name="password"]', "userpassword");
    await page.click('button[type="submit"]');
    await page.waitForURL(/\/dashboard/);

    await page.context().storageState({ path: "storage/user1.json" });
});
