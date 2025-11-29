import { expect, test } from '@playwright/test';

test.describe('myKtube 전체 사용자 흐름', () => {
    test('홈페이지 접속 및 감정 리포트 진입', async ({ page }) => {
        await page.goto('/');
        await expect(page).toHaveTitle(/myKtube/i);

        // 감정 대시보드 버튼 클릭 (예시: sidebar에 있는 경우)
        await page.click('text=감정 대시보드');
        await expect(page).toHaveURL(/.*\/dashboard\/emotion/);
    });

    test('관리자 후원자 프로필 진입', async ({ page }) => {
        await page.goto('/admin/users/1');
        await expect(page.locator('text=후원자 프로필')).toBeVisible();

        await expect(page.locator('text=총 후원 금액')).toBeVisible();
        await expect(page.locator('text=관리자 메모')).toBeVisible();
    });
});
