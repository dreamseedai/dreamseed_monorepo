import { Locator, expect as playwrightExpect } from "@playwright/test";

function expect(locator: Locator) {
    return playwrightExpect(locator);
}

