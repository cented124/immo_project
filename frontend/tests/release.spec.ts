import { test, expect } from "@playwright/test";

test("operating status, local indexing and revoking another browser session", async ({ page, browser }) => {
  async function login(target: typeof page) {
    await target.goto("/admin");
    await target.getByLabel("E-Mail-Adresse").fill("browser@example.com");
    await target.getByLabel("Passwort", { exact: true }).fill("browser-test-only-123");
    await target.getByRole("button", { name: "Im Arbeitsbereich anmelden" }).click();
    await expect(target.getByRole("heading", { name: "Übersicht." })).toBeVisible();
  }
  await login(page);
  await expect(page.locator(".admin-topbar")).toContainText("Lokal auf diesem Computer · 1.0.0");
  await page.goto("/admin/settings");
  await expect(page.getByRole("heading", { name: "Betriebsstatus & Startprüfung" })).toBeVisible();
  await expect(page.getByText("Raumwerk 1.0.0 · Lokaler Baukasten", { exact: true })).toBeVisible();
  await expect(page.getByText(/keine automatische Synchronisierung/)).toBeVisible();
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  const robots = await page.request.get("/robots.txt");
  expect(robots.status()).toBe(200);
  expect(await robots.text()).toContain("Disallow: /");
  const sitemap = await page.request.get("/sitemap.xml");
  expect(sitemap.status()).toBe(200);
  expect(await sitemap.text()).not.toContain("<loc>");
  const other = await browser.newContext({ baseURL: "http://localhost:3001" });
  try {
    const second = await other.newPage();
    await login(second);
    await page.goto("/admin/account");
    await page.getByRole("button", { name: "Andere Sitzungen abmelden" }).click();
    await expect(page.getByRole("status")).toContainText(/andere Sitzung\(en\) beendet/);
    expect((await other.request.get("http://localhost:3001/api/admin/me")).status()).toBe(401);
    expect((await page.request.get("/api/admin/me")).status()).toBe(200);
  } finally { await other.close(); }
});
