import { expect, test } from "@playwright/test";

test("사용자 로그인 성공 흐름", async ({ page }) => {
    await page.goto("/login");

    await page.fill('input[name="email"]', "testuser@example.com");
    await page.fill('input[name="password"]', "correctpassword");
    await page.click('button[type="submit"]');

    // 로그인 후 대시보드로 이동
    await expect(page).toHaveURL(/\/dashboard/);
    await expect(page.getByText("환영합니다")).toBeVisible();
});
