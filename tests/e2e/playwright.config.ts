import { defineConfig } from "@playwright/test";

export default defineConfig({
    testDir: "./tests/e2e",
    use: {
        baseURL: "http://localhost:5173",
        storageState: "storageState.json",  // ✅ 여기!
        headless: true,
    },
});
