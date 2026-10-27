"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import {
  ArrowUpRight,
  Check,
  Copy,
  Download,
  Eye,
  FileCode2,
  Globe,
  History,
  Save,
  ShieldCheck,
  Upload,
  Building2,
  Server,
  ChevronRight,
  AlertCircle,
} from "lucide-react";
import { api, download } from "./api";

type Config = Record<string, any>;
type Props = { config: Config; setConfig: (v: Config) => void };
function Card({
  title,
  text,
  children,
  className = "",
}: {
  title: string;
  text?: string;
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <section className={"admin-card builder-card " + className}>
      <div className="card-header">
        <h2>{title}</h2>
        {text && <p>{text}</p>}
      </div>
      {children}
    </section>
  );
}
function Message({ message, error }: { message: string; error: boolean }) {
  return message ? (
    <div
      className={"notice " + (error ? "error" : "success")}
      role={error ? "alert" : "status"}
    >
      <AlertCircle size={17} />
      <span>{message}</span>
    </div>
  ) : null;
}
function Input({
  label,
  value,
  onChange,
  ...props
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  type?: string;
  placeholder?: string;
  maxLength?: number;
}) {
  return (
    <label>
      {label}
      <input
        value={value || ""}
        onChange={(e) => onChange(e.target.value)}
        maxLength={2000}
        {...props}
      />
    </label>
  );
}

export function CompanyForm({ config: c, setConfig: set }: Props) {
  const legal = (key: string, value: string) =>
    set({ ...c, legal: { ...c.legal, [key]: value, reviewed: false } });
  const company = (key: string, value: string) =>
    set({ ...c, [key]: value, legal: { ...c.legal, reviewed: false } });
  return (
    <div className="field-grid company-grid">
      <Input
        label="Firmenname"
        value={c.company}
        maxLength={100}
        onChange={(v) => company("company", v)}
        placeholder="Muster Immobilien GmbH"
      />
      <Input
        label="Rechtsform"
        value={c.legal.legal_form}
        onChange={(v) => legal("legal_form", v)}
        placeholder="z. B. GmbH oder Einzelunternehmen"
      />
      <Input
        label="Geschäftsführung / Vertretung"
        value={c.legal.representative}
        onChange={(v) => legal("representative", v)}
        placeholder="Name der vertretungsberechtigten Person"
      />
      <Input
        label="Anschrift"
        value={c.address}
        onChange={(v) => company("address", v)}
        placeholder="Straße und Hausnummer"
      />
      <Input
        label="Postleitzahl"
        value={c.legal.postcode}
        onChange={(v) => legal("postcode", v)}
      />
      <Input label="Ort" value={c.city} onChange={(v) => company("city", v)} />
      <Input
        label="E-Mail"
        type="email"
        value={c.email}
        onChange={(v) => company("email", v)}
      />
      <Input
        label="Telefon"
        type="tel"
        value={c.phone}
        onChange={(v) => company("phone", v)}
      />
      <Input
        label="Registergericht"
        value={c.legal.register_court}
        onChange={(v) => legal("register_court", v)}
        placeholder="Falls zutreffend"
      />
      <Input
        label="Handelsregisternummer"
        value={c.legal.register_number}
        onChange={(v) => legal("register_number", v)}
        placeholder="HRB … / HRA …, falls zutreffend"
      />
      <Input
        label="Umsatzsteuer-ID"
        value={c.legal.vat_id}
        onChange={(v) => legal("vat_id", v)}
        placeholder="Falls vorhanden"
      />
      <Input
        label="Aufsichtsbehörde"
        value={c.legal.supervisory_authority}
        onChange={(v) => legal("supervisory_authority", v)}
        placeholder="Falls erforderlich"
      />
      <Input
        label="Berufsrechtliche Angaben"
        value={c.legal.professional_rules}
        onChange={(v) => legal("professional_rules", v)}
      />
      <Input
        label="Inhaltlich verantwortlich"
        value={c.legal.responsible_content}
        onChange={(v) => legal("responsible_content", v)}
      />
      <label className="wide">
        Impressum
        <textarea
          rows={5}
          value={c.legal_text}
          onChange={(e) => company("legal_text", e.target.value)}
        />
      </label>
    </div>
  );
}

export function FrontendStudio({
  config: c,
  setConfig: set,
  companyOnly = false,
}: Props & { companyOnly?: boolean }) {
  const [prompt, setPrompt] = useState(""),
    [message, setMessage] = useState(""),
    [error, setError] = useState(false),
    [busy, setBusy] = useState(false);
  const [file, setFile] = useState<File | null>(null),
    [report, setReport] = useState<any>(null),
    [checks, setChecks] = useState<any>(null);
  async function action(job: () => Promise<void>) {
    setBusy(true);
    setMessage("");
    setError(false);
    try {
      await job();
    } catch (e: any) {
      setError(true);
      setMessage(e.message);
    } finally {
      setBusy(false);
    }
  }
  async function save() {
    const saved = await api("/admin/config", {
      method: "PUT",
      body: JSON.stringify(c),
    });
    set(saved);
    return saved;
  }
  async function generate() {
    await save();
    setPrompt((await api("/admin/builder/prompt")).prompt);
    setMessage("Prompt aus dem gespeicherten Firmenprofil erstellt.");
  }
  async function validate() {
    if (!file)
      throw new Error("Bitte zuerst eine JSON- oder ZIP-Datei auswählen.");
    const data = new FormData();
    data.append("file", file);
    const result = await api("/admin/builder/design/validate", {
      method: "POST",
      body: data,
    });
    setReport(result);
    setMessage(result.message);
  }
  return (
    <>
      {!companyOnly && (
        <nav className="studio-steps" aria-label="Frontend-Schritte">
          {[
            ["Firmendaten", "#firmendaten"],
            ["KI-Paket", "#ki-paket"],
            ["Frontend importieren", "#frontend-import"],
            ["Prüfen", "#frontend-pruefen"],
            ["Live gehen", "/admin/deployment"],
          ].map(([label, href], i) => (
            <Link href={href} key={href}>
              <span>{i + 1}</span>
              {label}
              {i < 4 && <ChevronRight size={14} />}
            </Link>
          ))}
        </nav>
      )}
      <div className="studio-toolbar">
        <span>
          <span className="draft-dot" /> Änderungen zuerst speichern und in der
          Vorschau prüfen.
        </span>
        <div className="button-row">
          <Link className="small-button" target="_blank" href="/?preview=1">
            <Eye size={15} />
            Vorschau
          </Link>
          <button
            className="button"
            disabled={busy}
            onClick={() =>
              action(async () => {
                await save();
                setMessage("Entwurf gespeichert.");
              })
            }
          >
            <Save size={15} />
            Entwurf speichern
          </button>
        </div>
      </div>
      <Message message={message} error={error} />
      <div className={companyOnly ? "" : "studio-grid"}>
        <div id="firmendaten">
          <Card
            title="Firma & Rechtliches"
            text="Einmal eintragen. Für Website und KI-Prompt verwenden."
          >
            <CompanyForm config={c} setConfig={set} />
            <button
              className="small-button"
              disabled={busy}
              onClick={() =>
                action(async () => {
                  await save();
                  const result = await api("/admin/builder/imprint");
                  set({
                    ...c,
                    legal_text: result.text,
                    legal: { ...c.legal, reviewed: false },
                  });
                  setMessage(
                    "Impressumsentwurf übernommen. Bitte ergänzen, prüfen und speichern.",
                  );
                })
              }
            >
              <FileCode2 size={15} />
              Impressumsentwurf aus Firmendaten
            </button>
            <p className="card-hint">
              Angaben nur ausfüllen, soweit sie auf dein Unternehmen zutreffen.
              Der Entwurf ersetzt keine rechtliche Prüfung.
            </p>
            {companyOnly && (
              <>
                <label>
                  Datenschutzerklärung
                  <textarea
                    rows={8}
                    value={c.privacy_text}
                    onChange={(e) =>
                      set({
                        ...c,
                        privacy_text: e.target.value,
                        legal: { ...c.legal, reviewed: false },
                      })
                    }
                  />
                </label>
                <label className="checkbox-label">
                  <input
                    type="checkbox"
                    checked={c.legal.reviewed}
                    onChange={(e) =>
                      set({
                        ...c,
                        legal: { ...c.legal, reviewed: e.target.checked },
                      })
                    }
                  />
                  Ich habe Impressum und Datenschutz für diesen Betrieb fachlich
                  prüfen lassen.
                </label>
              </>
            )}
          </Card>
        </div>
        {!companyOnly && (
          <div id="ki-paket">
            <Card
              title="Dein KI-Frontend-Paket"
              text="Für deine bevorzugte KI – mit verbindlicher Schnittstelle."
            >
              <Input
                label="Zielgruppe"
                value={c.frontend_brief.audience}
                onChange={(v) =>
                  set({
                    ...c,
                    frontend_brief: { ...c.frontend_brief, audience: v },
                  })
                }
              />
              <Input
                label="Gewünschter Stil"
                value={c.frontend_brief.style}
                onChange={(v) =>
                  set({
                    ...c,
                    frontend_brief: { ...c.frontend_brief, style: v },
                  })
                }
              />
              <label>
                Weitere Designwünsche
                <textarea
                  rows={3}
                  maxLength={6000}
                  value={c.frontend_brief.wishes}
                  onChange={(e) =>
                    set({
                      ...c,
                      frontend_brief: {
                        ...c.frontend_brief,
                        wishes: e.target.value,
                      },
                    })
                  }
                  placeholder="Farben, Aufbau, Tonalität …"
                />
              </label>
              <textarea
                className="prompt-preview"
                aria-label="Generierter KI-Prompt"
                readOnly
                value={
                  prompt ||
                  "Erstelle dein KI-Paket aus den Firmendaten. Der Prompt enthält den vollständigen Vertrag für Seiten, Immobilien, Formulare, Module und sichere Datenanbindung."
                }
                rows={8}
              />
              <div className="button-row">
                <button
                  className="button"
                  disabled={busy}
                  onClick={() => action(generate)}
                >
                  <FileCode2 size={16} />
                  Prompt erstellen
                </button>
                <button
                  className="small-button"
                  disabled={!prompt || busy}
                  onClick={() =>
                    action(async () => {
                      await navigator.clipboard.writeText(prompt);
                      setMessage("Prompt kopiert.");
                    })
                  }
                >
                  <Copy size={15} />
                  Kopieren
                </button>
              </div>
              <button
                className="small-button"
                disabled={!prompt || busy}
                onClick={() => {
                  const blob = new Blob([prompt], { type: "text/markdown" });
                  const url = URL.createObjectURL(blob);
                  const a = document.createElement("a");
                  a.href = url;
                  a.download = "Raumwerk-Prompt.md";
                  a.click();
                  setTimeout(() => URL.revokeObjectURL(url), 1000);
                }}
              >
                <Download size={15} />
                Prompt als Datei
              </button>
            </Card>
            <Card
              title="Referenzfrontend"
              text="Vollständiger Beispielcode · Manifest · API-Vertrag · Schemas · Prüfliste"
              className="reference-card"
            >
              <FileCode2 size={42} strokeWidth={1.2} />
              <p>
                Gib der KI den Prompt und dieses ZIP. Das Referenzfrontend
                unterstützt alle Funktionen des Baukastens und bleibt
                firmenneutral.
              </p>
              <button
                className="small-button"
                disabled={busy}
                onClick={() =>
                  action(async () => {
                    await save();
                    await download(
                      "/admin/builder/reference",
                      "Raumwerk-KI-Frontend.zip",
                    );
                    setMessage(
                      "Referenzpaket mit aktuellem Firmenprofil heruntergeladen.",
                    );
                  })
                }
              >
                <Download size={16} />
                Referenzpaket exportieren
              </button>
            </Card>
            <ThemeControls config={c} setConfig={set} />
          </div>
        )}
      </div>
      {!companyOnly && (
        <>
          <div className="studio-grid lower-grid">
            <Card
              title="Frontend importieren"
              text="KI-Ergebnis als manifest.json oder ZIP auswählen."
              className="import-card"
            >
              <div id="frontend-import">
                <label className="package-upload">
                  <Upload size={28} />
                  <strong>Designpaket auswählen</strong>
                  <span>JSON oder ZIP · maximal 10 MB</span>
                  <input
                    aria-label="Frontend-Designpaket"
                    type="file"
                    accept=".json,.zip"
                    onChange={(e) => {
                      setFile(e.target.files?.[0] || null);
                      setReport(null);
                    }}
                  />
                </label>
                <p className="card-hint">
                  Direkter Import unterstützt geprüfte Layout- und Theme-Daten.
                  Freie React-/CSS-Quellen liegen im Referenzpaket und erfordern
                  Einbau, Build und Tests; sie werden hier nicht installiert.
                </p>
                <div className="button-row">
                  <button
                    className="small-button"
                    disabled={busy || !file}
                    onClick={() => action(validate)}
                  >
                    <ShieldCheck size={16} />
                    Paket prüfen
                  </button>
                  <button
                    className="button"
                    disabled={busy || !report?.valid || !report?.available}
                    onClick={() =>
                      action(async () => {
                        await save();
                        const data = new FormData();
                        data.append("file", file!);
                        const result = await api(
                          "/admin/builder/design/import",
                          { method: "POST", body: data },
                        );
                        set(result.config);
                        setReport(null);
                        setMessage(result.message);
                      })
                    }
                  >
                    Als Entwurf übernehmen
                  </button>
                </div>
                {report && (
                  <div className="package-report">
                    <Check size={18} />
                    <div>
                      <strong>{report.manifest.name}</strong>
                      <p>
                        Version {report.manifest.version} ·{" "}
                        {report.manifest.pages.length} Seitentypen ·{" "}
                        {report.manifest.actions.length} Aktionen
                      </p>
                      <small>{report.message}</small>
                    </div>
                  </div>
                )}
              </div>
            </Card>
            <Card
              title="Prüfen & veröffentlichen"
              text="Datenvertrag und Medien prüfen, dann Vorschau ansehen."
            >
              <div id="frontend-pruefen">
                <button
                  className="small-button"
                  disabled={busy}
                  onClick={() =>
                    action(async () => {
                      await save();
                      const result = await api("/admin/builder/check");
                      setChecks(result);
                      setMessage(
                        result.valid
                          ? "Technische Prüfung bestanden. Hinweise und Vorschau vor Veröffentlichung prüfen."
                          : "Bitte die aufgeführten Fehler beheben.",
                      );
                    })
                  }
                >
                  <ShieldCheck size={16} />
                  Kompatibilität prüfen
                </button>
                {checks && <CheckList checks={checks.checks} />}
                <p className="card-hint">
                  Rechtstexte unter{" "}
                  <Link href="/admin/company">Firma & Rechtliches</Link> prüfen.
                  Ein Schema-Check ersetzt keinen Browsertest frei geänderter
                  Quellen.
                </p>
                <button
                  className="button"
                  disabled={busy}
                  onClick={() =>
                    action(async () => {
                      await save();
                      const result = await api("/admin/builder/check");
                      setChecks(result);
                      if (!result.valid)
                        throw new Error(
                          "Bitte zuerst die technischen Fehler beheben.",
                        );
                      await api("/admin/config/publish", { method: "POST" });
                      window.dispatchEvent(new Event("raumwerk:published"));
                      setMessage("Änderungen sind veröffentlicht.");
                    })
                  }
                >
                  Veröffentlichen
                  <ArrowUpRight size={16} />
                </button>
              </div>
            </Card>
          </div>
          <section className="studio-deploy">
            <div>
              <h2>Export & Livegang</h2>
              <p>
                Die fertige Website mit Adminbereich auf deinen VPS bringen.
              </p>
            </div>
            <div className="deploy-milestones">
              <span>
                <Building2 />
                Projektpaket<small>Inhalte & Medien</small>
              </span>
              <ChevronRight />
              <span>
                <Server />
                VPS & Domain<small>Ziel einrichten</small>
              </span>
              <ChevronRight />
              <span>
                <ShieldCheck />
                HTTPS & Start<small>Verbindung prüfen</small>
              </span>
            </div>
            <Link className="button" href="/admin/deployment">
              Deployment einrichten
              <ArrowUpRight size={16} />
            </Link>
          </section>
        </>
      )}
    </>
  );
}

function ThemeControls({ config: c, setConfig: set }: Props) {
  const update = (key: string, value: string | number) =>
    set({ ...c, frontend_theme: { ...c.frontend_theme, [key]: value } });
  return (
    <div className="admin-card builder-card">
      <details>
        <summary>Layout feinabstimmen</summary>
        <p>Auch ohne KI kannst du das importierbare Design hier bearbeiten.</p>
        <div className="field-grid">
          <label>
            Hero-Aufbau
            <select
              value={c.frontend_theme.hero_layout}
              onChange={(e) => update("hero_layout", e.target.value)}
            >
              <option value="cover">Große Bildfläche</option>
              <option value="split">Text und Bild geteilt</option>
            </select>
          </label>
          <label>
            Immobilienkarten
            <select
              value={c.frontend_theme.card_layout}
              onChange={(e) => update("card_layout", e.target.value)}
            >
              <option value="grid">Raster</option>
              <option value="list">Liste</option>
            </select>
          </label>
          <label>
            Abschnittsabstände
            <select
              value={c.frontend_theme.spacing}
              onChange={(e) => update("spacing", e.target.value)}
            >
              <option value="compact">Kompakt</option>
              <option value="normal">Normal</option>
              <option value="generous">Großzügig</option>
            </select>
          </label>
          <label>
            Schriftstil
            <select
              value={c.font}
              onChange={(e) => set({ ...c, font: e.target.value })}
            >
              <option value="modern">Modern</option>
              <option value="classic">Klassisch</option>
            </select>
          </label>
          {[
            ["primary", "Primärfarbe"],
            ["accent", "Akzentfarbe"],
          ].map(([key, label]) => (
            <label key={key}>
              {label}
              <input
                type="color"
                value={c[key]}
                onChange={(e) => set({ ...c, [key]: e.target.value })}
              />
            </label>
          ))}
          {[
            ["background", "Hintergrund"],
            ["foreground", "Textfarbe"],
          ].map(([key, label]) => (
            <label key={key}>
              {label}
              <input
                type="color"
                value={c.frontend_theme[key]}
                onChange={(e) => update(key, e.target.value)}
              />
            </label>
          ))}
          <label>
            Rundung (px)
            <input
              type="number"
              min={0}
              max={32}
              value={c.frontend_theme.radius}
              onChange={(e) => update("radius", Number(e.target.value))}
            />
          </label>
          <label>
            Inhaltsbreite (px)
            <input
              type="number"
              min={960}
              max={1600}
              step={10}
              value={c.frontend_theme.content_width}
              onChange={(e) => update("content_width", Number(e.target.value))}
            />
          </label>
          <label>
            Überschriftengröße
            <input
              type="number"
              min={0.8}
              max={1.3}
              step={0.05}
              value={c.frontend_theme.heading_scale}
              onChange={(e) => update("heading_scale", Number(e.target.value))}
            />
          </label>
        </div>
        <p className="card-hint">
          Änderungen oben speichern und in der Vorschau ansehen. Weitere
          Inhalte, Bilder und Abschnitte unter Design & Medien bzw. Seiten &
          Inhalte.
        </p>
      </details>
    </div>
  );
}

function CheckList({ checks }: { checks: any[] }) {
  return (
    <ul className="builder-checks">
      {checks.map((x) => (
        <li
          key={x.id}
          className={
            x.ok ? "passed" : x.level === "error" ? "failed" : "warning"
          }
        >
          {x.ok ? <Check size={17} /> : <AlertCircle size={17} />}
          <div>
            <strong>{x.title}</strong>
            <small>{x.detail}</small>
          </div>
          <span>
            {x.ok ? "OK" : x.level === "error" ? "Fehler" : "Hinweis"}
          </span>
        </li>
      ))}
    </ul>
  );
}

export function DeploymentPanel() {
  const [domain, setDomain] = useState(""),
    [plan, setPlan] = useState<any>(null),
    [busy, setBusy] = useState(false),
    [message, setMessage] = useState(""),
    [error, setError] = useState(false);
  async function run(job: () => Promise<void>) {
    setBusy(true);
    setError(false);
    setMessage("");
    try {
      await job();
    } catch (e: any) {
      setError(true);
      setMessage(e.message);
    } finally {
      setBusy(false);
    }
  }
  return (
    <>
      <div className="deploy-intro">
        <Globe size={34} strokeWidth={1.2} />
        <div>
          <h2>Ein Paket. Website und Admin dabei.</h2>
          <p>
            Dein VPS übernimmt das Hosting. Du brauchst eine Domain, einen
            erreichbaren Linux-Server und Docker. Die Anleitung führt dich durch
            DNS, Start und HTTPS.
          </p>
        </div>
      </div>
      <Message message={message} error={error} />
      <div className="studio-grid">
        <Card
          title="1 · Projektpaket exportieren"
          text="Der veröffentlichte Stand wird zur öffentlichen Website. Der gespeicherte Entwurf bleibt im Admin bearbeitbar."
        >
          <ul className="export-includes">
            <li>
              <Check />
              Website und Adminbereich inklusive Quellcode
            </li>
            <li>
              <Check />
              Firmendaten, Inhalte, Design und importierte Manifeste
            </li>
            <li>
              <Check />
              Alle Immobilien mit Status, Bildern und Objekt-PDFs
            </li>
            <li>
              <Check />
              Docker, HTTPS-Konfiguration und Startprogramm
            </li>
          </ul>
          <p className="card-hint">
            Vor dem Export Änderungen speichern und den gewünschten Stand
            veröffentlichen. Enthält auch interne Objekt-PDFs und
            Immobilienentwürfe; Paket vertraulich aufbewahren. Benutzer,
            Anfragen, ausgefüllte Selbstauskünfte und Zugangsdaten werden nicht
            mitgenommen. Am Ziel einen neuen Administrator anlegen;
            Integrationen neu einrichten. Anfragen landen zunächst im
            Adminbereich.
          </p>
          <button
            className="button"
            disabled={busy}
            onClick={() =>
              run(async () => {
                await download(
                  "/admin/builder/project",
                  "Raumwerk-Projekt.zip",
                  { domain },
                );
                setMessage(
                  "Projektpaket exportiert. Auf dem VPS entpacken und der Anleitung folgen.",
                );
              })
            }
          >
            <Download size={17} />
            Fertiges Projekt exportieren
          </button>
        </Card>
        <Card
          title="2 · VPS & Domain"
          text="Ubuntu 24.04 LTS · mindestens 2 CPU / 4 GB RAM empfohlen"
        >
          <Input
            label="Deine Domain"
            value={domain}
            onChange={(v) => {
              setDomain(v);
              setPlan(null);
            }}
            placeholder="immobilien.de"
          />
          <button
            className="small-button"
            disabled={busy || !domain}
            onClick={() =>
              run(async () =>
                setPlan(
                  await api("/admin/builder/deployment", {
                    method: "POST",
                    body: JSON.stringify({ domain }),
                  }),
                ),
              )
            }
          >
            <Server size={16} />
            Deployment vorbereiten
          </button>
          <p>
            Eine zusätzliche Shared-Hosting-Buchung ist nicht nötig. Dieses
            Formular kauft keinen Server und verändert dein DNS nicht.
          </p>
          <p>
            Ohne Domain kannst du das Paket mit STARTEN.cmd zuerst auf Windows
            testen.
          </p>
        </Card>
      </div>
      <Card
        title="3 · HTTPS & Start"
        text="Die ausführliche Anleitung liegt in jedem Export unter docs/DEPLOYMENT.md."
      >
        {plan ? (
          <>
            <ol className="deployment-steps">
              {plan.steps.map((s: string) => (
                <li key={s}>{s}</li>
              ))}
            </ol>
            <pre className="builder-code">{plan.command}</pre>
            <div className="button-row">
              <a
                className="small-button"
                href={plan.url}
                target="_blank"
                rel="noreferrer"
              >
                Website nach dem Start öffnen
                <ArrowUpRight size={15} />
              </a>
              <a
                className="small-button"
                href={plan.admin_url}
                target="_blank"
                rel="noreferrer"
              >
                Admin nach dem Start öffnen
                <ArrowUpRight size={15} />
              </a>
            </div>
            <p className="card-hint">
              Die Links funktionieren nach dem Start auf deinem VPS.
              DNS-Umstellung und Zertifikatsausstellung können Zeit brauchen.
              Dies ist ein Einrichtungsplan, keine Bestätigung einer bereits
              laufenden Website.
            </p>
          </>
        ) : (
          <div className="admin-empty small">
            <ShieldCheck size={32} />
            <h3>Bereit für deinen eigenen Server.</h3>
            <p>
              Trage oben deine Domain ein. Danach erhältst du die konkreten
              Schritte.
            </p>
          </div>
        )}
        <details>
          <summary>Bereits vorhandene Installation umstellen</summary>
          <p>
            Eine vorhandene .env wird aus Sicherheitsgründen erhalten.
            PUBLIC_ORIGIN auf https://deine-domain.de, COOKIE_SECURE auf 1 und
            DOMAIN auf deine-domain.de setzen. Geheime Werte behalten. Danach
            bash LIVE-STARTEN.sh ausführen. Bestehende Datenbank und Dateien
            werden nicht durch einen Export überschrieben. Vollständige Umzüge
            bestehender Benutzer und Anfragen erfolgen über das verschlüsselte
            Backup aus docs/OPERATIONS.md.
          </p>
        </details>
      </Card>
    </>
  );
}

export function VersionPanel({ config, setConfig }: Props) {
  const [rows, setRows] = useState<any[]>([]),
    [selected, setSelected] = useState<any>(null),
    [message, setMessage] = useState(""),
    [error, setError] = useState(false),
    [busy, setBusy] = useState(false);
  async function load() {
    setRows(await api("/admin/builder/versions"));
  }
  useEffect(() => {
    load().catch((e) => {
      setError(true);
      setMessage(e.message);
    });
  }, []);
  async function run(job: () => Promise<void>) {
    setBusy(true);
    setMessage("");
    setError(false);
    try {
      await job();
    } catch (e: any) {
      setError(true);
      setMessage(e.message);
    } finally {
      setBusy(false);
    }
  }
  return (
    <>
      <Message message={message} error={error} />
      <Card
        title="Versionen & Wiederherstellung"
        text="Die letzten 100 gespeicherten Konfigurationen. Immobilien, Anfragen, Team und Integrationen sind davon unabhängig."
      >
        <p>
          Vergleiche zuerst mit dem gespeicherten Entwurf. Wiederherstellung
          legt die ausgewählte Konfiguration als Entwurf ab; die öffentliche
          Website ändert sich erst beim Veröffentlichen. Ungespeicherte
          Änderungen vorher sichern.
        </p>
        <button
          className="small-button"
          disabled={busy}
          onClick={() =>
            run(async () => {
              await api("/admin/config", {
                method: "PUT",
                body: JSON.stringify(config),
              });
              await load();
              setMessage("Aktuellen Entwurf als Version gesichert.");
            })
          }
        >
          <Save size={15} />
          Aktuellen Entwurf sichern
        </button>
        <div className="version-list">
          {rows.map((r) => (
            <div key={r.id}>
              <History size={18} />
              <div>
                <strong>{r.label}</strong>
                <small>
                  #{r.id} · {new Date(r.created).toLocaleString("de-DE")} ·{" "}
                  {r.actor}
                </small>
                <span>
                  {r.changed_fields.length} geänderte Bereiche gegenüber
                  gespeichertem Entwurf
                </span>
              </div>
              <span className="badge">
                {r.kind === "published" ? "Veröffentlicht" : "Entwurf"}
              </span>
              <button
                className="small-button"
                disabled={busy}
                onClick={() =>
                  run(async () =>
                    setSelected(await api("/admin/builder/versions/" + r.id)),
                  )
                }
              >
                Vergleichen
              </button>
            </div>
          ))}
        </div>
        {!rows.length && (
          <p>Noch keine Versionen. Speichere den ersten Entwurf.</p>
        )}
      </Card>
      {selected && (
        <Card
          title={"Vergleich mit Version " + selected.id}
          text={selected.label}
        >
          {selected.changes.length ? (
            selected.changes.map((x: any) => (
              <details key={x.field}>
                <summary>{x.field}</summary>
                <div className="field-grid">
                  <label>
                    Gespeicherter Entwurf
                    <pre className="builder-code">
                      {JSON.stringify(x.current, null, 2)}
                    </pre>
                  </label>
                  <label>
                    Ausgewählte Version
                    <pre className="builder-code">
                      {JSON.stringify(x.saved, null, 2)}
                    </pre>
                  </label>
                </div>
              </details>
            ))
          ) : (
            <p>Keine Unterschiede zum gespeicherten Entwurf.</p>
          )}
          <button
            className="button"
            disabled={busy}
            onClick={() =>
              run(async () => {
                setConfig(
                  await api(
                    "/admin/builder/versions/" + selected.id + "/restore",
                    { method: "POST" },
                  ),
                );
                setSelected(null);
                await load();
                setMessage(
                  "Version als Entwurf wiederhergestellt. Bitte Vorschau prüfen und anschließend im Frontend-Studio veröffentlichen.",
                );
              })
            }
          >
            <History size={16} />
            Diese Version als Entwurf wiederherstellen
          </button>
        </Card>
      )}
    </>
  );
}
