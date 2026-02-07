import { expect, test } from "@playwright/test";

test("arcade home loads and links to too.foo", async ({ page }) => {
  await page.goto("/");
  await expect(page).toHaveTitle(/books\.too\.foo/i);

  await expect(
    page.getByLabel("Primary").getByRole("link", { name: "too.foo" }),
  ).toHaveAttribute("href", "https://too.foo/");

  // Card should take you to the book entry route (redirect handled by _redirects).
  const bookCard = page.getByRole("link", { name: /Butterfly Effect/i });
  await expect(bookCard).toHaveAttribute("href", "/butterfly-effect/");
});
