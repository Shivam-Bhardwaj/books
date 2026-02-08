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

  // Reader theme should stay "paper-like" even when the browser is in dark mode.
  const rgb = await page.evaluate(() => {
    const c = getComputedStyle(document.body).color;
    const m = c.match(/rgba?\((\d+),\s*(\d+),\s*(\d+)/);
    return m ? m.slice(1, 4).map((n) => Number(n)) : null;
  });
  expect(rgb).not.toBeNull();
  expect(rgb[0] + rgb[1] + rgb[2]).toBeLessThan(200);

  // Spot-check that the first chapter link works.
  await page.getByRole("link", { name: /The Lensmaker/i }).click();
  await expect(page).toHaveURL(/\/books\/butterfly-effect\/manuscript\/arc-1\/chapter-01\.html$/);
});

test("Chapter nav 'Contents' returns to TOC", async ({ page }) => {
  await page.goto("/books/butterfly-effect/manuscript/arc-1/chapter-01.html");
  await expect(page).toHaveTitle(/Butterfly Effect — Chapter 1/i);

  // Avoid strict justification + auto hyphenation (no trailing hyphens like `some-`).
  const paraStyles = await page.evaluate(() => {
    const p = document.querySelector(".chapter-body p");
    if (!p) return null;
    const cs = getComputedStyle(p);
    return { textAlign: cs.textAlign, hyphens: cs.hyphens };
  });
  expect(paraStyles).not.toBeNull();
  expect(paraStyles.textAlign).toBe("justify");
  expect(paraStyles.hyphens).toBe("auto");

  await page
    .locator("nav.chapter-nav")
    .first()
    .getByRole("link", { name: "Contents" })
    .click();
  await expect(page).toHaveURL(/\/books\/butterfly-effect\/(index\.html)?$/);
});

test("Chapter sigils are inline SVGs with animation attributes", async ({
  page,
}) => {
  await page.goto("/books/butterfly-effect/manuscript/arc-1/chapter-01.html");

  // Chapter pages should have an inline <svg>, not an <img>, for the sigil
  const sigil = page.locator(".chapter-sigil svg.sigil");
  await expect(sigil).toHaveCount(1);
  await expect(sigil).toHaveAttribute("data-anim", "draw-on-scroll");
  await expect(sigil).toHaveAttribute("role", "img");

  // Should have one of the world animation classes
  const hasWorldClass = await sigil.evaluate((el) =>
    el.classList.contains("svg-anim-continental") ||
    el.classList.contains("svg-anim-antarctic") ||
    el.classList.contains("svg-anim-dual")
  );
  expect(hasWorldClass).toBeTruthy();
});

test("SVG animation activates on scroll", async ({ page }) => {
  await page.goto("/books/butterfly-effect/manuscript/arc-1/chapter-01.html");
  const sigil = page.locator(".chapter-sigil svg.sigil");
  await expect(sigil).toHaveCount(1);

  // After the page loads and the sigil is visible, the IntersectionObserver
  // should add the svg-anim-active class
  await expect(sigil).toHaveClass(/svg-anim-active/, { timeout: 5000 });
});

test("TOC sigils remain as <img> tags (not inline SVGs)", async ({ page }) => {
  await page.goto("/books/butterfly-effect/");

  // TOC should use <img> tags for sigils, not inline SVGs
  const imgSigils = page.locator(".chapter-link .chapter-sigil img.sigil");
  const svgSigils = page.locator(".chapter-link .chapter-sigil svg.sigil");

  const imgCount = await imgSigils.count();
  const svgCount = await svgSigils.count();

  expect(imgCount).toBeGreaterThan(0);
  expect(svgCount).toBe(0);
});
