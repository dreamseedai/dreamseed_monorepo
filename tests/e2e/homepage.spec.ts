import { expect, test } from "@playwright/test";

test("홈페이지 접근 및 감정 대시보드 진입", async ({ page }) => {
    await page.goto("/");

    // 타이틀 확인
    await expect(page).toHaveTitle(/myKtube/i);

    // 메뉴 클릭 (사이드바 또는 헤더 기준)
    await page.getByText("감정 대시보드").click();

    // URL 확인
    await expect(page).toHaveURL(/\/dashboard\/emotion/);
});
