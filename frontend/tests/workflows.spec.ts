import { test, expect } from "@playwright/test";
async function login(page: any) {
  await page.goto("/admin");
  await page.getByLabel("E-Mail-Adresse").fill("browser@example.com");
  await page
    .getByLabel("Passwort", { exact: true })
    .fill("browser-test-only-123");
  await page
    .getByRole("button", { name: "Im Arbeitsbereich anmelden" })
    .click();
  await expect(page.getByRole("heading", { name: "Übersicht." })).toBeVisible();
}

test("template import, safe preview navigation and individual page form settings", async ({
  page,
}) => {
  await login(page);
  await page.goto("/admin/design");
  const id = "import-" + Date.now();
  const manifest = {
    id,
    name: "Importiertes Testdesign",
    version: 1,
    adapter: "editorial",
    pages: [
      "home",
      "properties",
      "property",
      "contact",
      "disclosure",
      "content",
    ],
    actions: ["search", "inquiry", "download", "return"],
  };
  await page.getByLabel("Manifest-Inhalt").fill(JSON.stringify(manifest));
  await page.getByRole("button", { name: "Prüfen und importieren" }).click();
  await expect(
    page.getByRole("status").filter({ hasText: "Template importiert" }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Entwurf speichern" }).click();
  await expect(
    page.getByRole("status").filter({ hasText: "Entwurf gespeichert" }),
  ).toBeVisible();
  await page.goto("/?preview=1");
  await expect(page.locator(".website.editorial")).toBeVisible();
  await page
    .locator(".site-footer")
    .getByRole("link", { name: "Kontakt", exact: true })
    .click();
  await expect(page).toHaveURL(/preview=1/);
  await expect(
    page
      .locator(
        "form.contact-form button[type=submit],form.contact-form button.button",
      )
      .first(),
  ).toBeDisabled();
  await page.goto("/admin/modules");
  await page.locator("summary").filter({ hasText: "Bewertung ·" }).click();
  const details = page
    .locator("details[open]")
    .filter({ hasText: "Bewertung ·" });
  await details
    .getByRole("checkbox", { name: "Eigene Einstellungen verwenden" })
    .check();
  await details.getByRole("switch", { name: "Telefon ist Pflicht" }).check();
  await page.getByRole("button", { name: "Entwurf speichern" }).click();
  await expect(
    page.getByRole("status").filter({ hasText: "Entwurf gespeichert" }),
  ).toBeVisible();
  const settings = await (await page.request.get("/api/admin/config")).json();
  expect(settings.draft.forms.bewertung.phone_required).toBe(true);
  await page.goto("/admin/account");
  await expect(
    page.getByRole("heading", { name: "Mein Passwort ändern" }),
  ).toBeVisible();
});
test("public navigation, responsive layout and accepted contact form", async ({
  page,
}) => {
  await page.goto("/");
  await expect(
    page.getByRole("heading", { name: "Räume für heute. Werte für morgen." }),
  ).toBeVisible();
  await expect(
    page.getByRole("link", { name: "Immobilien entdecken" }),
  ).toBeVisible();
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
  ).toBeTruthy();
  await page.goto("/kontakt");
  await page.getByLabel("Vorname *").fill("Browser");
  await page.getByLabel("Nachname *").fill("Test");
  await page
    .getByLabel("E-Mail *", { exact: true })
    .fill("browser@example.com");
  await page
    .getByLabel("Ihre Nachricht *")
    .fill("Eine Anfrage aus dem automatisierten Browsertest.");
  await page.getByRole("checkbox").check();
  await page.getByRole("button", { name: "Anfrage absenden" }).click();
  await expect(
    page.getByRole("heading", { name: "Vielen Dank für Ihr Vertrauen." }),
  ).toBeVisible();
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
  ).toBeTruthy();
});
test("login, company-neutral preview, inquiry management and logout", async ({
  page,
}) => {
  await login(page);
  await page.goto("/admin/design");
  await page
    .getByLabel("Firmenname", { exact: true })
    .fill("Beliebige Firma GmbH");
  await page.getByRole("button", { name: "Entwurf speichern" }).click();
  await expect(page.getByRole("status")).toContainText("Entwurf gespeichert");
  await page.goto("/?preview=1");
  await expect(page.locator(".site-header .brand")).toContainText(
    "Beliebige Firma GmbH",
  );
  await page.goto("/admin/inquiries");
  await expect(page.getByText("Browser Test").first()).toBeVisible();
  await page.getByText("Browser Test").first().click();
  await page.getByLabel("Interne Notizen").fill("Rückruf geplant");
  await page.getByLabel("Bearbeitungsstatus").selectOption("processing");
  await page.getByRole("button", { name: "Änderungen speichern" }).click();
  await expect(page.getByRole("status")).toContainText("Anfrage aktualisiert");
  await page.goto("/admin");
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
  ).toBeTruthy();
  if (await page.getByRole("button", { name: "Menü", exact: true }).isVisible())
    await page.getByRole("button", { name: "Menü", exact: true }).click();
  await page.getByRole("button", { name: "Abmelden" }).click();
  await expect(
    page.getByRole("heading", { name: "Schön, dass Sie da sind." }),
  ).toBeVisible();
});
test("wizard saves a private property draft with a real image", async ({
  page,
}) => {
  await login(page);
  await page.goto("/admin/properties");
  await page
    .getByRole("button", { name: "Immobilie anlegen", exact: true })
    .click();
  await page
    .getByLabel("Titel", { exact: true })
    .fill("BROWSERTEST – kein echtes Angebot");
  await page.getByLabel("URL-Slug").fill("browsertest-" + Date.now());
  await page.getByLabel("Ort", { exact: true }).fill("Hamburg");
  await page.getByRole("button", { name: "Texte & Medien" }).click();
  await page
    .locator("input[type=file]")
    .first()
    .setInputFiles({
      name: "test.png",
      mimeType: "image/png",
      buffer: Buffer.from(
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+jN1kAAAAASUVORK5CYII=",
        "base64",
      ),
    });
  await expect(page.getByText("Titelbild", { exact: true })).toBeVisible();
  await page.getByRole("button", { name: "Als Entwurf speichern" }).click();
  await expect(page.getByRole("status")).toContainText("Entwurf gespeichert");
  await page.getByRole("button", { name: "Zur Immobilienverwaltung" }).click();
  await expect(
    page.getByText("BROWSERTEST – kein echtes Angebot").first(),
  ).toBeVisible();
  const properties = await page.request.get("/api/public/properties");
  expect((await properties.json()).total).toBe(0);
});

test("publish a listing, submit an associated application, disable the module and withdraw the listing", async ({
  page,
}) => {
  await login(page);
  const slug = "durchgang-" + Date.now();
  await page.goto("/admin/properties");
  await page
    .getByRole("button", { name: "Immobilie anlegen", exact: true })
    .click();
  await page
    .getByLabel("Titel", { exact: true })
    .fill("ABNAHMETEST – kein echtes Angebot");
  await page.getByLabel("URL-Slug").fill(slug);
  await page.getByLabel("Ort", { exact: true }).fill("Hamburg");
  await page.getByLabel("Postleitzahl").fill("20095");
  await page.getByRole("button", { name: "Flächen & Ausstattung" }).click();
  await page.getByLabel("Wohnfläche (m²)", { exact: true }).fill("90");
  await page.getByLabel("Zimmer", { exact: true }).fill("3");
  await page.getByRole("button", { name: /Preise$/ }).click();
  await page.getByLabel("Kaufpreis (€)", { exact: true }).fill("450000");
  await page.getByRole("button", { name: /Energie$/ }).click();
  await page
    .getByRole("combobox", { name: "Energieausweis", exact: true })
    .selectOption("exempt");
  await page
    .getByLabel("Grund für die Ausnahme")
    .fill("Synthetischer Abnahmetest, keine rechtliche Aussage.");
  await page.getByRole("button", { name: "Texte & Medien" }).click();
  await page
    .getByLabel("Objektbeschreibung", { exact: true })
    .fill("Synthetisches Objekt nur im isolierten Browsertest.");
  await page
    .locator("input[type=file]")
    .first()
    .setInputFiles({
      name: "test.png",
      mimeType: "image/png",
      buffer: Buffer.from(
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+jN1kAAAAASUVORK5CYII=",
        "base64",
      ),
    });
  await expect(page.getByText("Titelbild", { exact: true })).toBeVisible();
  await page.getByRole("button", { name: "Prüfen & veröffentlichen" }).click();
  await page
    .getByRole("combobox", { name: "Veröffentlichungsstatus", exact: true })
    .selectOption("published");
  const responsePromise = page.waitForResponse(
    (r) =>
      r.url().endsWith("/api/admin/properties") &&
      r.request().method() === "POST",
  );
  await page
    .getByRole("button", { name: "Immobilie veröffentlichen", exact: true })
    .click();
  const property = await (await responsePromise).json();
  await expect(page.getByRole("status")).toContainText("Veröffentlicht");
  await page.goto("/immobilien/" + slug);
  await expect(
    page.getByRole("heading", { name: "ABNAHMETEST – kein echtes Angebot" }),
  ).toBeVisible();
  await page
    .getByRole("button", { name: "Interesse an dieser Immobilie" })
    .click();
  await page.getByLabel("Vorname *").fill("Objekt");
  await page.getByLabel("Nachname *").fill("Bewerbung");
  await page
    .getByLabel("E-Mail *", { exact: true })
    .fill("application@example.com");
  await page
    .getByLabel("Ihre Nachricht *")
    .fill("Bewerbung für genau dieses Testobjekt.");
  await page.getByRole("checkbox").check();
  await page.getByRole("button", { name: "Anfrage absenden" }).click();
  await expect(
    page.getByRole("heading", { name: "Vielen Dank für Ihr Vertrauen." }),
  ).toBeVisible();
  const applications = await (
    await page.request.get("/api/admin/inquiries?property_id=" + property.id)
  ).json();
  expect(applications[0].property_id).toBe(property.id);
  await page.goto("/admin/modules");
  await page.getByRole("switch", { name: /^Immobilienangebote/ }).uncheck();
  await page
    .getByRole("button", { name: "Veröffentlichen", exact: true })
    .click();
  await expect(
    page
      .getByRole("status")
      .filter({ hasText: "Änderungen sind veröffentlicht." }),
  ).toBeVisible();
  expect((await page.request.get("/api/public/properties")).status()).toBe(404);
  await page.goto("/");
  await expect(
    page.locator(".site-header nav a").filter({ hasText: /^Immobilien$/ }),
  ).toHaveCount(0);
  const cfg = await (await page.request.get("/api/admin/config")).json();
  cfg.draft.modules.properties = true;
  const headers = { "X-Requested-With": "Raumwerk" };
  expect(
    (
      await page.request.put("/api/admin/config", { headers, data: cfg.draft })
    ).ok(),
  ).toBeTruthy();
  expect(
    (await page.request.post("/api/admin/config/publish", { headers })).ok(),
  ).toBeTruthy();
  expect(
    (
      await page.request.put("/api/admin/properties/" + property.id, {
        headers,
        data: { ...property, status: "archived" },
      })
    ).ok(),
  ).toBeTruthy();
  expect(
    (await page.request.get("/api/public/properties/" + slug)).status(),
  ).toBe(404);
  expect(
    (
      await page.request.get("/api/public/files/" + property.images[0].id)
    ).status(),
  ).toBe(404);
});
