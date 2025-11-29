import { expect, test } from "@playwright/test";

test.use({ storageState: "storage/admin.json" });

test("관리자 후원자 통계 → 후원자 프로필 보기", async ({ page }) => {
    await page.goto("/admin/finance/mybrand/sponsor-stats");

    // 후원자 이름 클릭 → 프로필 페이지 이동
    await page.getByRole("link", { name: "홍길동" }).click();

    await expect(page).toHaveURL(/\/admin\/users\/\d+/);
    await expect(page.getByText("후원자 프로필")).toBeVisible();
});

test("관리자 후원자 목록 접근", async ({ page }) => {
    await page.goto("/admin/finance/mybrand/sponsor-stats");
    await page.getByRole("link", { name: "홍길동" }).click();
    await expect(page).toHaveURL(/\/admin\/users\/\d+/);
});

test.use({ storageState: "storage/user1.json" });

test("사용자 대시보드 진입", async ({ page }) => {
    await page.goto("/dashboard");
    await expect(page.getByText("학습 기록")).toBeVisible();
});
