// Two real browser users against a NEW isolated HTTPS test installation.
// Never run on customer data. Configuration and screenshots stay in the ignored run folder.
const fs = require("fs");
const path = require("path");
const { chromium, expect } = require("../frontend/node_modules/@playwright/test");
const configFile = path.resolve(process.argv[2]);
const run = path.dirname(configFile);
const config = JSON.parse(fs.readFileSync(configFile, "utf8"));
const target = new URL(config.url);
if (target.protocol !== "https:" || target.hostname !== "release.raumwerk.test" || !target.port || target.username || target.password || target.pathname !== "/" || target.search || target.hash || !config.spki)
  throw new Error("Only the isolated release.raumwerk.test installation is supported.");
const headers = { "X-Requested-With": "Raumwerk" };
let browser;
(async () => {
  browser = await chromium.launch({ executablePath: process.env.CHROMIUM_PATH || "/usr/bin/chromium", headless: true,
    args: ["--host-resolver-rules=MAP release.raumwerk.test 127.0.0.1", "--no-proxy-server", "--ignore-certificate-errors-spki-list=" + config.spki] });
  const owner = await browser.newContext({ viewport: { width: 1366, height: 900 } });
  const page = await owner.newPage();
  await page.goto(config.url + "/admin");
  await page.getByLabel("E-Mail-Adresse").fill(config.email);
  await page.getByLabel("Passwort", { exact: true }).fill(config.password);
  await page.getByRole("button", { name: "Im Arbeitsbereich anmelden" }).click();
  await expect(page.getByRole("heading", { name: "Übersicht." })).toBeVisible();
  await expect(page.locator(".admin-topbar")).toContainText("Server-Installation · 1.0.0");
  // Fixture setup uses the same authenticated API as the editor; property creation below uses the GUI.
  async function request(route, method = "GET", data) {
    const result = await page.evaluate(async ({ route, method, data }) => {
      const response = await fetch("/api" + route, { method, headers: { "X-Requested-With": "Raumwerk", "Content-Type": "application/json" }, body: data === undefined ? undefined : JSON.stringify(data) });
      return { status: response.status, body: await response.json() };
    }, { route, method, data });
    if (result.status >= 400) throw new Error(route + ": " + result.status);
    return result.body;
  }
  if ((await request("/admin/properties")).length || (await request("/admin/inquiries")).length)
    throw new Error("Simulation requires an empty disposable installation.");
  const c = (await request("/admin/config")).draft;
  c.company = "Lindenhafen Immobilien GmbH"; c.email = "kontakt@lindenhafen.example";
  c.phone = "+49 40 5550100"; c.address = "Beispielkai 12"; c.city = "Hamburg";
  c.legal = { ...c.legal, legal_form: "GmbH", representative: "Lara Beispiel", postcode: "20457", register_court: "Amtsgericht Musterstadt", register_number: "HRB TEST100", reviewed: true };
  c.legal_text = "Synthetisches Impressum der isolierten Testfirma. Kein öffentliches Unternehmen.";
  c.privacy_text = "Synthetischer Datenschutzhinweis. Alle Anfragen sind Testdaten.";
  c.modules.telegram = true; c.forms.application.telegram = true;
  await request("/admin/integrations/telegram", "PUT", { token: "release-test-token", chat_id: "synthetic-group", include_details: true });
  await request("/admin/config", "PUT", c); await request("/admin/config/publish", "POST");
  await page.goto(config.url + "/admin/studio");
  await page.getByLabel("Frontend-Designpaket").setInputFiles(path.join(__dirname, "../downloads/Westminster-Frontend.zip"));
  await expect(page.getByText(/Dateien · .* Bilder · vollständiges Frontend/)).toBeVisible();
  await page.getByRole("button", { name: "Als Entwurf übernehmen" }).click();
  await expect(page.getByRole("link", { name: "Vorschau öffnen" })).toBeVisible();
  await page.getByRole("button", { name: "Veröffentlichen", exact: true }).click();
  await expect(page.getByRole("status")).toContainText("Änderungen sind veröffentlicht");
  await page.goto(config.url + "/admin/properties");
  await page.getByRole("button", { name: "Immobilie anlegen", exact: true }).click();
  await page.getByLabel("Titel", { exact: true }).fill("SIMULATION – Helle Wohnung am Park");
  await page.getByLabel("URL-Slug (z. B. haus-am-park)").fill("wohnung-am-park");
  await page.getByRole("combobox", { name: "Angebotsart", exact: true }).selectOption("rent");
  await page.getByRole("combobox", { name: "Objektart", exact: true }).selectOption("apartment");
  await page.getByLabel("Postleitzahl").fill("20457"); await page.getByLabel("Ort", { exact: true }).fill("Hamburg");
  await page.getByRole("button", { name: "Weiter", exact: true }).click();
  await page.getByLabel("Wohnfläche (m²)", { exact: true }).fill("82"); await page.getByLabel("Zimmer", { exact: true }).fill("3");
  await page.getByRole("button", { name: "Weiter", exact: true }).click();
  await page.getByLabel("Kaltmiete (€)", { exact: true }).fill("1290");
  await page.getByRole("button", { name: "Weiter", exact: true }).click();
  await page.getByRole("combobox", { name: "Energieausweis", exact: true }).selectOption("exempt");
  await page.getByLabel("Grund für die Ausnahme").fill("Reines Testobjekt der isolierten Simulation.");
  await page.getByRole("button", { name: "Weiter", exact: true }).click();
  await page.getByLabel("Objektbeschreibung", { exact: true }).fill("Ausgedachte helle Wohnung für den vollständigen Abnahmetest.");
  await page.getByLabel("Immobilienbild hochladen (max. 10 MB)").setInputFiles(path.join(__dirname, "../frontend/public/architecture.png"));
  await expect(page.getByLabel("Bildbeschreibung / Alt-Text")).toBeVisible();
  await page.getByLabel("Bildbeschreibung / Alt-Text").fill("Illustration für die Simulation");
  await page.getByRole("button", { name: "Weiter", exact: true }).click();
  await page.getByRole("combobox", { name: "Veröffentlichungsstatus", exact: true }).selectOption("published");
  await page.getByRole("button", { name: "Immobilie veröffentlichen", exact: true }).click();
  await expect(page.getByRole("status")).toContainText("Immobilie gespeichert");
  const property = (await request("/admin/properties"))[0];
  const visitor = await browser.newContext({ viewport: { width: 390, height: 844 }, isMobile: true, hasTouch: true });
  const customer = await visitor.newPage();
  const propertyUrl = config.url + "/immobilien/wohnung-am-park";
  await customer.goto(propertyUrl);
  const site = customer.frameLocator("iframe");
  await expect(site.getByRole("heading", { name: property.title, exact: true, level: 1 })).toBeVisible();
  await expect(customer).toHaveTitle(new RegExp(property.title));
  expect(await customer.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  await customer.screenshot({ path: path.join(run, "besucher-mobil.png"), fullPage: true });
  // Browser TLS certificate was pinned above. Same-origin fetches verify the generated public metadata.
  const indexed = await customer.evaluate(async () => ({ robots: await (await fetch("/robots.txt")).text(), sitemap: await (await fetch("/sitemap.xml")).text() }));
  expect(indexed.robots).toContain("Disallow: /admin"); expect(indexed.sitemap).toContain(propertyUrl);
  await request("/admin/properties/" + property.id, "PUT", { ...property, status: "archived" });
  const hidden = await customer.goto(propertyUrl); expect(hidden.status()).toBe(404);
  await request("/admin/properties/" + property.id, "PUT", { ...property, status: "published" });
  await customer.goto(propertyUrl);
  await site.getByRole("button", { name: "Interesse an dieser Immobilie" }).click();
  await site.getByLabel("Vorname *").fill("Mara"); await site.getByLabel("Nachname *").fill("Testkundin");
  await site.getByLabel("E-Mail *", { exact: true }).fill("mara@example.com");
  await site.getByLabel("Ihre Nachricht *").fill("Synthetische Anfrage: Ich möchte die Musterwohnung besichtigen.");
  await site.getByRole("checkbox").check(); await site.getByRole("button", { name: "Anfrage absenden" }).click();
  await expect(site.getByRole("heading", { name: "Vielen Dank für Ihr Vertrauen." })).toBeVisible();
  await expect.poll(async () => (await request("/admin/deliveries"))[0]?.status, { timeout: 15000 }).toBe("sent");
  await page.goto(config.url + "/admin/inquiries");
  await page.getByText("Mara Testkundin", { exact: true }).click();
  await page.getByLabel("Bearbeitungsstatus").selectOption("processing");
  await page.getByLabel("Interne Notizen").fill("Rückruf vereinbart; synthetische Simulation.");
  await page.getByRole("button", { name: "Änderungen speichern" }).click();
  await expect(page.getByRole("status")).toContainText("Anfrage aktualisiert");
  await page.screenshot({ path: path.join(run, "anfrage-bearbeitet.png"), fullPage: true });
  await page.goto(config.url + "/admin/settings");
  await expect(page.getByRole("heading", { name: "Betriebsstatus & Startprüfung" })).toBeVisible();
  await expect(page.getByText("Technische Startprüfung bestanden.", { exact: false })).toBeVisible();
  const system = await request("/admin/system"); expect(system.ready).toBe(true);
  await page.screenshot({ path: path.join(run, "betriebsstatus.png"), fullPage: true });
  const result = { result: "passed", version: system.version, company: c.company, direct_live_property_creation: true, custom_frontend_import: true, mobile_customer: true, publication_withdrawal_republication: true, inquiry: true, simulated_telegram_delivery: true, admin_processing: true, https: true, search_metadata: true, system_ready: true, public_vps: false, real_messages_sent: 0 };
  fs.writeFileSync(path.join(run, "ergebnis.json"), JSON.stringify(result, null, 2));
  console.log("Live simulation passed: direct listings, custom frontend, mobile inquiry, simulated notification and admin processing.");
})().catch(error => { console.error(error.message); process.exitCode = 1; }).finally(async () => { if (browser) await browser.close(); });
