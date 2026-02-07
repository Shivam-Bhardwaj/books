import { expect, test } from "@playwright/test";

async function waitForFonts(page) {
  await page.waitForFunction(async () => {
    // `document.fonts` is supported in all modern browsers Playwright ships.
    await document.fonts.ready;
    return true;
  });
}

test("Butterfly Effect TOC loads styles, fonts, and navigation", async ({
  page,
}) => {
  await page.goto("/books/butterfly-effect/");
  await expect(page).toHaveTitle(/Butterfly Effect — Table of Contents/i);

  await expect(page.locator('link[rel="stylesheet"][href="style/novel.css"]')).toHaveCount(1);

  await expect(page.getByRole("link", { name: /All books/i })).toHaveAttribute(
    "href",
    "/#books",
  );
  await expect(page.getByRole("link", { name: /too\.foo/i })).toHaveAttribute(
    "href",
    "https://too.foo/",
  );

  await waitForFonts(page);
  const fontsOk = await page.evaluate(() => {
    return (
      document.fonts.check('12px "Literata"') &&
      document.fonts.check('12px "Space Grotesk"')
    );
  });
  expect(fontsOk).toBeTruthy();

  // Spot-check that the first chapter link works.
  await page.getByRole("link", { name: /1\.\s*The Lensmaker/i }).click();
  await expect(page).toHaveURL(/\/books\/butterfly-effect\/manuscript\/arc-1\/chapter-01\.html$/);
});

test("Chapter nav 'Contents' returns to TOC", async ({ page }) => {
  await page.goto("/books/butterfly-effect/manuscript/arc-1/chapter-01.html");
  await expect(page).toHaveTitle(/Butterfly Effect — Chapter 1/i);

  await page
    .locator("nav.chapter-nav")
    .first()
    .getByRole("link", { name: "Contents" })
    .click();
  await expect(page).toHaveURL(/\/books\/butterfly-effect\/(index\.html)?$/);
});
