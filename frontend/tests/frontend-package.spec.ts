import { test, expect } from "@playwright/test";
import path from "node:path";
import { execFileSync } from "node:child_process";

test("complete frontend ZIP: automatic check, isolated preview, publish, customer inquiry and unchanged admin", async ({
  page,
  context,
}, testInfo) => {
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(e.message));
  await page.goto("/admin");
  await page.getByLabel("E-Mail-Adresse").fill("browser@example.com");
  await page
    .getByLabel("Passwort", { exact: true })
    .fill("browser-test-only-123");
  await page
    .getByRole("button", { name: "Im Arbeitsbereich anmelden" })
    .click();
  await expect(page.getByRole("heading", { name: "Übersicht." })).toBeVisible();
  const saved = await (await page.request.get("/api/admin/config")).json();
  try {
    await page.goto("/admin/studio");
    await expect(
      page.getByRole("heading", { name: "Frontend importieren", exact: true }),
    ).toBeVisible();
    const file =
      process.env.RAUMWERK_TEST_PACKAGE ||
      path.resolve(__dirname, "../portable/example.zip");
    const buffer = execFileSync(
      path.resolve(__dirname, "../../.venv/bin/python"),
      [
        "-c",
        'import io,json,sys,zipfile; src=zipfile.ZipFile(sys.argv[1]); out=io.BytesIO(); dest=zipfile.ZipFile(out,"w",zipfile.ZIP_DEFLATED); [(dest.writestr(n,json.dumps({**json.loads(src.read(n)),"id":sys.argv[2]}).encode() if n=="manifest.json" else src.read(n))) for n in src.namelist()]; dest.close(); sys.stdout.buffer.write(out.getvalue())',
        file,
        "e2e-" + testInfo.project.name + "-" + Date.now().toString(36),
      ],
      { maxBuffer: 12 * 1024 * 1024 },
    );
    await page
      .getByLabel("Frontend-Designpaket")
      .setInputFiles({
        name: "Raumwerk-Frontend.zip",
        mimeType: "application/zip",
        buffer,
      });
    await expect(
      page.getByText(/Dateien · .* Bilder · vollständiges Frontend/),
    ).toBeVisible();
    await page.getByRole("button", { name: "Als Entwurf übernehmen" }).click();
    await expect(
      page.getByRole("link", { name: "Vorschau öffnen" }),
    ).toBeVisible();
    const draft = (await (await page.request.get("/api/admin/config")).json())
      .draft;
    expect(draft.company).toBe(saved.draft.company);
    const pdf = Buffer.from(
      "%PDF-1.4\nSynthetic browser fixture only\n%%EOF\n",
    );
    const uploaded = await (
      await page.request.post("/api/admin/files", {
        headers: { "X-Requested-With": "Raumwerk" },
        multipart: {
          purpose: "template",
          file: {
            name: "Testvorlage.pdf",
            mimeType: "application/pdf",
            buffer: pdf,
          },
        },
      })
    ).json();
    draft.modules.disclosure = true;
    draft.disclosure_returns = true;
    draft.disclosure_pdf = uploaded.id;
    expect(
      (
        await page.request.put("/api/admin/config", {
          headers: { "X-Requested-With": "Raumwerk" },
          data: draft,
        })
      ).ok(),
    ).toBe(true);
    const anonymous = await context.browser()!.newContext();
    expect(
      (
        await anonymous.request.get(
          draft.frontend_package.entry.replace(
            /frontend-preview\/[^/]+\//,
            "frontend/",
          ),
        )
      ).status(),
    ).toBe(404);
    await anonymous.close();
    await page.goto("/?preview=1");
    const preview = page.frameLocator("iframe");
    await expect(
      preview.getByRole("heading", { name: /Räume für heute/ }),
    ).toBeVisible({ timeout: 30000 });
    await preview.getByRole("link", { name: "Immobilien entdecken" }).click();
    await expect(page).toHaveURL(/immobilien\?preview=1/);
    await preview
      .getByRole("link", { name: /Kontakt/ })
      .first()
      .click();
    await expect(page).toHaveURL(/kontakt\?preview=1/);
    await expect(
      preview.getByRole("button", { name: "Vorschau · kein Versand" }),
    ).toBeDisabled();
    // Foreign frontend code must never read host DOM, storage or private APIs.
    const isolation = await page
      .locator("iframe")
      .evaluate(async (node: HTMLIFrameElement) =>
        node.getAttribute("sandbox"),
      );
    expect(isolation).not.toContain("allow-same-origin");
    await page.goto("/admin/studio");
    await page
      .getByRole("button", { name: "Veröffentlichen", exact: true })
      .click();
    await expect(
      page
        .getByRole("status")
        .filter({ hasText: "Änderungen sind veröffentlicht" }),
    ).toBeVisible();
    const visitor = await context.browser()!.newContext();
    const customer = await visitor.newPage();
    await customer.goto("/kontakt");
    const site = customer.frameLocator("iframe");
    await site.getByLabel("Vorname *").fill("Paket");
    await site
      .getByLabel("Nachname *")
      .fill("Interessent " + testInfo.project.name);
    await site
      .getByLabel("E-Mail *", { exact: true })
      .fill("paket@example.com");
    await site
      .getByLabel("Ihre Nachricht *")
      .fill(
        "Synthetische Anfrage durch das vollständige importierte Frontend.",
      );
    await site.getByRole("checkbox").check();
    const acceptedResponse = customer.waitForResponse(
      (r) =>
        r.url().endsWith("/api/public/inquiries") &&
        r.request().method() === "POST",
    );
    await site.getByRole("button", { name: "Anfrage absenden" }).click();
    await expect(
      site.getByRole("heading", { name: "Vielen Dank für Ihr Vertrauen." }),
    ).toBeVisible();
    const accepted = await (await acceptedResponse).json();
    const customerFrame = customer
      .frames()
      .find((f) => f.url().includes("/api/public/frontend/"))!;
    expect(
      await customerFrame.evaluate(() => {
        try {
          return !!parent.document.body;
        } catch {
          return false;
        }
      }),
    ).toBe(false);
    const refused = await customerFrame.evaluate(async () => {
      try {
        await fetch("/api/admin/inquiries");
        return false;
      } catch {
        return true;
      }
    });
    expect(refused).toBe(true);
    expect(
      await customerFrame.evaluate(async () => {
        try {
          await (window as any).Raumwerk.navigate("https://example.com");
          return false;
        } catch {
          return true;
        }
      }),
    ).toBe(true);
    expect(
      await customerFrame.evaluate(
        () => document.documentElement.scrollWidth <= innerWidth,
      ),
    ).toBe(true);
    await customer.goto("/selbstauskunft");
    const documentSite = customer.frameLocator("iframe");
    const downloadEvent = customer.waitForEvent("download");
    await documentSite
      .getByRole("link", { name: "Selbstauskunft herunterladen" })
      .click();
    expect((await downloadEvent).suggestedFilename()).toContain(".pdf");
    await documentSite
      .getByLabel("Anfragekennung")
      .fill(String(accepted.reference));
    await documentSite
      .getByLabel("E-Mail der Anfrage")
      .fill("paket@example.com");
    await documentSite
      .getByLabel("Persönlicher Rückgabecode")
      .fill(accepted.document_token);
    await documentSite
      .getByLabel("Ausgefülltes PDF")
      .setInputFiles({
        name: "Private-Rueckgabe.pdf",
        mimeType: "application/pdf",
        buffer: pdf,
      });
    await documentSite.getByRole("checkbox").check();
    const returnedResponse = customer.waitForResponse(
      (r) =>
        r.url().endsWith("/api/public/disclosure-return") &&
        r.request().method() === "POST",
    );
    await documentSite
      .getByRole("button", { name: "Dokument privat übermitteln" })
      .click();
    expect((await returnedResponse).status()).toBe(202);
    await expect(documentSite.getByRole("status")).toContainText(
      "privat gespeichert",
    );
    await customer.goto("/");
    await expect(
      customer
        .frameLocator("iframe")
        .getByRole("heading", { name: /Räume für heute/ }),
    ).toBeVisible();
    const hero = customer.frameLocator("iframe").locator(".hero-image");
    await expect
      .poll(() =>
        hero.evaluate(
          (img: HTMLImageElement) => img.complete && img.naturalWidth > 0,
        ),
      )
      .toBe(true);
    if (process.env.RAUMWERK_PACKAGE_SCREENSHOT)
      await customer.screenshot({
        path: process.env.RAUMWERK_PACKAGE_SCREENSHOT.replace("{project}", testInfo.project.name),
        fullPage: true,
      });
    await visitor.close();
    await page.goto("/admin/inquiries");
    await expect(
      page.getByText("Paket Interessent " + testInfo.project.name, {
        exact: true,
      }),
    ).toBeVisible();
    expect(await page.locator("iframe").count()).toBe(0);
    expect(errors).toEqual([]);
  } finally {
    await page.request.put("/api/admin/config", {
      data: saved.published,
      headers: { "X-Requested-With": "Raumwerk" },
    });
    await page.request.post("/api/admin/config/publish", {
      headers: { "X-Requested-With": "Raumwerk" },
    });
    await page.request.put("/api/admin/config", {
      data: saved.draft,
      headers: { "X-Requested-With": "Raumwerk" },
    });
  }
});
