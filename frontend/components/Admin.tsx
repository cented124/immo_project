"use client";
import { useState, useEffect, FormEvent } from "react";
import Link from "next/link";
import {
  LayoutDashboard,
  Building2,
  Inbox,
  Palette,
  FileText,
  Blocks,
  PlugZap,
  ChartNoAxesCombined,
  Settings,
  LogOut,
  ArrowUpRight,
  ArrowRight,
  Plus,
  Check,
  Search,
  ChevronRight,
  ChevronLeft,
  Eye,
  Save,
  Copy,
  Upload,
  Download,
  RefreshCw,
  Menu,
  X,
  Users,
  ShieldCheck,
  Globe,
  Send,
  Mail,
  ExternalLink,
  House,
  Layers,
  MoveUp,
  MoveDown,
  FileCode2,
  History,
  Rocket,
} from "lucide-react";
import { api, money, labels } from "./api";
import {
  AccountPanel,
  TeamControls,
  TemplateLibrary,
  FormRouting,
} from "./OperationalPanels";
import { FrontendStudio, DeploymentPanel, VersionPanel } from "./BuilderPanels";
type Any = any;
export default function Admin({ tab }: { tab: string }) {
  const [user, setUser] = useState<Any>(undefined),
    [config, setConfig] = useState<Any>(null),
    [publishedModules, setPublishedModules] = useState<Any>(null),
    [open, setOpen] = useState(false),
    [error, setError] = useState("");
  useEffect(() => {
    api("/admin/me")
      .then((u) => {
        setUser(u);
        api("/admin/config")
          .then((v) => {
            setConfig(v.draft);
            setPublishedModules(v.published.modules);
          })
          .catch((e) => setError(e.message));
      })
      .catch(() => setUser(null));
  }, []);
  useEffect(() => {
    const refresh = () =>
      api("/admin/config")
        .then((v) => setPublishedModules(v.published.modules))
        .catch(() => {});
    window.addEventListener("raumwerk:published", refresh);
    return () => window.removeEventListener("raumwerk:published", refresh);
  }, []);
  if (user === undefined)
    return (
      <div className="loading-screen">
        <span className="loading-mark">R</span>
        <p>Ihr Arbeitsbereich wird geladen.</p>
      </div>
    );
  if (!user)
    return (
      <Login
        onLogin={(u: Any) => {
          setUser(u);
          api("/admin/config").then((v) => {
            setConfig(v.draft);
            setPublishedModules(v.published.modules);
          });
        }}
      />
    );
  const navigation = [
    { id: "dashboard", title: "Übersicht", icon: LayoutDashboard },
    ...(user.role === "admin"
      ? [
          { id: "company", title: "Firma & Rechtliches", icon: Building2 },
          { id: "studio", title: "Frontend-Studio", icon: FileCode2 },
          { id: "design", title: "Design & Medien", icon: Palette },
          { id: "pages", title: "Seiten & Inhalte", icon: Layers },
          { id: "modules", title: "Module & Formulare", icon: Blocks },
        ]
      : []),
    {
      id: "properties",
      title: "Immobilien",
      icon: Building2,
      module: "properties",
    },
    { id: "inquiries", title: "Anfragen", icon: Inbox },
    { id: "documents", title: "Dokumente", icon: FileText },
    ...(user.role === "admin"
      ? [
          { id: "integrations", title: "Integrationen", icon: PlugZap },
          { id: "deployment", title: "Export & Livegang", icon: Rocket },
          { id: "versions", title: "Versionen", icon: History },
          { id: "settings", title: "Einstellungen", icon: Settings },
        ]
      : []),
    { id: "account", title: "Mein Konto", icon: ShieldCheck },
  ].filter((n) => !n.module || publishedModules?.[n.module]);
  const title = navigation.find((n) => n.id === tab)?.title || "Übersicht";
  return (
    <div className="admin-app">
      <aside className={"admin-sidebar " + (open ? "open" : "")}>
        <Link href="/admin" className="builder-logo">
          <span>
            r
            <span>
              <ArrowUpRight size={24} />
            </span>
          </span>
          <div>
            raumwerk<small>IMMOBILIEN · BAUKASTEN</small>
          </div>
        </Link>
        <div className="workspace">
          <div className="workspace-avatar">
            {config?.company.slice(0, 1) || "W"}
          </div>
          <div>
            <strong>{config?.company || "Ihre Website"}</strong>
            <small>Ihr Arbeitsbereich</small>
          </div>
          <ChevronRight size={15} />
        </div>
        <small className="sidebar-label">VERWALTEN & GESTALTEN</small>
        <nav>
          {navigation.map((n) => (
            <Link
              href={"/admin/" + n.id}
              key={n.id}
              className={tab === n.id ? "active" : ""}
              onClick={() => setOpen(false)}
            >
              <n.icon size={18} />
              {n.title}
              {tab === n.id && <span />}
            </Link>
          ))}
        </nav>
        <div className="sidebar-bottom">
          <div>
            <ShieldCheck size={16} />
            <span>
              {user.role === "admin" ? "Administrator" : "Mitarbeiter"}
              <small>{user.email}</small>
            </span>
          </div>
          <button
            onClick={async () => {
              await api("/admin/logout", { method: "POST" });
              setUser(null);
            }}
          >
            <LogOut size={16} />
            Abmelden
          </button>
          <Link href="/" target="_blank">
            Website öffnen <ArrowUpRight size={15} />
          </Link>
        </div>
      </aside>
      <div className="admin-main">
        <header className="admin-topbar">
          <div>
            <button
              className="icon-button admin-menu"
              aria-label="Menü"
              onClick={() => setOpen(!open)}
            >
              {open ? <X /> : <Menu />}
            </button>
            <span>Arbeitsbereich</span>
            <ChevronRight size={13} />
            <strong>{title}</strong>
          </div>
          <div>
            <span className="live-dot" />
            Ihr Arbeitsbereich
            <Link className="small-button" href="/" target="_blank">
              <Eye size={14} />
              Website ansehen <ArrowUpRight size={13} />
            </Link>
          </div>
        </header>
        <main className="admin-content">
          {error && <Notice error text={error} />}
          <div className="admin-heading">
            <div>
              <div className="admin-eyebrow">IHR RAUM FÜR MÖGLICHKEITEN</div>
              <h1>
                {title}
                {tab === "dashboard" ? "." : ""}
              </h1>
              <p>
                {
                  (
                    {
                      dashboard:
                        "Alles im Blick. Und Raum für Ihren nächsten Schritt.",
                      properties:
                        "Von der ersten Idee zum veröffentlichten Exposé.",
                      inquiries: "Aus Interesse werden gute Verbindungen.",
                      design: "Ihre Identität. Ihr Auftritt. Ihre Website.",
                      company: "Ihre Firmendaten. Für Website und KI-Prompt.",
                      studio:
                        "Deine Firmendaten. Dein KI-Briefing. Ein kompatibles Frontend.",
                      deployment:
                        "Ihre Website und Ihr Adminbereich. Auf Ihrem eigenen Server.",
                      versions:
                        "Änderungen vergleichen und einen früheren Stand zurückholen.",
                      pages:
                        "Geben Sie Ihrer Website Struktur und Persönlichkeit.",
                      modules:
                        "Genau die Funktionen, die Ihr Unternehmen braucht.",
                      integrations:
                        "Verbinden Sie Ihre Website mit Ihrem Arbeitsalltag.",
                      documents: "Unterlagen an einem geschützten Ort.",
                      settings:
                        "Ihr Unternehmen. Sicher und übersichtlich verwaltet.",
                    } as Any
                  )[tab]
                }
              </p>
            </div>
            {user.role === "admin" &&
              ["design", "pages", "modules"].includes(tab) && (
                <Link
                  className="small-button"
                  href="/?preview=1"
                  target="_blank"
                >
                  <Eye size={15} />
                  Entwurf ansehen <ArrowUpRight size={15} />
                </Link>
              )}
          </div>
          {!config ? (
            <p>Einstellungen werden geladen …</p>
          ) : tab === "account" ? (
            <AccountPanel />
          ) : tab === "dashboard" ? (
            <Dashboard config={config} />
          ) : tab === "properties" ? (
            <PropertyManager />
          ) : tab === "inquiries" ? (
            <InquiryManager admin={user.role === "admin"} />
          ) : tab === "documents" ? (
            <Documents
              config={config}
              setConfig={setConfig}
              admin={user.role === "admin"}
            />
          ) : user.role === "admin" && tab === "design" ? (
            <Design config={config} setConfig={setConfig} />
          ) : user.role === "admin" &&
            (tab === "studio" || tab === "company") ? (
            <FrontendStudio
              config={config}
              setConfig={setConfig}
              companyOnly={tab === "company"}
            />
          ) : user.role === "admin" && tab === "deployment" ? (
            <DeploymentPanel />
          ) : user.role === "admin" && tab === "versions" ? (
            <VersionPanel config={config} setConfig={setConfig} />
          ) : user.role === "admin" && tab === "pages" ? (
            <Pages config={config} setConfig={setConfig} />
          ) : user.role === "admin" && tab === "modules" ? (
            <Modules config={config} setConfig={setConfig} />
          ) : user.role === "admin" && tab === "integrations" ? (
            <Integrations />
          ) : user.role === "admin" && tab === "settings" ? (
            <SettingsPanel config={config} setConfig={setConfig} />
          ) : (
            <Notice error text="Dieser Bereich ist nicht verfügbar." />
          )}
        </main>
        <footer className="admin-footer">
          <span>
            raumwerk <i>·</i> Alles beginnt mit einer Perspektive.
          </span>
          <span>Ihr firmenneutraler Immobilien-Baukasten</span>
        </footer>
      </div>
    </div>
  );
}
function Login({ onLogin }: { onLogin: (u: Any) => void }) {
  const [error, setError] = useState(""),
    [busy, setBusy] = useState(false);
  async function submit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setBusy(true);
    setError("");
    const f = Object.fromEntries(new FormData(e.currentTarget));
    try {
      onLogin(
        await api("/admin/login", { method: "POST", body: JSON.stringify(f) }),
      );
    } catch (e: Any) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  }
  return (
    <div className="login-page">
      <div className="login-art">
        <img src="/architecture.png" alt="Moderne Architektur" />
        <div>
          <Link href="/" className="login-wordmark">
            raumwerk ↗
          </Link>
          <div>
            <span className="eyebrow">IHR RAUM FÜR MÖGLICHKEITEN</span>
            <h1>
              Ihre Immobilien.
              <br />
              Ihre Marke.
              <br />
              <span>Ihr nächster Schritt.</span>
            </h1>
            <p>
              Ein Baukasten. Alle Möglichkeiten.
              <br />
              Für das Unternehmen, das Sie daraus machen.
            </p>
          </div>
          <small>IMMOBILIEN WEITERDENKEN.</small>
        </div>
      </div>
      <div className="login-form">
        <Link href="/" className="back-link">
          <ChevronLeft size={15} />
          Zur Website
        </Link>
        <div>
          <div className="admin-eyebrow">WILLKOMMEN ZURÜCK</div>
          <h1>Schön, dass Sie da sind.</h1>
          <p>Melden Sie sich in Ihrem Arbeitsbereich an.</p>
          <form onSubmit={submit}>
            <label>
              E-Mail-Adresse
              <input
                type="email"
                name="email"
                required
                autoComplete="username"
                placeholder="name@unternehmen.de"
              />
            </label>
            <label>
              Passwort
              <input
                type="password"
                name="password"
                required
                autoComplete="current-password"
                placeholder="Ihr Passwort"
              />
            </label>
            {error && <Notice text={error} error />}
            <button className="button" disabled={busy}>
              {busy ? "Anmeldung läuft …" : "Im Arbeitsbereich anmelden"}
              <ArrowRight size={17} />
            </button>
          </form>
          <div className="login-help">
            <ShieldCheck size={18} />
            <p>
              Erste Einrichtung? Erstellen Sie Ihren Administrator mit dem
              sicheren Einrichtungsbefehl in der Installationsanleitung.
            </p>
          </div>
        </div>
        <small>Eine Website, die zu Ihrem Unternehmen passt.</small>
      </div>
    </div>
  );
}
export function Notice({
  text,
  error = false,
}: {
  text: string;
  error?: boolean;
}) {
  return (
    <div
      className={"notice " + (error ? "error" : "success")}
      role={error ? "alert" : "status"}
    >
      {error ? <ShieldCheck size={17} /> : <Check size={17} />}
      <span>{text}</span>
    </div>
  );
}
function Card({
  title,
  description,
  children,
}: {
  title: string;
  description?: string;
  children: React.ReactNode;
}) {
  return (
    <section className="admin-card">
      <div className="card-header">
        <h2>{title}</h2>
        {description && <p>{description}</p>}
      </div>
      {children}
    </section>
  );
}
function Toggle({
  label,
  description,
  checked,
  onChange,
}: {
  label: string;
  description?: string;
  checked: boolean;
  onChange: (v: boolean) => void;
}) {
  return (
    <label className="toggle-row">
      <div>
        <strong>{label}</strong>
        {description && <small>{description}</small>}
      </div>
      <input
        type="checkbox"
        role="switch"
        checked={checked}
        onChange={(e) => onChange(e.target.checked)}
      />
    </label>
  );
}
function Field({ label, value, onChange, type = "text", ...props }: Any) {
  return (
    <label>
      {label}
      <input
        type={type}
        value={value ?? ""}
        onChange={(e) =>
          onChange(
            type === "number"
              ? e.target.value === ""
                ? null
                : Number(e.target.value)
              : e.target.value,
          )
        }
        {...props}
      />
    </label>
  );
}
function Select({ label, value, onChange, options }: Any) {
  return (
    <label>
      {label}
      <select value={value} onChange={(e) => onChange(e.target.value)}>
        {options.map(([v, t]: string[]) => (
          <option value={v} key={v}>
            {t}
          </option>
        ))}
      </select>
    </label>
  );
}
function SaveBar({
  config,
  setConfig,
}: {
  config: Any;
  setConfig: (c: Any) => void;
}) {
  const [msg, setMsg] = useState(""),
    [error, setError] = useState(false),
    [busy, setBusy] = useState(false);
  async function save(publish = false) {
    setBusy(true);
    setMsg("");
    try {
      const c = await api("/admin/config", {
        method: "PUT",
        body: JSON.stringify(config),
      });
      setConfig(c);
      if (publish) {
        await api("/admin/config/publish", { method: "POST" });
        window.dispatchEvent(new Event("raumwerk:published"));
      }
      setError(false);
      setMsg(
        publish
          ? "Änderungen sind veröffentlicht."
          : "Entwurf gespeichert. Noch nicht öffentlich sichtbar.",
      );
    } catch (e: Any) {
      setError(true);
      setMsg(e.message);
    } finally {
      setBusy(false);
    }
  }
  return (
    <div className="save-area">
      {msg && <Notice text={msg} error={error} />}
      <div className="save-bar">
        <span>
          <span className="draft-dot" />
          Änderungen werden zuerst als Entwurf gespeichert.
        </span>
        <div>
          <button
            className="small-button"
            onClick={() => save()}
            disabled={busy}
          >
            <Save size={15} />
            Entwurf speichern
          </button>
          <button className="button" onClick={() => save(true)} disabled={busy}>
            {busy ? "Wird gespeichert …" : "Veröffentlichen"}
            <ArrowUpRight size={16} />
          </button>
        </div>
      </div>
    </div>
  );
}
function Dashboard({ config }: { config: Any }) {
  const [data, setData] = useState<Any>(null),
    [error, setError] = useState("");
  useEffect(() => {
    api("/admin/dashboard")
      .then(setData)
      .catch((e) => setError(e.message));
  }, []);
  if (error) return <Notice error text={error} />;
  if (!data) return <p>Dashboard wird geladen …</p>;
  return (
    <>
      <div className="dashboard-welcome">
        <div>
          <span>GUTEN TAG. GUTE PERSPEKTIVEN.</span>
          <h2>Was möchten Sie heute bewegen?</h2>
          <p>Ihre Website ist der Anfang. Machen Sie etwas daraus.</p>
          <Link
            href={
              config.modules.properties ? "/admin/properties" : "/admin/design"
            }
            className="button"
          >
            {config.modules.properties
              ? "Immobilie anlegen"
              : "Website gestalten"}
            <Plus size={17} />
          </Link>
        </div>
        <div className="welcome-architecture">
          <House size={128} strokeWidth={0.45} />
          <span>RAUM FÜR MEHR.</span>
        </div>
      </div>
      <div className="metric-grid">
        {[
          {
            label: "Neue Anfragen",
            value: data.new_inquiries,
            icon: Inbox,
            sub: "Noch nicht bearbeitet",
            link: "inquiries",
          },
          {
            label: "Veröffentlichte Immobilien",
            value: data.published,
            icon: Building2,
            sub: "Öffentlich sichtbare Angebote",
            link: "properties",
          },
          {
            label: "Seitenaufrufe",
            value: data.events?.pageview ?? "—",
            icon: ChartNoAxesCombined,
            sub: data.events
              ? "Seit Beginn der Erfassung"
              : "Analytics ist deaktiviert",
            link: "modules",
          },
          {
            label: "Zustellfehler",
            value: data.delivery_errors,
            icon: Send,
            sub: "Nach Wiederholungen fehlgeschlagen",
            link: "integrations",
          },
        ].map((x) => (
          <Link className="metric-card" key={x.label} href={"/admin/" + x.link}>
            <div>
              <span>{x.label}</span>
              <x.icon size={18} />
            </div>
            <strong>{x.value}</strong>
            <small>
              {x.sub}
              <ArrowUpRight size={13} />
            </small>
          </Link>
        ))}
      </div>
      <div className="dashboard-columns">
        <Card
          title="Die neuesten Anfragen"
          description="Menschen, die den nächsten Schritt gehen möchten."
        >
          {data.recent.length ? (
            <div className="recent-list">
              {data.recent.map((r: Any) => (
                <Link key={r.id} href="/admin/inquiries">
                  <div className="avatar">
                    {r.data.first_name[0]}
                    {r.data.last_name[0]}
                  </div>
                  <div>
                    <strong>
                      {r.data.first_name} {r.data.last_name}
                    </strong>
                    <small>
                      {r.data.subject} ·{" "}
                      {new Date(r.created).toLocaleDateString("de-DE")}
                    </small>
                  </div>
                  <span className={"badge " + r.status}>
                    {labels[r.status]}
                  </span>
                  <ChevronRight size={15} />
                </Link>
              ))}
            </div>
          ) : (
            <div className="admin-empty">
              <Inbox size={32} strokeWidth={1} />
              <h3>Hier beginnen neue Verbindungen.</h3>
              <p>Sobald eine Anfrage eingeht, finden Sie sie hier.</p>
            </div>
          )}
          <Link className="card-bottom-link" href="/admin/inquiries">
            Alle Anfragen ansehen
            <ArrowRight size={15} />
          </Link>
        </Card>
        <Card
          title="Ihr nächster Schritt"
          description="Ein guter Auftritt entsteht Stück für Stück."
        >
          <div className="checklist">
            {[
              {
                text: "Firmenidentität hinterlegen",
                done: !!config.email,
                link: "design",
              },
              {
                text: "Website nach Ihren Wünschen gestalten",
                done: config.company !== "RAUM & WERT",
                link: "design",
              },
              {
                text: "Erste Immobilie veröffentlichen",
                done: data.published > 0,
                link: "properties",
              },
              {
                text: "Zustellwege einrichten",
                done: config.modules.email || config.modules.telegram,
                link: "integrations",
              },
            ].map((x, i) => (
              <Link href={"/admin/" + x.link} key={x.text}>
                <span className={x.done ? "done" : ""}>
                  {x.done ? (
                    <Check size={13} />
                  ) : (
                    String(i + 1).padStart(2, "0")
                  )}
                </span>
                <strong>{x.text}</strong>
                <ChevronRight size={14} />
              </Link>
            ))}
          </div>
        </Card>
      </div>
      <div className="dashboard-columns">
        <Card
          title="Anfragen der letzten 30 Tage"
          description="Tatsächlich gespeicherte Anfragen pro Kalendertag."
        >
          {data.daily.length ? (
            <div className="bar-chart">
              {data.daily.map((d: Any) => (
                <div key={d.date}>
                  <span>{d.count}</span>
                  <i
                    style={{
                      height:
                        Math.max(
                          8,
                          (d.count /
                            Math.max(...data.daily.map((x: Any) => x.count))) *
                            100,
                        ) + "px",
                    }}
                  />
                  <small>{d.date.slice(5)}</small>
                </div>
              ))}
            </div>
          ) : (
            <div className="admin-empty small">
              <ChartNoAxesCombined size={26} />
              <p>Noch keine Anfragen in diesem Zeitraum.</p>
            </div>
          )}
        </Card>
        <Card
          title="Echte Ereignisse. Klare Einblicke."
          description="Keine externen Tracker, keine Nutzerprofile."
        >
          {data.events ? (
            <div className="analytics-values">
              {[
                ["Exposéaufrufe", "property_view"],
                ["Klicks auf Anfragebutton", "inquiry_click"],
                ["Angenommene Formulare", "submission"],
              ].map(([name, key]) => (
                <div key={key}>
                  <span>{name}</span>
                  <strong>{data.events[key]}</strong>
                </div>
              ))}
            </div>
          ) : (
            <div className="admin-empty small">
              <p>Die Ereigniserfassung ist deaktiviert.</p>
              <Link className="text-link" href="/admin/modules">
                Analytics konfigurieren
                <ArrowUpRight size={14} />
              </Link>
            </div>
          )}
          <p className="card-hint">
            {data.by_form
              .map((r: Any) => `${labels[r.kind] || r.kind}: ${r.count}`)
              .join(" · ") || "Noch keine Formularstatistik"}
          </p>
          {data.by_property.length > 0 && (
            <p className="card-hint">
              {data.by_property
                .map(
                  (r: Any) =>
                    `${r.property_id ? "Objekt #" + r.property_id : "Ohne Objekt"}: ${r.count}`,
                )
                .join(" · ")}
            </p>
          )}
        </Card>
      </div>
    </>
  );
}
function MediaUpload({
  purpose,
  onUpload,
  label = "Datei hochladen",
}: {
  purpose: string;
  onUpload: (f: Any) => void;
  label?: string;
}) {
  const [error, setError] = useState(""),
    [busy, setBusy] = useState(false);
  return (
    <div className="media-upload">
      <label className="upload-control">
        <Upload size={18} />
        {busy ? "Wird hochgeladen …" : label}
        <input
          type="file"
          disabled={busy}
          accept={
            ["image", "brand"].includes(purpose)
              ? "image/png,image/jpeg,image/webp"
              : "application/pdf"
          }
          onChange={async (e) => {
            const file = e.target.files?.[0];
            if (!file) return;
            setBusy(true);
            setError("");
            const fd = new FormData();
            fd.set("file", file);
            fd.set("purpose", purpose);
            try {
              onUpload(await api("/admin/files", { method: "POST", body: fd }));
            } catch (e: Any) {
              setError(e.message);
            } finally {
              setBusy(false);
            }
          }}
        />
      </label>
      {error && <Notice error text={error} />}
    </div>
  );
}
function Design({
  config: c,
  setConfig: set,
}: {
  config: Any;
  setConfig: (c: Any) => void;
}) {
  const [manifest, setManifest] = useState(""),
    [result, setResult] = useState("");
  const edit = (k: string, v: Any) => set({ ...c, [k]: v });
  return (
    <>
      <div className="settings-columns">
        <div>
          <Card
            title="Ihr Unternehmen"
            description="Alle Angaben werden zentral auf Ihrer Website verwendet."
          >
            <div className="field-grid">
              <Field
                label="Firmenname"
                value={c.company}
                onChange={(v: string) => edit("company", v)}
              />
              <Field
                label="Zusatz / Branche"
                value={c.tagline}
                onChange={(v: string) => edit("tagline", v)}
              />
              <Field
                label="Geschäfts-E-Mail"
                value={c.email}
                type="email"
                onChange={(v: string) => edit("email", v)}
              />
              <Field
                label="Telefonnummer"
                value={c.phone}
                onChange={(v: string) => edit("phone", v)}
              />
              <Field
                label="Ort / Region"
                value={c.city}
                onChange={(v: string) => edit("city", v)}
              />
              <Field
                label="Anschrift"
                value={c.address}
                onChange={(v: string) => edit("address", v)}
              />
            </div>
            <div className="field-grid">
              <div>
                <label>Unternehmenslogo</label>
                {c.logo && (
                  <img
                    className="logo-preview"
                    src={c.logo.replace("/public/", "/admin/")}
                    alt="Logo"
                  />
                )}
                <MediaUpload
                  purpose="brand"
                  label="Logo auswählen"
                  onUpload={(f) => edit("logo", f.url)}
                />
                {c.logo && (
                  <button
                    className="text-link"
                    onClick={() => edit("logo", "")}
                  >
                    Wortmarke verwenden
                  </button>
                )}
              </div>
              <div>
                <label>Favicon</label>
                <MediaUpload
                  purpose="brand"
                  label="Favicon auswählen"
                  onUpload={(f) => edit("favicon", f.url)}
                />
                {c.favicon && <small>Favicon hinterlegt</small>}
              </div>
            </div>
          </Card>
          <Card
            title="Farben & Typografie"
            description="Geben Sie Ihrer Website eine eigene Handschrift."
          >
            <div className="field-grid">
              <Field
                label="Hauptfarbe"
                type="color"
                value={c.primary}
                onChange={(v: string) => edit("primary", v)}
              />
              <Field
                label="Akzentfarbe"
                type="color"
                value={c.accent}
                onChange={(v: string) => edit("accent", v)}
              />
              <Select
                label="Schriftstil"
                value={c.font}
                onChange={(v: string) => edit("font", v)}
                options={[
                  ["modern", "Modern · Manrope & Barlow"],
                  ["classic", "Klassisch · Serifenschrift"],
                ]}
              />
            </div>
          </Card>
          <Card
            title="Template auswählen"
            description="Design wechseln. Immobilien, Formulare und Anfragen bleiben verbunden."
          >
            <div className="template-grid">
              {[
                ["atelier", "Atelier", "Klar. Architektonisch. Zeitlos."],
                ["editorial", "Editorial", "Warm. Ruhig. Persönlich."],
              ].map(([id, name, desc]) => (
                <button
                  key={id}
                  className={
                    "template-card " + (c.template === id ? "selected" : "")
                  }
                  onClick={() => edit("template", id)}
                >
                  <div className={"template-mini " + id}>
                    <span />
                    <i />
                    <b />
                    <div />
                  </div>
                  <strong>
                    {name}
                    {c.template === id && <Check size={15} />}
                  </strong>
                  <small>{desc}</small>
                </button>
              ))}
            </div>
            <details>
              <summary>Weiteres Frontend anschließen</summary>
              <p>
                JSON-Manifest prüfen und einen registrierten Adapter wählen.
                HTML und fremder JavaScript-Code werden nicht ausgeführt. Neue
                Adapter werden nach der dokumentierten Schnittstelle entwickelt.
              </p>
              <textarea
                value={manifest}
                onChange={(e) => setManifest(e.target.value)}
                rows={5}
                placeholder='{"id":"mein-design","name":"Mein Design","version":1,"adapter":"atelier",…}'
              />
              <button
                className="small-button"
                onClick={async () => {
                  try {
                    const r = await api("/admin/templates/validate", {
                      method: "POST",
                      body: manifest,
                    });
                    setResult(r.message);
                  } catch (e: Any) {
                    setResult(e.message);
                  }
                }}
              >
                Manifest prüfen
              </button>
              {result && <p>{result}</p>}
              <a
                className="text-link"
                href="/api/admin/help/templates"
                target="_blank"
                rel="noreferrer"
              >
                Adapter-Anleitung öffnen
                <ArrowUpRight size={14} />
              </a>
            </details>
          </Card>
          <TemplateLibrary config={c} setConfig={set} />
        </div>
        <aside>
          <div className="design-preview">
            <div className="preview-browser">
              <i />
              <i />
              <i />
              <span>IHRE WEBSITE</span>
            </div>
            <div className="mini-site" style={{ background: c.primary }}>
              <span>{c.company}</span>
              <small>{c.city} · IMMOBILIEN</small>
              <h2>{c.headline}</h2>
              <p>{c.introduction}</p>
              <b>{c.cta_label} ↗</b>
            </div>
            <div className="preview-caption">
              <Eye size={15} />
              Live-Vorschau Ihrer Einstellungen
            </div>
          </div>
          <div className="info-card">
            <Palette size={23} />
            <h3>Ihre Marke im Mittelpunkt.</h3>
            <p>
              Raumwerk ist Ihr Werkzeug. Was Ihre Besucher sehen, ist
              ausschließlich Ihr Unternehmen.
            </p>
          </div>
        </aside>
      </div>
      <SaveBar config={c} setConfig={set} />
    </>
  );
}
function Pages({
  config: c,
  setConfig: set,
}: {
  config: Any;
  setConfig: (c: Any) => void;
}) {
  const edit = (k: string, v: Any) => set({ ...c, [k]: v });
  return (
    <>
      <Card title="Startseite" description="Der erste Eindruck Ihrer Website.">
        <div className="field-grid">
          <label>
            Hauptüberschrift (Zeilenumbruch möglich)
            <textarea
              rows={3}
              value={c.headline}
              onChange={(e) => edit("headline", e.target.value)}
            />
          </label>
          <label>
            Einleitung
            <textarea
              rows={3}
              value={c.introduction}
              onChange={(e) => edit("introduction", e.target.value)}
            />
          </label>
          <Field
            label="Text des Hauptbuttons"
            value={c.cta_label}
            onChange={(v: string) => edit("cta_label", v)}
          />
          <Select
            label="Ziel des Hauptbuttons"
            value={c.cta_target}
            onChange={(v: string) => edit("cta_target", v)}
            options={[
              ["immobilien", "Immobilienübersicht"],
              ["kontakt", "Kontaktformular"],
            ]}
          />
          <Field
            label="Bildbeschreibung"
            value={c.hero_alt}
            onChange={(v: string) => edit("hero_alt", v)}
          />
          <div>
            <label>Titelbild</label>
            <MediaUpload
              purpose="brand"
              label="Eigenes Titelbild hochladen"
              onUpload={(f) => edit("hero_image", f.url)}
            />
          </div>
        </div>
        <div className="section-sort">
          {c.sections.map((s: Any, i: number) => (
            <div key={s.id}>
              <Toggle
                label={
                  (
                    {
                      hero: "Titelbereich",
                      services: "Leistungen",
                      properties: "Immobilien",
                      approach: "Vorstellung",
                      contact: "Kontaktaufruf",
                    } as Any
                  )[s.id]
                }
                checked={s.visible}
                onChange={(v) =>
                  edit(
                    "sections",
                    c.sections.map((x: Any, j: number) =>
                      j === i ? { ...x, visible: v } : x,
                    ),
                  )
                }
              />
              <button
                className="icon-button"
                disabled={i === 0}
                aria-label="Abschnitt nach oben"
                onClick={() => {
                  const sections = [...c.sections];
                  [sections[i - 1], sections[i]] = [
                    sections[i],
                    sections[i - 1],
                  ];
                  edit("sections", sections);
                }}
              >
                <MoveUp size={15} />
              </button>
              <button
                className="icon-button"
                disabled={i === c.sections.length - 1}
                aria-label="Abschnitt nach unten"
                onClick={() => {
                  const sections = [...c.sections];
                  [sections[i + 1], sections[i]] = [
                    sections[i],
                    sections[i + 1],
                  ];
                  edit("sections", sections);
                }}
              >
                <MoveDown size={15} />
              </button>
            </div>
          ))}
        </div>
      </Card>
      <Card
        title="Leistungen & Vorstellung"
        description="Auch diese Texte und Bilder gehören Ihrer Firma und lassen sich austauschen."
      >
        <div className="field-grid">
          <Field
            label="Überschrift Leistungen"
            value={c.services_heading}
            onChange={(v: string) => edit("services_heading", v)}
          />
          <Field
            label="Einleitung Leistungen"
            value={c.services_intro}
            onChange={(v: string) => edit("services_intro", v)}
          />
        </div>
        {c.services.map((service: Any, i: number) => (
          <details className="page-editor" key={i}>
            <summary>{service.title}</summary>
            <div className="field-grid">
              {[
                ["title", "Überschrift"],
                ["text", "Beschreibung"],
                ["label", "Buttontext"],
              ].map(([k, label]) => (
                <Field
                  key={k}
                  label={label}
                  value={service[k]}
                  onChange={(v: string) =>
                    edit(
                      "services",
                      c.services.map((x: Any, j: number) =>
                        i === j ? { ...x, [k]: v } : x,
                      ),
                    )
                  }
                />
              ))}
              <Select
                label="Zielseite"
                value={service.slug}
                onChange={(v: string) =>
                  edit(
                    "services",
                    c.services.map((x: Any, j: number) =>
                      i === j ? { ...x, slug: v } : x,
                    ),
                  )
                }
                options={c.pages.map((p: Any) => [p.slug, p.title])}
              />
            </div>
          </details>
        ))}
        <div className="field-grid">
          <label>
            Überschrift Vorstellung
            <textarea
              rows={2}
              value={c.approach_heading}
              onChange={(e) => edit("approach_heading", e.target.value)}
            />
          </label>
          <label>
            Vorstellungstext
            <textarea
              rows={4}
              value={c.approach_text}
              onChange={(e) => edit("approach_text", e.target.value)}
            />
          </label>
          <Field
            label="Bildbeschreibung Vorstellung"
            value={c.approach_alt}
            onChange={(v: string) => edit("approach_alt", v)}
          />
          <div>
            <label>Bild Vorstellung</label>
            <MediaUpload
              purpose="brand"
              label="Eigenes Bild hochladen"
              onUpload={(f) => edit("approach_image", f.url)}
            />
          </div>
        </div>
      </Card>
      <Card
        title="Seiten & Navigation"
        description="Aktive Seiten erscheinen in dieser Reihenfolge in der Navigation. Formulare nutzen die zentralen Zustellziele."
      >
        {c.pages.map((p: Any, i: number) => (
          <details key={i} className="page-editor">
            <summary>
              <span className={"status-dot " + (p.enabled ? "enabled" : "")} />
              {p.title}
              <span>/{p.slug}</span>
            </summary>
            <div className="field-grid">
              <Field
                label="Seitentitel / Navigationsname"
                value={p.title}
                onChange={(v: string) =>
                  edit(
                    "pages",
                    c.pages.map((x: Any, j: number) =>
                      j === i ? { ...x, title: v } : x,
                    ),
                  )
                }
              />
              <Field
                label="URL-Pfad"
                value={p.slug}
                onChange={(v: string) =>
                  set({
                    ...c,
                    pages: c.pages.map((x: Any, j: number) =>
                      j === i ? { ...x, slug: v } : x,
                    ),
                    services: c.services.map((s: Any) =>
                      s.slug === p.slug ? { ...s, slug: v } : s,
                    ),
                    forms: Object.fromEntries(
                      Object.entries(c.forms).map(([key, value]) => [
                        key === p.slug ? v : key,
                        value,
                      ]),
                    ),
                  })
                }
              />
            </div>
            <label>
              Seiteninhalt
              <textarea
                value={p.text}
                rows={5}
                onChange={(e) =>
                  edit(
                    "pages",
                    c.pages.map((x: Any, j: number) =>
                      j === i ? { ...x, text: e.target.value } : x,
                    ),
                  )
                }
              />
            </label>
            <Field
              label="SEO-Beschreibung"
              value={p.seo_description}
              onChange={(v: string) =>
                edit(
                  "pages",
                  c.pages.map((x: Any, j: number) =>
                    j === i ? { ...x, seo_description: v } : x,
                  ),
                )
              }
            />
            <Toggle
              label="Seite aktivieren"
              checked={p.enabled}
              onChange={(v) =>
                edit(
                  "pages",
                  c.pages.map((x: Any, j: number) =>
                    j === i ? { ...x, enabled: v } : x,
                  ),
                )
              }
            />
            <Toggle
              label="Anfrageformular anzeigen"
              checked={p.form}
              onChange={(v) =>
                edit(
                  "pages",
                  c.pages.map((x: Any, j: number) =>
                    j === i ? { ...x, form: v } : x,
                  ),
                )
              }
            />
            <div className="button-row">
              <button
                className="small-button"
                disabled={i === 0}
                onClick={() => {
                  const pages = [...c.pages];
                  [pages[i - 1], pages[i]] = [pages[i], pages[i - 1]];
                  edit("pages", pages);
                }}
              >
                <MoveUp size={14} />
                In Navigation nach oben
              </button>
              <button
                className="small-button danger"
                onClick={() =>
                  set({
                    ...c,
                    pages: c.pages.filter((_: Any, j: number) => j !== i),
                    services: c.services.filter((s: Any) => s.slug !== p.slug),
                    forms: Object.fromEntries(
                      Object.entries(c.forms).filter(([key]) => key !== p.slug),
                    ),
                  })
                }
              >
                Seite entfernen
              </button>
            </div>
          </details>
        ))}
        <button
          className="small-button"
          onClick={() =>
            edit("pages", [
              ...c.pages,
              {
                slug: "neue-seite-" + c.pages.length,
                title: "Neue Seite",
                enabled: false,
                text: "",
                form: false,
                seo_description: "",
              },
            ])
          }
        >
          <Plus size={15} />
          Seite hinzufügen
        </button>
      </Card>
      <Card title="Footer, Social Media & Suchmaschinen">
        <div className="field-grid">
          <Field
            label="SEO-Titel"
            value={c.seo_title}
            onChange={(v: string) => edit("seo_title", v)}
          />
          <Field
            label="SEO-Beschreibung"
            value={c.seo_description}
            onChange={(v: string) => edit("seo_description", v)}
          />
          <Field
            label="Footer-Text"
            value={c.footer_text}
            onChange={(v: string) => edit("footer_text", v)}
          />
          <label>
            Social-Media-Links (HTTPS, eine URL pro Zeile)
            <textarea
              value={c.social_links.join("\n")}
              onChange={(e) =>
                edit("social_links", e.target.value.split("\n").filter(Boolean))
              }
            />
          </label>
        </div>
      </Card>
      <SaveBar config={c} setConfig={set} />
    </>
  );
}
function Modules({
  config: c,
  setConfig: set,
}: {
  config: Any;
  setConfig: (c: Any) => void;
}) {
  return (
    <>
      <div className="modules-grid">
        {[
          [
            "contact",
            "Kontaktformular",
            "Anfragen direkt auf Ihrer Website empfangen.",
            Inbox,
          ],
          [
            "properties",
            "Immobilienangebote",
            "Objekte verwalten und als Exposé veröffentlichen.",
            Building2,
          ],
          [
            "applications",
            "Immobilienbewerbungen",
            "Interesse eindeutig mit einem Objekt verbinden.",
            Users,
          ],
          [
            "disclosure",
            "Selbstauskunft",
            "Ihr eigenes PDF zum Download bereitstellen.",
            FileText,
          ],
          [
            "email",
            "E-Mail-Zustellung",
            "Anfragen über Ihren SMTP-Server zustellen.",
            Mail,
          ],
          [
            "telegram",
            "Telegram-Zustellung",
            "Benachrichtigungen über Ihren Firmenbot.",
            Send,
          ],
          [
            "analytics",
            "Eigene Analytics",
            "Datensparsame Ereignisse ohne externe Tracker.",
            ChartNoAxesCombined,
          ],
        ].map(([id, name, text, Icon]: Any) => (
          <div className="module-card" key={id}>
            <Icon size={24} strokeWidth={1.3} />
            <Toggle
              label={name}
              description={text}
              checked={c.modules[id]}
              onChange={(v) =>
                set({
                  ...c,
                  modules: { ...c.modules, [id]: v },
                  forms:
                    !v && ["email", "telegram"].includes(id)
                      ? Object.fromEntries(
                          Object.entries(c.forms).map(
                            ([key, value]: [string, any]) => [
                              key,
                              { ...value, [id]: false },
                            ],
                          ),
                        )
                      : c.forms,
                })
              }
            />
            <small>
              {c.modules[id]
                ? "Im Entwurf aktiviert"
                : "Im Entwurf deaktiviert"}
            </small>
          </div>
        ))}
      </div>
      <Notice text="Deaktivierte Module verschwinden nach Veröffentlichung aus Website und Navigation. Die zugehörigen öffentlichen API-Funktionen und Dateizugriffe werden ebenfalls gesperrt." />
      <Card
        title="Formulare & Zustellziele"
        description="Jedes Formular kann mehrere Ziele gleichzeitig verwenden."
      >
        {["contact", "application"].map((kind) => (
          <div className="form-targets" key={kind}>
            <h3>{labels[kind]}</h3>
            {[
              [
                "store",
                "Im Adminbereich speichern",
                "Dauerhafte Speicherung bis zur eingestellten Löschfrist.",
              ],
              [
                "email",
                "Per E-Mail zustellen",
                "Zuerst E-Mail-Modul aktivieren und SMTP einrichten.",
              ],
              [
                "telegram",
                "Per Telegram zustellen",
                "Zuerst Telegram-Modul und Bot einrichten.",
              ],
              [
                "phone_required",
                "Telefon als Pflichtangabe",
                "Name, E-Mail, Nachricht und Datenschutzhinweis bleiben verpflichtend.",
              ],
            ].map(([k, name, text]) => (
              <Toggle
                key={k}
                label={name}
                description={text}
                checked={c.forms[kind][k]}
                onChange={(v) =>
                  set({
                    ...c,
                    forms: { ...c.forms, [kind]: { ...c.forms[kind], [k]: v } },
                  })
                }
              />
            ))}
          </div>
        ))}
        <p className="card-hint">
          Ohne dauerhafte Speicherung werden Anfragedaten ausschließlich
          technisch für höchstens 24 Stunden verarbeitet. Fehlgeschlagene
          Zustellungen müssen innerhalb dieses Zeitraums bearbeitet werden.
        </p>
      </Card>
      <FormRouting config={c} setConfig={set} />
      <SaveBar config={c} setConfig={set} />
    </>
  );
}
function Integrations() {
  const [channel, setChannel] = useState("email"),
    [c, setC] = useState<Any>(null),
    [msg, setMsg] = useState(""),
    [error, setError] = useState(false),
    [busy, setBusy] = useState(false),
    [deliveries, setDeliveries] = useState<Any[]>([]);
  const refresh = () =>
    api("/admin/deliveries")
      .then(setDeliveries)
      .catch(() => {});
  useEffect(() => {
    let active = true;
    setC(null);
    setMsg("");
    api("/admin/integrations/" + channel)
      .then(
        (v) =>
          active &&
          setC(
            channel === "email"
              ? {
                  host: "",
                  port: 587,
                  tls: "starttls",
                  username: "",
                  password: "",
                  sender_name: "",
                  sender: "",
                  recipients: [],
                  confirmation: false,
                  ...v,
                }
              : {
                  token: "",
                  chat_id: "",
                  include_details: false,
                  types: ["contact", "application"],
                  ...v,
                },
          ),
      )
      .catch((e) => {
        if (!active) return;
        setMsg(e.message);
        setError(true);
      });
    refresh();
    return () => {
      active = false;
    };
  }, [channel]);
  async function save(test = false) {
    setBusy(true);
    setMsg("");
    try {
      await api("/admin/integrations/" + channel, {
        method: "PUT",
        body: JSON.stringify(c),
      });
      const r = test
        ? await api("/admin/integrations/" + channel + "/test", {
            method: "POST",
          })
        : null;
      setError(false);
      setMsg(r?.message || "Einstellungen verschlüsselt gespeichert.");
      setC({ ...c, password: "", token: "", secret_configured: true });
      refresh();
    } catch (e: Any) {
      setError(true);
      setMsg(e.message);
    } finally {
      setBusy(false);
    }
  }
  const edit = (k: string, v: Any) => setC({ ...c, [k]: v });
  return (
    <>
      <div className="tab-bar">
        <button
          className={channel === "email" ? "active" : ""}
          disabled={busy}
          onClick={() => {
            if (channel !== "email") {
              setC(null);
              setChannel("email");
            }
          }}
        >
          <Mail size={16} />
          E-Mail / SMTP
        </button>
        <button
          className={channel === "telegram" ? "active" : ""}
          disabled={busy}
          onClick={() => {
            if (channel !== "telegram") {
              setC(null);
              setChannel("telegram");
            }
          }}
        >
          <Send size={16} />
          Telegram
        </button>
      </div>
      <div className="settings-columns">
        <Card
          title={
            channel === "email"
              ? "E-Mails zuverlässig versenden"
              : "Ihr direkter Draht zu Telegram"
          }
          description="Zugangsdaten bleiben serverseitig verschlüsselt. Leere Geheimnisfelder behalten den gespeicherten Wert."
        >
          {c ? (
            channel === "email" ? (
              <div className="field-grid">
                <Field
                  label="SMTP-Host"
                  value={c.host}
                  onChange={(v: string) => edit("host", v)}
                />
                <Field
                  label="Port"
                  type="number"
                  value={c.port}
                  onChange={(v: number) => edit("port", v)}
                />
                <Select
                  label="Verschlüsselung"
                  value={c.tls}
                  onChange={(v: string) => edit("tls", v)}
                  options={[
                    ["starttls", "STARTTLS (meist 587)"],
                    ["ssl", "TLS (meist 465)"],
                    ["none", "Unverschlüsselt · nur lokale Tests"],
                  ]}
                />
                <Field
                  label="Benutzername"
                  value={c.username}
                  onChange={(v: string) => edit("username", v)}
                />
                <Field
                  label={
                    c.secret_configured
                      ? "Passwort (gespeichert, maskiert)"
                      : "SMTP-Passwort"
                  }
                  type="password"
                  autoComplete="new-password"
                  value={c.password}
                  onChange={(v: string) => edit("password", v)}
                />
                <Field
                  label="Absendername"
                  value={c.sender_name}
                  onChange={(v: string) => edit("sender_name", v)}
                />
                <Field
                  label="Verifizierte Absenderadresse"
                  type="email"
                  value={c.sender}
                  onChange={(v: string) => edit("sender", v)}
                />
                <Field
                  label="Empfänger (mit Komma trennen)"
                  value={c.recipients.join(", ")}
                  onChange={(v: string) =>
                    edit(
                      "recipients",
                      v.split(",").map((s) => s.trim()),
                    )
                  }
                />
                <Toggle
                  label="Eingangsbestätigung senden"
                  description="An die E-Mail-Adresse der angenommenen Anfrage."
                  checked={c.confirmation}
                  onChange={(v) => edit("confirmation", v)}
                />
              </div>
            ) : (
              <>
                <div className="field-grid">
                  <Field
                    label={
                      c.secret_configured
                        ? "Bot-Token (gespeichert, maskiert)"
                        : "Bot-Token"
                    }
                    type="password"
                    autoComplete="new-password"
                    value={c.token}
                    onChange={(v: string) => edit("token", v)}
                  />
                  <Field
                    label="Ziel-Chat-ID"
                    value={c.chat_id}
                    onChange={(v: string) => edit("chat_id", v)}
                  />
                </div>
                <Toggle
                  label="Kontaktdaten und Nachricht übertragen"
                  description="Standardmäßig wird nur eine Benachrichtigung versendet. Dokumente bleiben immer privat."
                  checked={c.include_details}
                  onChange={(v) => edit("include_details", v)}
                />
                {["contact", "application"].map((kind) => (
                  <Toggle
                    key={kind}
                    label={labels[kind] + " benachrichtigen"}
                    checked={c.types.includes(kind)}
                    onChange={(v) =>
                      edit(
                        "types",
                        v
                          ? [...c.types, kind]
                          : c.types.filter((x: string) => x !== kind),
                      )
                    }
                  />
                ))}
              </>
            )
          ) : (
            <p>Einstellungen werden geladen …</p>
          )}
          {msg && <Notice error={error} text={msg} />}
          <div className="button-row">
            <button
              className="small-button"
              onClick={() => save()}
              disabled={busy || !c}
            >
              <Save size={15} />
              Speichern
            </button>
            <button
              className="button"
              onClick={() => save(true)}
              disabled={busy || !c}
            >
              {busy
                ? "Wird geprüft …"
                : channel === "email"
                  ? "Test-E-Mail senden"
                  : "Testnachricht senden"}
              <Send size={15} />
            </button>
          </div>
        </Card>
        <aside className="info-card">
          <PlugZap size={26} />
          <h3>
            {channel === "email"
              ? "SMTP statt IMAP."
              : "In wenigen Schritten verbunden."}
          </h3>
          {channel === "email" ? (
            <>
              <p>
                Verwenden Sie die SMTP-Daten Ihres E-Mail-Anbieters. Die
                Firmenadresse ist der Absender; Interessenten werden als
                Reply-To eingetragen.
              </p>
              <p>
                Verifizieren Sie die Absenderadresse bei Ihrem Anbieter. Der
                Verbindungstest prüft die Annahme durch den SMTP-Server, nicht
                den Eingang im Postfach.
              </p>
            </>
          ) : (
            <ol>
              <li>Erstellen Sie mit @BotFather einen Bot.</li>
              <li>
                Öffnen Sie den Bot mit Ihrem Firmenaccount und senden Sie
                /start. Für Gruppen: Bot zur Firmengruppe hinzufügen.
              </li>
              <li>
                Ermitteln Sie die richtige Chat-ID über die offizielle Bot API.
              </li>
              <li>Token und Chat-ID speichern, Testnachricht senden.</li>
            </ol>
          )}
          <p>
            Aktivieren Sie anschließend das Modul und wählen Sie den Zustellweg
            je Formular unter „Module & Formulare“.
          </p>
        </aside>
      </div>
      <Card
        title="Zustellprotokoll"
        description="Angenommen bedeutet gespeichert. Versendet bedeutet vom Zielserver bestätigt."
      >
        <button className="small-button" onClick={refresh}>
          <RefreshCw size={14} />
          Aktualisieren
        </button>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Anfrage</th>
                <th>Ziel</th>
                <th>Status</th>
                <th>Versuche</th>
                <th>Ergebnis</th>
                <th />
              </tr>
            </thead>
            <tbody>
              {deliveries.map((d) => (
                <tr key={d.id}>
                  <td>#{d.inquiry_id}</td>
                  <td>{labels[d.channel]}</td>
                  <td>
                    <span className={"badge " + d.status}>
                      {labels[d.status]}
                    </span>
                  </td>
                  <td>{d.attempts} / 4</td>
                  <td>{d.error || "—"}</td>
                  <td>
                    {d.status !== "sent" && (
                      <button
                        className="small-button"
                        onClick={async () => {
                          try {
                            await api("/admin/deliveries/" + d.id + "/retry", {
                              method: "POST",
                            });
                            refresh();
                          } catch (e: Any) {
                            setError(true);
                            setMsg(e.message);
                          }
                        }}
                      >
                        Erneut versuchen
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {!deliveries.length && (
            <div className="admin-empty small">
              <Send size={25} />
              <p>Noch keine externen Zustellungen.</p>
            </div>
          )}
        </div>
      </Card>
    </>
  );
}
function InquiryManager({ admin }: { admin: boolean }) {
  const [items, setItems] = useState<Any[]>([]),
    [selected, setSelected] = useState<Any>(null),
    [q, setQ] = useState(""),
    [status, setStatus] = useState(""),
    [kind, setKind] = useState(""),
    [pid, setPid] = useState(""),
    [from, setFrom] = useState(""),
    [to, setTo] = useState(""),
    [msg, setMsg] = useState(""),
    [error, setError] = useState(false);
  const load = () =>
    api(
      "/admin/inquiries?" +
        new URLSearchParams({
          q,
          status,
          kind,
          property_id: pid || "0",
          date_from: from,
          date_to: to,
        }),
    )
      .then(setItems)
      .catch((e) => {
        setError(true);
        setMsg(e.message);
      });
  useEffect(() => {
    load();
  }, [q, status, kind, pid, from, to]);
  return (
    <>
      {msg && <Notice text={msg} error={error} />}
      <div className="filter-toolbar">
        <label className="search-input">
          <Search size={16} />
          <input
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder="Name, E-Mail oder Nachricht suchen"
            aria-label="Anfragen durchsuchen"
          />
        </label>
        <select
          aria-label="Anfragestatus"
          value={status}
          onChange={(e) => setStatus(e.target.value)}
        >
          <option value="">Alle Status</option>
          {["new", "processing", "answered", "closed"].map((x) => (
            <option value={x} key={x}>
              {labels[x]}
            </option>
          ))}
        </select>
        <select
          aria-label="Anfragetyp"
          value={kind}
          onChange={(e) => setKind(e.target.value)}
        >
          <option value="">Alle Formulare</option>
          <option value="contact">Kontakt</option>
          <option value="application">Bewerbung</option>
        </select>
        <a
          href={
            "/api/admin/export?" +
            new URLSearchParams({
              q,
              status,
              kind,
              property_id: pid || "0",
              date_from: from,
              date_to: to,
            })
          }
          className="small-button"
        >
          <Download size={15} />
          CSV exportieren
        </a>
      </div>
      <div className="filter-toolbar">
        <Field
          label="Objekt-ID"
          type="number"
          min="1"
          value={pid}
          onChange={setPid}
        />
        <Field label="Ab Datum" type="date" value={from} onChange={setFrom} />
        <Field label="Bis Datum" type="date" value={to} onChange={setTo} />
      </div>
      <div className="admin-card table-wrap">
        <table>
          <thead>
            <tr>
              <th>Interessent</th>
              <th>Anliegen</th>
              <th>Immobilie</th>
              <th>Eingang</th>
              <th>Status</th>
              <th />
            </tr>
          </thead>
          <tbody>
            {items.map((r) => (
              <tr
                key={r.id}
                onClick={() => setSelected({ ...r })}
                className="clickable"
              >
                <td>
                  <strong>
                    {r.data.first_name} {r.data.last_name}
                  </strong>
                  <small>{r.data.email}</small>
                </td>
                <td>
                  {r.data.subject}
                  <small>{labels[r.kind]}</small>
                </td>
                <td>{r.property_id ? "#" + r.property_id : "—"}</td>
                <td>{new Date(r.created).toLocaleDateString("de-DE")}</td>
                <td>
                  <span className={"badge " + r.status}>
                    {labels[r.status]}
                  </span>
                </td>
                <td>
                  <ChevronRight size={16} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {!items.length && (
          <div className="admin-empty">
            <Inbox size={36} strokeWidth={1} />
            <h3>Platz für neue Verbindungen.</h3>
            <p>Hier erscheinen Ihre gespeicherten Anfragen.</p>
          </div>
        )}
      </div>
      {selected && (
        <div className="modal-backdrop">
          <section
            className="modal"
            role="dialog"
            aria-modal="true"
            aria-label="Anfrage bearbeiten"
          >
            <button
              className="modal-close icon-button"
              aria-label="Schließen"
              onClick={() => setSelected(null)}
            >
              <X />
            </button>
            <div className="admin-eyebrow">ANFRAGE #{selected.id}</div>
            <h2>
              {selected.data.first_name} {selected.data.last_name}
            </h2>
            <p>
              {selected.data.email}
              {selected.data.phone ? " · " + selected.data.phone : ""}
            </p>
            <p>
              <strong>{selected.data.subject}</strong>
              {selected.property_id ? " · Objekt #" + selected.property_id : ""}
            </p>
            <p className="message-body preserve">{selected.data.message}</p>
            <Select
              label="Bearbeitungsstatus"
              value={selected.status}
              onChange={(v: string) => setSelected({ ...selected, status: v })}
              options={["new", "processing", "answered", "closed"].map((x) => [
                x,
                labels[x],
              ])}
            />
            <label>
              Interne Notizen
              <textarea
                rows={4}
                value={selected.notes}
                onChange={(e) =>
                  setSelected({ ...selected, notes: e.target.value })
                }
              />
            </label>
            <div className="button-row">
              <button
                className="button"
                onClick={async () => {
                  try {
                    await api("/admin/inquiries/" + selected.id, {
                      method: "PATCH",
                      body: JSON.stringify({
                        status: selected.status,
                        notes: selected.notes,
                      }),
                    });
                    setSelected(null);
                    load();
                    setError(false);
                    setMsg("Anfrage aktualisiert.");
                  } catch (e: Any) {
                    setError(true);
                    setMsg(e.message);
                  }
                }}
              >
                Änderungen speichern
                <Check size={15} />
              </button>
              {admin && (
                <button
                  className="small-button danger"
                  onClick={async () => {
                    if (
                      !confirm(
                        "Anfrage und zugehörige Dokumente endgültig löschen?",
                      )
                    )
                      return;
                    try {
                      await api("/admin/inquiries/" + selected.id, {
                        method: "DELETE",
                      });
                      setSelected(null);
                      load();
                    } catch (e: Any) {
                      setError(true);
                      setMsg(e.message);
                    }
                  }}
                >
                  Löschen
                </button>
              )}
            </div>
            <small>
              Datenschutzhinweis bestätigt:{" "}
              {new Date(selected.data.consent_at).toLocaleString("de-DE")}
            </small>
          </section>
        </div>
      )}
    </>
  );
}
function Documents({
  config: c,
  setConfig: set,
  admin,
}: {
  config: Any;
  setConfig: (c: Any) => void;
  admin: boolean;
}) {
  const [files, setFiles] = useState<Any[]>([]),
    [error, setError] = useState("");
  useEffect(() => {
    api("/admin/files")
      .then(setFiles)
      .catch((e) => setError(e.message));
  }, []);
  return (
    <>
      {error && <Notice text={error} error />}
      {admin && (
        <Card
          title="Ihre Selbstauskunft"
          description="Verwenden Sie ausschließlich Ihr eigenes, freigegebenes Dokument. Es wird kein Ersatz-PDF erzeugt."
        >
          <p>
            {c.disclosure_pdf
              ? "Ein PDF ist im Entwurf ausgewählt."
              : "Noch kein eigenes PDF hinterlegt. Das Modul bleibt bis zum Upload deaktiviert."}
          </p>
          <MediaUpload
            purpose="template"
            label="Eigenes PDF hochladen / austauschen"
            onUpload={(f) => {
              set({ ...c, disclosure_pdf: f.id });
              setFiles([f, ...files]);
            }}
          />
          <label>
            Erklärungstext
            <textarea
              rows={4}
              value={c.disclosure_text}
              onChange={(e) => set({ ...c, disclosure_text: e.target.value })}
            />
          </label>
          <Toggle
            label="Sichere Rückgabe aktivieren"
            description="Nur PDF, mit bestehender Anfragekennung und passender E-Mail-Adresse. Unterlagen bleiben privat."
            checked={c.disclosure_returns}
            onChange={(v) => set({ ...c, disclosure_returns: v })}
          />
          <SaveBar config={c} setConfig={set} />
        </Card>
      )}
      <Card
        title="Geschützte Dateien"
        description="Zurückgesendete Dokumente und Exposé-Unterlagen sind nur nach Anmeldung abrufbar."
      >
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Datei</th>
                <th>Verwendung</th>
                <th>Zuordnung</th>
                <th>Größe</th>
                <th />
              </tr>
            </thead>
            <tbody>
              {files.map((f) => (
                <tr key={f.id}>
                  <td>
                    <FileText size={16} /> {f.name}
                  </td>
                  <td>
                    {
                      (
                        {
                          return: "Private Rückgabe",
                          template: "Selbstauskunft-Vorlage",
                          document: "Privates Exposé-Dokument",
                          image: "Immobilienbild",
                          brand: "Design-Medium",
                        } as Any
                      )[f.purpose]
                    }
                  </td>
                  <td>
                    {f.inquiry_id
                      ? "Anfrage #" + f.inquiry_id
                      : f.property_id
                        ? "Objekt #" + f.property_id
                        : "—"}
                  </td>
                  <td>{Math.ceil(f.size / 1024)} KB</td>
                  <td>
                    <a
                      className="small-button"
                      href={"/api/admin/files/" + f.id}
                    >
                      <Download size={14} />
                      Herunterladen
                    </a>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {!files.length && (
            <div className="admin-empty">
              <FileText size={32} />
              <h3>Gut aufgehoben. Sobald es losgeht.</h3>
              <p>Noch keine Dokumente vorhanden.</p>
            </div>
          )}
        </div>
      </Card>
    </>
  );
}
function SettingsPanel({
  config: c,
  setConfig: set,
}: {
  config: Any;
  setConfig: (c: Any) => void;
}) {
  const [users, setUsers] = useState<Any[]>([]),
    [audit, setAudit] = useState<Any[]>([]),
    [message, setMessage] = useState(""),
    [error, setError] = useState(false);
  const refresh = () => {
    api("/admin/users").then(setUsers);
    api("/admin/audit").then(setAudit);
  };
  useEffect(refresh, []);
  async function add(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const form = e.currentTarget;
    try {
      await api("/admin/users", {
        method: "POST",
        body: JSON.stringify(Object.fromEntries(new FormData(form))),
      });
      setMessage("Benutzer angelegt.");
      setError(false);
      form.reset();
      refresh();
    } catch (e: Any) {
      setMessage(e.message);
      setError(true);
    }
  }
  return (
    <>
      <Card
        title="Datenschutz & Aufbewahrung"
        description="Texte müssen vor einem öffentlichen Betrieb fachlich und rechtlich geprüft werden."
      >
        <Field
          type="number"
          label="Aufbewahrung gespeicherter Anfragen / Ereignisse (Tage)"
          value={c.retention_days}
          min={1}
          max={730}
          onChange={(v: number) => set({ ...c, retention_days: v })}
        />
        <label>
          Datenschutzhinweis
          <textarea
            rows={7}
            value={c.privacy_text}
            onChange={(e) => set({ ...c, privacy_text: e.target.value })}
          />
        </label>
        <label>
          Impressum
          <textarea
            rows={5}
            value={c.legal_text}
            onChange={(e) => set({ ...c, legal_text: e.target.value })}
          />
        </label>
        <SaveBar config={c} setConfig={set} />
      </Card>
      <Card
        title="Team & Berechtigungen"
        description="Mitarbeiter verwalten Immobilien, Anfragen und private Unterlagen. Zugangsdaten und sicherheitsrelevante Einstellungen sind Administratoren vorbehalten."
      >
        {users.map((u) => (
          <div className="team-row" key={u.id}>
            <div className="avatar">{u.email[0].toUpperCase()}</div>
            <strong>{u.email}</strong>
            <span className="badge">
              {u.role === "admin" ? "Administrator" : "Mitarbeiter"}
            </span>
          </div>
        ))}
        <TeamControls users={users} refresh={refresh} />
        <form onSubmit={add}>
          <div className="field-grid">
            <label>
              E-Mail
              <input type="email" required name="email" />
            </label>
            <label>
              Startpasswort (mindestens 12 Zeichen)
              <input
                type="password"
                required
                minLength={12}
                name="password"
                autoComplete="new-password"
              />
            </label>
            <label>
              Rolle
              <select name="role">
                <option value="staff">Mitarbeiter</option>
                <option value="admin">Administrator</option>
              </select>
            </label>
          </div>
          <button className="small-button">
            <Plus size={15} />
            Teammitglied anlegen
          </button>
        </form>
        {message && <Notice text={message} error={error} />}
      </Card>
      <Card
        title="Änderungsprotokoll"
        description="Wichtige Verwaltungsaktionen, ohne Zugangsdaten oder Anfrageinhalte."
      >
        <div className="audit-list">
          {audit.map((a, i) => (
            <div key={i}>
              <span>{new Date(a.created).toLocaleString("de-DE")}</span>
              <strong>{a.action}</strong>
              <small>{a.actor}</small>
            </div>
          ))}
        </div>
      </Card>
    </>
  );
}
const newProperty = () => ({
  title: "",
  slug: "",
  number: "",
  status: "draft",
  offer: "sale",
  type: "house",
  street: "",
  house_number: "",
  postcode: "",
  city: "",
  district: "",
  show_address: false,
  available: "",
  contact: "",
  area: 0,
  land_area: 0,
  rooms: 0,
  bedrooms: 0,
  bathrooms: 0,
  floor: null,
  floors: null,
  year: null,
  modernized: null,
  condition: "",
  furnished: "",
  accessibility: "",
  pets: "",
  features: [],
  price: 0,
  service_charge: 0,
  heating_cost: 0,
  heating_included: true,
  deposit: 0,
  parking_cost: 0,
  furniture_cost: 0,
  maintenance: 0,
  commission: "",
  heating: "",
  energy_source: "",
  certificate: "unknown",
  energy_value: null,
  energy_class: "",
  energy_until: "",
  energy_year: null,
  exemption_reason: "",
  description: "",
  equipment: "",
  location: "",
  notes: "",
  images: [],
  documents: [],
});
function PropertyManager() {
  const [items, setItems] = useState<Any[]>([]),
    [edit, setEdit] = useState<Any>(null),
    [q, setQ] = useState(""),
    [status, setStatus] = useState(""),
    [error, setError] = useState(""),
    [page, setPage] = useState(1);
  const load = () =>
    api("/admin/properties")
      .then(setItems)
      .catch((e) => setError(e.message));
  useEffect(() => {
    load();
  }, []);
  if (edit)
    return (
      <PropertyEditor
        initial={edit}
        onClose={() => {
          setEdit(null);
          load();
        }}
      />
    );
  const filtered = items.filter(
    (p) =>
      (!q ||
        `${p.title} ${p.city} ${p.number}`
          .toLowerCase()
          .includes(q.toLowerCase())) &&
      (!status || p.status === status),
  );
  return (
    <>
      {error && <Notice error text={error} />}
      <div className="filter-toolbar">
        <label className="search-input">
          <Search size={16} />
          <input
            placeholder="Titel, Ort oder Objektnummer suchen"
            aria-label="Immobilien durchsuchen"
            value={q}
            onChange={(e) => {
              setQ(e.target.value);
              setPage(1);
            }}
          />
        </label>
        <select
          aria-label="Veröffentlichungsstatus"
          value={status}
          onChange={(e) => {
            setStatus(e.target.value);
            setPage(1);
          }}
        >
          <option value="">Alle Status</option>
          {["draft", "published", "reserved", "sold", "archived"].map((v) => (
            <option value={v} key={v}>
              {labels[v]}
            </option>
          ))}
        </select>
        <button className="button" onClick={() => setEdit(newProperty())}>
          <Plus size={17} />
          Immobilie anlegen
        </button>
      </div>
      <div className="admin-card table-wrap">
        <table>
          <thead>
            <tr>
              <th>Immobilie</th>
              <th>Standort</th>
              <th>Fläche / Zimmer</th>
              <th>Preis</th>
              <th>Status</th>
              <th />
            </tr>
          </thead>
          <tbody>
            {filtered.slice((page - 1) * 10, page * 10).map((p) => (
              <tr key={p.id}>
                <td>
                  <button
                    className="property-table-title"
                    onClick={() => setEdit(p)}
                  >
                    {p.images[0] ? (
                      <img src={"/api/admin/files/" + p.images[0].id} alt="" />
                    ) : (
                      <span>
                        <Building2 size={22} />
                      </span>
                    )}
                    <div>
                      <strong>{p.title}</strong>
                      <small>
                        {p.number || "#" + p.id} ·{" "}
                        {p.offer === "sale" ? "Verkauf" : "Vermietung"}
                      </small>
                    </div>
                  </button>
                </td>
                <td>{p.city || "Noch offen"}</td>
                <td>
                  {p.area} m² · {p.rooms} Zi.
                </td>
                <td>{money(p.price)}</td>
                <td>
                  <span className={"badge " + p.status}>
                    {labels[p.status]}
                  </span>
                </td>
                <td>
                  <div className="button-row">
                    <button
                      className="icon-button"
                      title="Bearbeiten"
                      onClick={() => setEdit(p)}
                    >
                      <ArrowUpRight size={16} />
                    </button>
                    <button
                      className="icon-button"
                      title="Duplizieren"
                      onClick={async () => {
                        try {
                          await api(
                            "/admin/properties/" + p.id + "/duplicate",
                            { method: "POST" },
                          );
                          load();
                        } catch (e: Any) {
                          setError(e.message);
                        }
                      }}
                    >
                      <Copy size={15} />
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {!filtered.length && (
          <div className="admin-empty">
            <Building2 size={42} strokeWidth={1} />
            <h3>Jede Immobilie beginnt mit einem Entwurf.</h3>
            <p>
              Legen Sie Ihr erstes Objekt an. Nichts wird automatisch
              veröffentlicht.
            </p>
            <button
              className="small-button"
              onClick={() => setEdit(newProperty())}
            >
              <Plus size={15} />
              Ersten Entwurf anlegen
            </button>
          </div>
        )}
      </div>
      {filtered.length > 10 && (
        <div className="pagination">
          <button disabled={page === 1} onClick={() => setPage(page - 1)}>
            <ChevronLeft />
          </button>
          {page} / {Math.ceil(filtered.length / 10)}
          <button
            disabled={page >= Math.ceil(filtered.length / 10)}
            onClick={() => setPage(page + 1)}
          >
            <ChevronRight />
          </button>
        </div>
      )}
    </>
  );
}
function PropertyEditor({
  initial,
  onClose,
}: {
  initial: Any;
  onClose: () => void;
}) {
  const [p, setP] = useState<Any>(initial),
    [step, setStep] = useState(0),
    [message, setMessage] = useState(""),
    [error, setError] = useState(false),
    [busy, setBusy] = useState(false);
  const edit = (k: string, v: Any) => setP({ ...p, [k]: v });
  const field = (k: string, label: string, type = "text", extra: Any = {}) => (
    <Field
      key={k}
      label={label}
      value={p[k]}
      type={type}
      onChange={(v: Any) => edit(k, v)}
      {...extra}
    />
  );
  async function save(status = p.status) {
    setBusy(true);
    setMessage("");
    try {
      const row = await api("/admin/properties" + (p.id ? "/" + p.id : ""), {
        method: p.id ? "PUT" : "POST",
        body: JSON.stringify({ ...p, status }),
      });
      setP(row);
      setError(false);
      setMessage(
        status === "draft"
          ? "Entwurf gespeichert. Nur im Adminbereich sichtbar."
          : `Immobilie gespeichert: ${labels[status]}.`,
      );
    } catch (e: Any) {
      setError(true);
      setMessage(e.message);
    } finally {
      setBusy(false);
    }
  }
  const steps = [
    "Stammdaten",
    "Flächen & Ausstattung",
    "Preise",
    "Energie",
    "Texte & Medien",
    "Prüfen & veröffentlichen",
  ];
  return (
    <>
      <button className="back-link" onClick={onClose}>
        <ChevronLeft size={15} />
        Zur Immobilienverwaltung
      </button>
      <div className="wizard-heading">
        <div>
          <h2>{p.title || "Ihre neue Immobilie"}</h2>
          <span className={"badge " + p.status}>{labels[p.status]}</span>
        </div>
        <button
          className="small-button"
          disabled={busy}
          onClick={() => save("draft")}
        >
          <Save size={15} />
          Als Entwurf speichern
        </button>
      </div>
      <div className="wizard-steps">
        {steps.map((s, i) => (
          <button
            key={s}
            className={step === i ? "active" : i < step ? "complete" : ""}
            onClick={() => setStep(i)}
          >
            <span>{i < step ? <Check size={13} /> : i + 1}</span>
            {s}
          </button>
        ))}
      </div>
      <Card
        title={steps[step]}
        description={
          step === 5
            ? "Prüfen Sie alle Angaben vor der Veröffentlichung. Fehlende Pflichtangaben werden serverseitig geprüft."
            : "Sie können jederzeit als Entwurf zwischenspeichern."
        }
      >
        {step === 0 && (
          <>
            <div className="field-grid">
              {field("title", "Titel")}
              {field("slug", "URL-Slug (z. B. haus-am-park)")}
              {field("number", "Interne Objektnummer")}
              <Select
                label="Angebotsart"
                value={p.offer}
                onChange={(v: string) => edit("offer", v)}
                options={[
                  ["sale", "Verkauf"],
                  ["rent", "Vermietung"],
                ]}
              />
              <Select
                label="Objektart"
                value={p.type}
                onChange={(v: string) => edit("type", v)}
                options={[
                  ["house", "Haus"],
                  ["apartment", "Wohnung"],
                ]}
              />
              {field("contact", "Ansprechpartner")}
              {field("street", "Straße")}
              {field("house_number", "Hausnummer")}
              {field("postcode", "Postleitzahl")}
              {field("city", "Ort")}
              {field("district", "Stadtteil")}
              {field("available", "Verfügbar ab")}
            </div>
            <Toggle
              label="Vollständige Adresse öffentlich anzeigen"
              description="Bei Deaktivierung werden Straße und Hausnummer auch in der öffentlichen API verborgen."
              checked={p.show_address}
              onChange={(v) => edit("show_address", v)}
            />
          </>
        )}
        {step === 1 && (
          <>
            <div className="field-grid">
              {[
                ["area", "Wohnfläche (m²)"],
                ["land_area", "Grundstück (m²)"],
                ["rooms", "Zimmer"],
                ["bedrooms", "Schlafzimmer"],
                ["bathrooms", "Badezimmer"],
                ["floor", "Etage"],
                ["floors", "Etagen insgesamt"],
                ["year", "Baujahr"],
                ["modernized", "Modernisierungsjahr"],
              ].map(([k, l]) =>
                field(k, l, "number", {
                  min: k === "floor" ? -10 : 0,
                  step:
                    k === "rooms" || k === "area" || k === "land_area"
                      ? "0.5"
                      : "1",
                }),
              )}
              {field("condition", "Zustand")}
              {field("furnished", "Möblierung")}
              {field("accessibility", "Barrierefreiheit")}
              {field("pets", "Haustierregelung")}
            </div>
            <h3>Ausstattung</h3>
            <div className="feature-checkboxes">
              {[
                "Balkon",
                "Terrasse",
                "Garten",
                "Aufzug",
                "Keller",
                "Einbauküche",
                "Stellplatz",
                "Garage",
              ].map((f) => (
                <label className="checkbox-label" key={f}>
                  <input
                    type="checkbox"
                    checked={p.features.includes(f)}
                    onChange={(e) =>
                      edit(
                        "features",
                        e.target.checked
                          ? [...p.features, f]
                          : p.features.filter((x: string) => x !== f),
                      )
                    }
                  />
                  {f}
                </label>
              ))}
            </div>
          </>
        )}
        {step === 2 && (
          <>
            <div className="field-grid">
              {field(
                "price",
                p.offer === "rent" ? "Kaltmiete (€)" : "Kaufpreis (€)",
                "number",
                { min: 0, step: ".01" },
              )}
              {(p.offer === "rent"
                ? [
                    ["service_charge", "Nebenkosten (€)"],
                    ["heating_cost", "Heizkosten (€)"],
                    ["deposit", "Kaution (€)"],
                    ["parking_cost", "Stellplatz zusätzlich (€)"],
                    ["furniture_cost", "Möblierung zusätzlich (€)"],
                  ]
                : [["maintenance", "Hausgeld (€)"]]
              ).map(([k, l]) => field(k, l, "number", { min: 0, step: ".01" }))}
              {p.offer === "sale" &&
                field("commission", "Provision mit Erläuterung")}
            </div>
            {p.offer === "rent" && (
              <>
                <Toggle
                  label="Heizkosten in Nebenkosten enthalten"
                  checked={p.heating_included}
                  onChange={(v) => edit("heating_included", v)}
                />
                <div className="rent-calculation">
                  <strong>
                    Warmmiete:{" "}
                    {money(
                      p.price +
                        p.service_charge +
                        (p.heating_included ? 0 : p.heating_cost),
                    )}
                  </strong>
                  <p>
                    Kaltmiete + Nebenkosten
                    {p.heating_included
                      ? " (einschließlich Heizkosten)"
                      : " + Heizkosten"}
                    . Stellplatz und Möblierung werden separat ausgewiesen.
                  </p>
                </div>
              </>
            )}
          </>
        )}
        {step === 3 && (
          <>
            <div className="field-grid">
              {field("heating", "Heizungsart")}
              {field("energy_source", "Energieträger")}
              <Select
                label="Energieausweis"
                value={p.certificate}
                onChange={(v: string) => edit("certificate", v)}
                options={[
                  ["unknown", "Nicht bekannt / noch nicht angegeben"],
                  ["demand", "Bedarfsausweis"],
                  ["consumption", "Verbrauchsausweis"],
                  ["exempt", "Begründete Ausnahme"],
                ]}
              />
              {p.certificate === "exempt"
                ? field("exemption_reason", "Grund für die Ausnahme")
                : p.certificate !== "unknown" && (
                    <>
                      {field(
                        "energy_value",
                        p.certificate === "demand"
                          ? "Energiebedarf kWh/(m²·a)"
                          : "Energieverbrauch kWh/(m²·a)",
                        "number",
                        { min: 0, step: ".1" },
                      )}
                      {field("energy_class", "Energieeffizienzklasse")}
                      {field("energy_until", "Gültig bis", "date")}
                      {field("energy_year", "Baujahr laut Ausweis", "number")}
                    </>
                  )}
            </div>
            <p className="card-hint">
              Keine Werte erfinden. Unbekannte Energieangaben sind als Entwurf
              zulässig. Für die Veröffentlichung sind ein vollständiger Ausweis
              oder eine begründete Ausnahme erforderlich. Fachliche Prüfung
              bleibt notwendig.
            </p>
          </>
        )}
        {step === 4 && (
          <>
            <div className="field-grid">
              {[
                ["description", "Objektbeschreibung"],
                ["equipment", "Ausstattung im Detail"],
                ["location", "Lagebeschreibung"],
                ["notes", "Sonstige Hinweise"],
              ].map(([k, l]) => (
                <label key={k}>
                  {l}
                  <textarea
                    rows={5}
                    value={p[k]}
                    onChange={(e) => edit(k, e.target.value)}
                  />
                </label>
              ))}
            </div>
            <h3>Bilder & Titelbild</h3>
            <MediaUpload
              purpose="image"
              label="Immobilienbild hochladen (max. 10 MB)"
              onUpload={(f) =>
                edit("images", [...p.images, { id: f.id, alt: "", title: "" }])
              }
            />
            <div className="image-editor">
              {p.images.map((img: Any, i: number) => (
                <div key={img.id}>
                  <img
                    src={"/api/admin/files/" + img.id}
                    alt={img.alt || "Bildvorschau"}
                  />
                  <span>{i === 0 ? "Titelbild" : "Bild " + (i + 1)}</span>
                  <Field
                    label="Bildtitel"
                    value={img.title}
                    onChange={(v: string) =>
                      edit(
                        "images",
                        p.images.map((x: Any, j: number) =>
                          j === i ? { ...x, title: v } : x,
                        ),
                      )
                    }
                  />
                  <Field
                    label="Bildbeschreibung / Alt-Text"
                    value={img.alt}
                    onChange={(v: string) =>
                      edit(
                        "images",
                        p.images.map((x: Any, j: number) =>
                          j === i ? { ...x, alt: v } : x,
                        ),
                      )
                    }
                  />
                  <div className="button-row">
                    <button
                      className="small-button"
                      disabled={i === 0}
                      onClick={() => {
                        const images = [...p.images];
                        [images[i - 1], images[i]] = [images[i], images[i - 1]];
                        edit("images", images);
                      }}
                    >
                      <MoveUp size={13} />
                      Nach vorne
                    </button>
                    <button
                      className="small-button"
                      onClick={() =>
                        edit(
                          "images",
                          p.images.filter((_: Any, j: number) => j !== i),
                        )
                      }
                    >
                      Entfernen
                    </button>
                  </div>
                </div>
              ))}
            </div>
            <h3>Grundrisse & Dokumente (privat)</h3>
            <MediaUpload
              purpose="document"
              label="PDF-Dokument hochladen"
              onUpload={(f) => edit("documents", [...p.documents, f.id])}
            />
            {p.documents.map((id: string) => (
              <div key={id} className="document-link">
                <a href={"/api/admin/files/" + id}>
                  Dokument {id.slice(0, 8)} <Download size={13} />
                </a>
                <button
                  className="icon-button"
                  aria-label="Dokumentzuordnung entfernen"
                  onClick={() =>
                    edit(
                      "documents",
                      p.documents.filter((x: string) => x !== id),
                    )
                  }
                >
                  <X size={14} />
                </button>
              </div>
            ))}
          </>
        )}
        {step === 5 && (
          <>
            <div className="publication-summary">
              <Building2 size={40} strokeWidth={1} />
              <div>
                <h2>{p.title || "Noch kein Titel"}</h2>
                <p>
                  {p.postcode} {p.city} · {p.area} m² · {p.rooms} Zimmer
                </p>
                <strong>
                  {money(p.price)}
                  {p.offer === "rent" ? " Kaltmiete" : ""}
                </strong>
              </div>
            </div>
            <div className="checklist publication-checks">
              {[
                ["Titel und URL", p.title.length >= 3 && !!p.slug],
                ["Standort mit PLZ", !!p.city && !!p.postcode],
                [
                  "Preis, Fläche und Zimmer",
                  p.price > 0 && p.area > 0 && p.rooms > 0,
                ],
                [
                  "Beschreibung und mindestens ein Bild",
                  !!p.description && p.images.length > 0,
                ],
                [
                  "Energieangaben",
                  p.certificate === "exempt"
                    ? !!p.exemption_reason
                    : p.certificate !== "unknown" &&
                      p.energy_value != null &&
                      !!p.energy_until &&
                      !!p.energy_class &&
                      !!p.energy_source,
                ],
              ].map(([l, done]) => (
                <div key={String(l)}>
                  <span className={done ? "done" : ""}>
                    {done ? <Check size={13} /> : <X size={13} />}
                  </span>
                  <strong>{String(l)}</strong>
                  <small>{done ? "Vorhanden" : "Noch ergänzen"}</small>
                </div>
              ))}
            </div>
            <Select
              label="Veröffentlichungsstatus"
              value={p.status}
              onChange={(v: string) => edit("status", v)}
              options={[
                "draft",
                "published",
                "reserved",
                "sold",
                "archived",
              ].map((x) => [x, labels[x]])}
            />
            <p className="card-hint">
              Reservierte Objekte bleiben sichtbar. Verkaufte, vermietete und
              archivierte Objekte sowie zurückgezogene Entwürfe sind öffentlich
              nicht abrufbar; bekannte Links liefern 404.
            </p>
            {p.id && (
              <Link
                className="small-button"
                target="_blank"
                href={`/immobilien/${p.slug}?preview=1&id=${p.id}`}
              >
                <Eye size={15} />
                Gespeichertes Exposé prüfen <ArrowUpRight size={15} />
              </Link>
            )}
          </>
        )}
      </Card>
      {message && <Notice text={message} error={error} />}
      <div className="wizard-footer">
        <button
          className="small-button"
          disabled={step === 0}
          onClick={() => setStep(step - 1)}
        >
          <ChevronLeft size={15} />
          Zurück
        </button>
        <span>
          Schritt {step + 1} von {steps.length}
        </span>
        {step < 5 ? (
          <button className="button" onClick={() => setStep(step + 1)}>
            Weiter
            <ChevronRight size={16} />
          </button>
        ) : (
          <button className="button" disabled={busy} onClick={() => save()}>
            {busy
              ? "Wird gespeichert …"
              : p.status === "published"
                ? "Immobilie veröffentlichen"
                : "Status speichern"}
            <Check size={16} />
          </button>
        )}
      </div>
    </>
  );
}
