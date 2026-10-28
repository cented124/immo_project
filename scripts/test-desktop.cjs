// Smoke test for an isolated fresh checkout. Never uses live integration secrets.
const fs = require("fs");
const path = require("path");
const cp = require("child_process");
const crypto = require("crypto");
const net = require("net");
const http = require("http");
const root = path.resolve(process.argv[2] || ".");
const python =
  process.argv[3] || path.join(root, ".runtime", "python", "python.exe");
const runtime = path.join(root, ".runtime");
const ready = fs
  .readdirSync(runtime)
  .filter(
    (n) =>
      n.startsWith("web-") &&
      fs.existsSync(path.join(runtime, n, "desktop-ready.json")),
  )
  .sort();
const { chromium, expect } = require(
  path.join(runtime, ready.at(-1), "node_modules", "@playwright", "test"),
);
const password = "Native-test-" + crypto.randomBytes(16).toString("hex");
let browser, guard;
function command(action) {
  const result = cp.spawnSync(
    python,
    [
      "-X",
      "utf8",
      path.join(root, "scripts/desktop.py"),
      action,
      "--no-browser",
      "--no-delivery",
    ],
    { cwd: root, encoding: "utf8", timeout: 180000, windowsHide: true },
  );
  if (result.status !== 0)
    throw new Error(action + " failed: " + (result.stderr || result.stdout));
}
function state() {
  return JSON.parse(
    fs.readFileSync(path.join(runtime, "control/state.json"), "utf8"),
  );
}
function control(s, route) {
  return new Promise((resolve, reject) => {
    const r = http.request(
      s.url + route,
      { method: "POST", headers: { "X-Raumwerk-Control": s.control } },
      (response) => {
        let text = "";
        response.on("data", (v) => (text += v));
        response.on("end", () => {
          if (response.statusCode !== 200)
            return reject(new Error("control " + response.statusCode));
          resolve(JSON.parse(text));
        });
      },
    );
    r.on("error", reject);
    r.end();
  });
}
async function login(page, url) {
  await page.goto(url + "/admin");
  await expect
    .poll(
      async () =>
        (await page.getByRole("heading", { name: "Übersicht." }).isVisible()) ||
        (await page.getByLabel("E-Mail-Adresse").isVisible()),
    )
    .toBe(true);
  if (await page.getByRole("heading", { name: "Übersicht." }).isVisible())
    return;
  await page.getByLabel("E-Mail-Adresse").fill("desktop@example.com");
  await page.getByLabel("Passwort", { exact: true }).fill(password);
  await page
    .getByRole("button", { name: "Im Arbeitsbereich anmelden" })
    .click();
  await expect(page.getByRole("heading", { name: "Übersicht." })).toBeVisible();
}
(async () => {
  try {
    // Never terminate a process occupying port 3000: our own guard must survive stop.
    guard = net.createServer((socket) => socket.end());
    const guarded = await new Promise((resolve) => {
      guard.once("error", () => resolve(false));
      guard.listen(3000, "127.0.0.1", () => resolve(true));
    });
    command("launch");
    const first = state();
    if (guarded && new URL(first.url).port === "3000")
      throw new Error("occupied port was reused");
    command("launch");
    if (state().pid !== first.pid) throw new Error("duplicate supervisor");
    const open = await control(first, "/__desktop/open");
    if (!open.url.includes("/einrichten#"))
      throw new Error(
        "A fresh test project is required; existing administrator left unchanged.",
      );
    const launch =
      process.platform === "win32"
        ? { channel: "msedge" }
        : { executablePath: process.env.CHROMIUM_PATH || "/usr/bin/chromium" };
    browser = await chromium.launch({ headless: true, ...launch });
    const context = await browser.newContext({
        viewport: { width: 1280, height: 900 },
      }),
      page = await context.newPage();
    const failed = await context.request.post(first.url + "/__desktop/setup", {
      data: { email: "attacker@example.com", password, repeat: password },
    });
    if (failed.status() !== 403) throw new Error("setup must require its key");
    await page.goto(open.url);
    fs.mkdirSync(path.join(root, ".runtime/test-evidence"), { recursive: true });
    await expect(page.getByRole("heading", { name: /Dein Baukasten/ })).toBeVisible();
    await page.screenshot({
      path: path.join(root, ".runtime/test-evidence/setup.png"),
      fullPage: true,
    });
    await page.getByLabel("E-Mail-Adresse").fill("desktop@example.com");
    await page.getByLabel("Neues Passwort", { exact: true }).fill(password);
    await page
      .getByLabel("Passwort wiederholen", { exact: true })
      .fill(password);
    await page.getByRole("button", { name: "Administrator anlegen" }).click();
    await page.waitForURL("**/admin");
    await login(page, first.url);
    await page.goto(first.url + "/admin/design");
    await page
      .getByLabel("Firmenname", { exact: true })
      .fill("Fensterblick Test GmbH");
    await page
      .getByRole("button", { name: "Veröffentlichen", exact: true })
      .click();
    await expect(page.getByRole("status")).toContainText(
      "Änderungen sind veröffentlicht",
    );
    const headers = { "X-Requested-With": "Raumwerk" };
    const logo = await context.request.post(first.url + "/api/admin/files", {
      headers,
      multipart: {
        purpose: "image",
        file: {
          name: "test.png",
          mimeType: "image/png",
          buffer: Buffer.from(
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+jN1kAAAAASUVORK5CYII=",
            "base64",
          ),
        },
      },
    });
    if (logo.status() !== 200) throw new Error("multipart upload failed");
    const image = await logo.json();
    const property = await context.request.post(
      first.url + "/api/admin/properties",
      {
        headers,
        data: {
          title: "NATIVTEST – kein echtes Angebot",
          slug: "native-test-wohnung",
          offer: "rent",
          type: "apartment",
          status: "published",
          city: "Teststadt",
          postcode: "00000",
          area: 70,
          rooms: 3,
          price: 900,
          description: "Synthetische Testwohnung ohne Docker.",
          certificate: "exempt",
          exemption_reason: "Nur synthetischer Softwaretest.",
          images: [{ id: image.id, alt: "Synthetisches Testbild" }],
        },
      },
    );
    if (property.status() !== 200) throw new Error("property save failed");
    const secret = await context.request.put(
      first.url + "/api/admin/integrations/telegram",
      {
        headers,
        data: { token: "FAKE-LOCAL-NO-SENDING", chat_id: "local-only" },
      },
    );
    if (!secret.ok()) throw new Error("encrypted setting failed");
    const visitor = await browser.newContext(),
      customer = await visitor.newPage();
    await customer.goto(first.url);
    await expect(customer.locator(".site-header .brand")).toContainText(
      "Fensterblick",
    );
    await customer.goto(first.url + "/immobilien/native-test-wohnung");
    await expect(
      customer.getByRole("heading", {
        name: "NATIVTEST – kein echtes Angebot",
        level: 1,
      }),
    ).toBeVisible();
    await customer
      .getByRole("button", { name: "Interesse an dieser Immobilie" })
      .click();
    await customer.getByLabel("Vorname *").fill("Test");
    await customer.getByLabel("Nachname *").fill("Interessent");
    await customer
      .getByLabel("E-Mail *", { exact: true })
      .fill("test@example.com");
    await customer
      .getByLabel("Ihre Nachricht *")
      .fill("Synthetische Anfrage beim nativen Windows-Test.");
    await customer.getByRole("checkbox").check();
    await customer.getByRole("button", { name: "Anfrage absenden" }).click();
    await expect(
      customer.getByRole("heading", { name: "Vielen Dank für Ihr Vertrauen." }),
    ).toBeVisible();
    const inquiries = await (
      await context.request.get(first.url + "/api/admin/inquiries")
    ).json();
    if (inquiries.length !== 1) throw new Error("inquiry missing");
    if (
      (await visitor.request.get(first.url + "/api/admin/me")).status() !== 401
    )
      throw new Error("visitor gained admin access");
    if (
      (
        await (
          await context.request.get(first.url + "/api/admin/deliveries")
        ).json()
      ).length
    )
      throw new Error("unexpected external delivery job");
    const rejected = await context.request.post(
      first.url + "/__desktop/setup",
      { data: { email: "second@example.com", password, repeat: password } },
    );
    if (rejected.status() !== 409) throw new Error("setup stayed open");
    const exported = await context.request.post(
      first.url + "/api/admin/builder/project",
      { headers, data: { domain: "" } },
    );
    if (!exported.ok()) throw new Error("native project export failed");
    const exportPath = path.join(runtime, "test-export.zip");
    fs.writeFileSync(exportPath, await exported.body());
    try {
      const checked = cp.spawnSync(
        python,
        ["-X", "utf8", path.join(root, "scripts/check-desktop-export.py"), exportPath],
        { cwd: root, encoding: "utf8", timeout: 120000, windowsHide: true },
      );
      if (checked.status !== 0)
        throw new Error("native export/import failed: " + checked.stderr);
    } finally {
      fs.rmSync(exportPath, { force: true });
    }
    fs.mkdirSync(path.join(root, ".runtime", "test-evidence"), {
      recursive: true,
    });
    await page.goto(first.url + "/admin/inquiries");
    await expect(
      page.getByText("Test Interessent", { exact: true }),
    ).toBeVisible();
    await page.screenshot({
      path: path.join(root, ".runtime/test-evidence/admin.png"),
      fullPage: true,
    });
    command("stop");
    if (guarded && !guard.listening)
      throw new Error("foreign service was stopped");
    command("backup");
    if (
      !fs
        .readdirSync(path.join(root, "SICHERUNGEN"))
        .some((n) => n.endsWith(".zip"))
    )
      throw new Error("backup missing");
    command("launch");
    const second = state();
    if (second.pid === first.pid) throw new Error("supervisor did not restart");
    await login(page, second.url);
    const config = await (
      await context.request.get(second.url + "/api/admin/integrations/telegram")
    ).json();
    if (!config.secret_configured || config.token)
      throw new Error("encryption key was lost or secret exposed");
    if (
      (
        await (
          await context.request.get(second.url + "/api/admin/inquiries")
        ).json()
      ).length !== 1
    )
      throw new Error("data lost after restart");
    command("stop");
    fs.writeFileSync(
      path.join(root, ".runtime/test-evidence/result.json"),
      JSON.stringify(
        {
          result: "passed",
          system: process.platform,
          setup: true,
          duplicate_start: true,
          occupied_port_preserved: guarded,
          inquiry: true,
          project_export_and_import: true,
          restart: true,
          encrypted_key_preserved: true,
          backup: true,
          no_external_delivery: true,
        },
        null,
        2,
      ),
    );
    console.log(
      "Native smoke passed: setup, login, port conflict, upload, listing, inquiry, project export/import, restart, encrypted settings and backup. No messages sent.",
    );
  } finally {
    if (browser) await browser.close();
    if (guard && guard.listening)
      await new Promise((resolve) => guard.close(resolve));
    try {
      command("stop");
    } catch {}
  }
})().catch((error) => {
  console.error(error.message);
  process.exit(1);
});
