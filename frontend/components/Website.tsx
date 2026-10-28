"use client";
import {
  useEffect,
  useState,
  useRef,
  createContext,
  useContext,
  FormEvent,
  CSSProperties,
} from "react";
import NextLink from "next/link";
import {
  ArrowUpRight,
  ArrowRight,
  ArrowDown,
  Mail,
  Phone,
  MapPin,
  Menu,
  X,
  House,
  KeyRound,
  ChartNoAxesCombined,
  Check,
  Download,
  FileText,
  SlidersHorizontal,
  ChevronLeft,
  ChevronRight,
  MoveUpRight,
} from "lucide-react";
import { api, money } from "./api";
import CustomFrontend from "./CustomFrontend";
type Any = any;
const PreviewContext = createContext(false);
function SiteLink(props: React.ComponentProps<typeof NextLink>) {
  const preview = useContext(PreviewContext);
  let href = props.href;
  if (
    preview &&
    typeof href === "string" &&
    href.startsWith("/") &&
    !href.startsWith("/admin") &&
    !href.startsWith("/api")
  )
    href += href.includes("?") ? "&preview=1" : "?preview=1";
  return <NextLink {...props} href={href} />;
}
async function previewProperties(query = "", page = 1) {
  const params = new URLSearchParams(query);
  let rows = await api("/admin/preview/properties");
  rows = rows.filter(
    (p: Any) =>
      (!params.get("q") ||
        `${p.city} ${p.postcode} ${p.title}`
          .toLowerCase()
          .includes(params.get("q")!.toLowerCase())) &&
      (!params.get("offer") || p.offer === params.get("offer")) &&
      (!params.get("type") || p.type === params.get("type")) &&
      p.price >= Number(params.get("min_price") || 0) &&
      p.price <= Number(params.get("max_price") || 1e12) &&
      p.area >= Number(params.get("min_area") || 0) &&
      p.rooms >= Number(params.get("rooms") || 0),
  );
  if (params.get("sort") === "price_asc")
    rows.sort((a: Any, b: Any) => a.price - b.price);
  if (params.get("sort") === "price_desc")
    rows.sort((a: Any, b: Any) => b.price - a.price);
  return {
    items: rows.slice((page - 1) * 9, page * 9),
    total: rows.length,
    page,
    pages: Math.ceil(rows.length / 9),
  };
}
function track(c: Any, kind: string, path: string) {
  if (c?.modules.analytics)
    api("/public/events", {
      method: "POST",
      body: JSON.stringify({ kind, path }),
    }).catch(() => {});
}
export default function Website({
  path,
  initialConfig,
  embedded = false,
}: {
  path: string[];
  initialConfig?: Any;
  embedded?: boolean;
}) {
  const [c, setC] = useState<Any>(initialConfig || null),
    [error, setError] = useState(""),
    [menu, setMenu] = useState(false),
    [preview, setPreview] = useState(false);
  const route = path.join("/");
  const trackedRoute = useRef<string | null>(null);
  useEffect(() => {
    const draft = new URLSearchParams(location.search).get("preview") === "1";
    setPreview(draft);
    (draft ? api("/admin/config").then((v) => v.draft) : api("/public/config"))
      .then(setC)
      .catch((e) => setError(e.message));
  }, []);
  useEffect(() => {
    if (c && !preview && (embedded || !c.frontend_package) && trackedRoute.current !== route) {
      trackedRoute.current = route;
      track(c, "pageview", "/" + route);
    }
  }, [c, route, preview]);
  if (error)
    return (
      <div className="system-message">
        <House />
        <h1>Ein kurzer Moment.</h1>
        <p>{error}</p>
        <button onClick={() => location.reload()}>Erneut versuchen</button>
      </div>
    );
  if (!c)
    return (
      <div className="loading-screen">
        <span className="loading-mark">R</span>
        <p>Räume für neue Perspektiven.</p>
      </div>
    );
  if (!embedded && c.frontend_package)
    return <CustomFrontend config={c} path={path} preview={preview} />;
  const active = (slug: string) =>
    c.pages.find((p: Any) => p.slug === slug && p.enabled);
  const nav = [
    ...(c.modules.properties
      ? [{ slug: "immobilien", title: "Immobilien" }]
      : []),
    ...c.pages.filter((p: Any) => p.enabled),
    ...(c.modules.disclosure
      ? [{ slug: "selbstauskunft", title: "Selbstauskunft" }]
      : []),
  ];
  let page;
  if (!route)
    page = (
      <Home
        c={
          preview
            ? {
                ...c,
                hero_image: c.hero_image.replace("/public/", "/admin/"),
                approach_image: c.approach_image.replace("/public/", "/admin/"),
              }
            : c
        }
      />
    );
  else if (path[0] === "immobilien" && c.modules.properties)
    page = path[1] ? (
      <PropertyPage c={c} slug={path[1]} preview={preview} />
    ) : (
      <Properties c={c} />
    );
  else if (path[0] === "kontakt" && c.modules.contact) page = <Contact c={c} />;
  else if (path[0] === "selbstauskunft" && c.modules.disclosure)
    page = <Disclosure c={c} />;
  else if (path[0] === "datenschutz" || path[0] === "impressum")
    page = (
      <section className="content-page narrow">
        <Eyebrow>Informationen</Eyebrow>
        <h1>{path[0] === "datenschutz" ? "Datenschutz" : "Impressum"}</h1>
        <p className="preserve">
          {path[0] === "datenschutz" ? c.privacy_text : c.legal_text}
        </p>
        {path[0] === "datenschutz" && (
          <p>
            Aktivierte Formularziele:{" "}
            {[
              ...new Set(
                Object.values(c.forms)
                  .flatMap((v: Any) => [
                    v.store ? "Speicherung im Adminbereich" : "",
                    v.email ? "SMTP-E-Mail" : "",
                    v.telegram ? "Telegram" : "",
                  ])
                  .filter(Boolean),
              ),
            ].join(", ")}
            . Technische Zustelldaten ohne dauerhafte Speicherung: maximal 24
            Stunden. Aufbewahrung gespeicherter Anfragen: {c.retention_days}{" "}
            Tage.
          </p>
        )}
      </section>
    );
  else if (active(path[0])) {
    const p = active(path[0]);
    page = (
      <section className="content-page narrow">
        <Eyebrow>Persönlich an Ihrer Seite</Eyebrow>
        <h1>
          {p.title}.<br />
          <em>Mit Perspektive.</em>
        </h1>
        <p className="lead preserve">{p.text}</p>
        {p.form && c.modules.contact && (
          <ContactForm c={c} page={p.slug} subject={p.title} />
        )}
      </section>
    );
  } else
    page = (
      <section className="content-page narrow">
        <Eyebrow>Neue Perspektiven</Eyebrow>
        <h1>
          Hier geht es
          <br />
          gerade nicht weiter.
        </h1>
        <p>Diese Seite oder Immobilie ist nicht verfügbar.</p>
        <SiteLink className="button" href="/">
          Zur Startseite <ArrowUpRight size={16} />
        </SiteLink>
      </section>
    );
  return (
    <PreviewContext.Provider value={preview}>
      <div
        className={`website ${c.template_adapter || c.template} ${c.font} hero-${c.frontend_theme?.hero_layout || "cover"} cards-${c.frontend_theme?.card_layout || "grid"} spacing-${c.frontend_theme?.spacing || "normal"}`}
        style={
          {
            "--primary": c.primary,
            "--accent": c.accent,
            "--site-background": c.frontend_theme?.background || "#f7f9fa",
            "--site-foreground": c.frontend_theme?.foreground || "#142736",
            "--site-radius": `${c.frontend_theme?.radius || 0}px`,
            "--site-width": `${c.frontend_theme?.content_width || 1280}px`,
            "--site-heading-scale": c.frontend_theme?.heading_scale || 1,
          } as CSSProperties
        }
      >
        {preview && (
          <div className="preview-banner">
            Unveröffentlichte Vorschau{" "}
            <SiteLink href="/admin/design">
              Zurück zum Baukasten <ArrowUpRight size={14} />
            </SiteLink>
          </div>
        )}
        <header className="site-header">
          <SiteLink
            href="/"
            className="brand"
            aria-label={c.company + " Startseite"}
          >
            {c.logo ? (
              <img
                src={preview ? c.logo.replace("/public/", "/admin/") : c.logo}
                alt={c.company}
              />
            ) : (
              <>
                <span>{c.company}</span>
                <small>{c.tagline}</small>
              </>
            )}
          </SiteLink>
          <nav className={menu ? "open" : ""} aria-label="Hauptnavigation">
            {nav.map((n: Any) => (
              <SiteLink
                className={path[0] === n.slug ? "active" : ""}
                key={n.slug}
                href={"/" + n.slug}
                onClick={() => setMenu(false)}
              >
                {n.title}
              </SiteLink>
            ))}
            <SiteLink className="account-link" href="/admin">
              Mein Bereich <ArrowUpRight size={15} />
            </SiteLink>
          </nav>
          <button
            className="mobile-menu icon-button"
            aria-label="Menü öffnen"
            onClick={() => setMenu(!menu)}
          >
            {menu ? <X /> : <Menu />}
          </button>
        </header>
        <main>{page}</main>
        <footer className="site-footer">
          <div>
            <SiteLink href="/" className="brand">
              <span>{c.company}</span>
              <small>{c.tagline}</small>
            </SiteLink>
            <p>{c.footer_text}</p>
          </div>
          <div className="footer-links">
            {c.modules.contact && (
              <SiteLink href="/kontakt">
                Kontakt <ArrowUpRight size={14} />
              </SiteLink>
            )}
            <SiteLink href="/impressum">Impressum</SiteLink>
            <SiteLink href="/datenschutz">Datenschutz</SiteLink>
            {c.social_links.map((url: string) => (
              <a href={url} key={url} target="_blank" rel="noopener noreferrer">
                Social Media <ArrowUpRight size={13} />
              </a>
            ))}
          </div>
          <div className="footer-bottom">
            <span>
              © {new Date().getFullYear()} {c.company}
            </span>
            <span>Neue Räume. Bleibende Werte.</span>
            <SiteLink href="/admin">
              Website verwalten <ArrowUpRight size={12} />
            </SiteLink>
          </div>
        </footer>
      </div>
    </PreviewContext.Provider>
  );
}
export function Eyebrow({ children }: { children: React.ReactNode }) {
  return (
    <div className="eyebrow">
      <span />
      {children}
    </div>
  );
}
function Home({ c }: { c: Any }) {
  const visible = c.sections.filter((s: Any) => s.visible);
  return (
    <>
      {visible.map((s: Any) => {
        if (s.id === "hero")
          return (
            <section className="hero" key={s.id}>
              <img className="hero-image" src={c.hero_image} alt={c.hero_alt} />
              <div className="hero-shade" />
              <div className="hero-inner">
                <Eyebrow>{c.city} · Immobilien mit Perspektive</Eyebrow>
                <h1>
                  {c.headline.split("\n").map((line: string, i: number) => (
                    <span key={i}>{line}</span>
                  ))}
                </h1>
                <p className="preserve">{c.introduction}</p>
                <div className="hero-actions">
                  {(c.cta_target === "immobilien"
                    ? c.modules.properties
                    : c.modules.contact) && (
                    <SiteLink
                      className="button light"
                      href={"/" + c.cta_target}
                    >
                      {c.cta_label}
                      <ArrowUpRight size={18} />
                    </SiteLink>
                  )}
                  {c.modules.contact &&
                    c.pages.some(
                      (p: Any) => p.slug === "bewertung" && p.enabled,
                    ) && (
                      <SiteLink
                        className="text-link light-text"
                        href="/bewertung"
                      >
                        Immobilie bewerten <ArrowUpRight size={17} />
                      </SiteLink>
                    )}
                </div>
                <div className="hero-contact">
                  {c.email && (
                    <a href={"mailto:" + c.email}>
                      <Mail size={14} />
                      {c.email}
                    </a>
                  )}
                  {c.phone && (
                    <a href={"tel:" + c.phone}>
                      <Phone size={14} />
                      {c.phone}
                    </a>
                  )}
                </div>
              </div>
              <div className="hero-bottom">
                <a href="#perspektiven">
                  <ArrowDown size={15} />
                  Ihre nächste Perspektive
                </a>
                <span>
                  <MapPin size={14} />
                  Architekturillustration · kein Immobilienangebot
                </span>
              </div>
            </section>
          );
        if (s.id === "services")
          return (
            <section className="section services" id="perspektiven" key={s.id}>
              <div className="section-title">
                <div>
                  <Eyebrow>Was uns bewegt</Eyebrow>
                  <h2 className="preserve">{c.services_heading}</h2>
                </div>
                <p>{c.services_intro}</p>
              </div>
              <div className="service-grid">
                {c.services
                  .map((x: Any, i: number) => ({
                    ...x,
                    icon: [House, KeyRound, ChartNoAxesCombined][i % 3],
                  }))
                  .filter((x: Any) =>
                    c.pages.some((p: Any) => p.slug === x.slug && p.enabled),
                  )
                  .map((x: Any, i: number) => (
                    <SiteLink
                      href={"/" + x.slug}
                      className="service-card"
                      key={x.slug}
                    >
                      <div className="service-top">
                        <x.icon size={26} strokeWidth={1} />
                        <small>0{i + 1}</small>
                      </div>
                      <h3>{x.title}</h3>
                      <p>{x.text}</p>
                      <span>
                        {x.label}
                        <ArrowUpRight size={16} />
                      </span>
                    </SiteLink>
                  ))}
              </div>
            </section>
          );
        if (s.id === "properties" && c.modules.properties)
          return (
            <section className="section offers-section" key={s.id}>
              <div className="section-title">
                <div>
                  <Eyebrow>Ausgewählte Immobilien</Eyebrow>
                  <h2>
                    Ein Ort, der <span>zu Ihnen passt.</span>
                  </h2>
                </div>
                <SiteLink className="text-link" href="/immobilien">
                  Alle Immobilien <ArrowUpRight size={17} />
                </SiteLink>
              </div>
              <PropertyTeaser c={c} />
            </section>
          );
        if (s.id === "approach")
          return (
            <section className="approach section" key={s.id}>
              <div className="approach-image">
                <img src={c.approach_image} alt={c.approach_alt} />
                <span>Raum für neue Möglichkeiten.</span>
              </div>
              <div>
                <Eyebrow>Mehr als Immobilien</Eyebrow>
                <h2 className="preserve">{c.approach_heading}</h2>
                <p>{c.approach_text}</p>
                {c.pages.some(
                  (p: Any) => p.slug === "ueber-uns" && p.enabled,
                ) && (
                  <SiteLink className="text-link" href="/ueber-uns">
                    Lernen Sie uns kennen <ArrowUpRight size={17} />
                  </SiteLink>
                )}
              </div>
            </section>
          );
        if (s.id === "contact" && c.modules.contact)
          return (
            <section className="contact-band" key={s.id}>
              <div>
                <Eyebrow>Der erste Schritt ist ein Gespräch</Eyebrow>
                <h2>
                  Was haben <span>Sie vor?</span>
                </h2>
              </div>
              <SiteLink className="button light" href="/kontakt">
                Lassen Sie uns sprechen <ArrowUpRight size={18} />
              </SiteLink>
            </section>
          );
        return null;
      })}
    </>
  );
}
function PropertyTeaser({ c }: { c: Any }) {
  const preview = useContext(PreviewContext);
  const [items, setItems] = useState<Any[] | null>(null);
  const [error, setError] = useState("");
  useEffect(() => {
    (preview ? previewProperties() : api("/public/properties"))
      .then((v) => setItems(v.items.slice(0, 3)))
      .catch((e) => setError(e.message));
  }, []);
  if (error) return <p role="alert">{error}</p>;
  if (!items) return <p>Immobilien werden geladen …</p>;
  return items.length ? (
    <div className="property-grid">
      {items.map((p) => (
        <PropertyCard key={p.id} p={p} />
      ))}
    </div>
  ) : (
    <Empty c={c} />
  );
}
function Empty({ c }: { c: Any }) {
  return (
    <div className="empty-properties">
      <House size={32} strokeWidth={1} />
      <Eyebrow>Neue Möglichkeiten entstehen</Eyebrow>
      <h3>Ihr nächstes Zuhause kommt.</h3>
      <p>
        Aktuell sind keine passenden Immobilien veröffentlicht.
        <br />
        Verraten Sie uns, wonach Sie suchen. Wir halten die Augen offen.
      </p>
      {c.modules.contact && (
        <SiteLink href="/kontakt" className="text-link">
          Suchwunsch mitteilen <ArrowUpRight size={16} />
        </SiteLink>
      )}
    </div>
  );
}
function PropertyCard({ p }: { p: Any }) {
  const preview = useContext(PreviewContext);
  return (
    <SiteLink
      href={"/immobilien/" + p.slug + (preview ? "?id=" + p.id : "")}
      className="property-card"
    >
      <div className="property-photo">
        <img
          src={
            (preview ? "/api/admin/files/" : "/api/public/files/") +
            p.images[0]?.id
          }
          alt={p.images[0]?.alt || p.title}
        />
        <span>
          {p.status === "reserved"
            ? "Reserviert"
            : p.offer === "rent"
              ? "Zur Miete"
              : "Zum Kauf"}
        </span>
        <i>
          <ArrowUpRight size={19} />
        </i>
      </div>
      <small>
        {p.postcode} {p.city}
        {p.district ? " · " + p.district : ""}
      </small>
      <h3>{p.title}</h3>
      <div className="property-spec">
        <span>{p.area} m²</span>
        <span>{p.rooms} Zimmer</span>
        <strong>
          {money(p.price)}
          {p.offer === "rent" ? " / Monat" : ""}
        </strong>
      </div>
    </SiteLink>
  );
}
function Properties({ c }: { c: Any }) {
  const preview = useContext(PreviewContext);
  const [result, setResult] = useState<Any>(null),
    [err, setErr] = useState(""),
    [loading, setLoading] = useState(false),
    [query, setQuery] = useState("");
  async function load(q = "", page = 1) {
    setLoading(true);
    setErr("");
    try {
      setResult(
        await (preview
          ? previewProperties(q, page)
          : api("/public/properties?" + q + "&page=" + page)),
      );
    } catch (e: Any) {
      setErr(e.message);
    } finally {
      setLoading(false);
    }
  }
  useEffect(() => {
    load();
  }, []);
  function search(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const params = new URLSearchParams();
    new FormData(e.currentTarget).forEach((v, k) => {
      if (v) params.set(k, String(v));
    });
    setQuery(params.toString());
    load(params.toString());
  }
  return (
    <section className="content-page property-list-page">
      <Eyebrow>Ausgewählte Immobilien</Eyebrow>
      <div className="listing-title">
        <h1>
          Finden Sie Ihren <span>nächsten Ort.</span>
        </h1>
        <span className="listing-count">{result?.total ?? "—"} Immobilien</span>
      </div>
      <form onSubmit={search} className="search-grid">
        <label>
          Vorhaben
          <select name="offer">
            <option value="">Kaufen & Mieten</option>
            <option value="sale">Kaufen</option>
            <option value="rent">Mieten</option>
          </select>
        </label>
        <label>
          Ort oder PLZ
          <input name="q" placeholder="Hamburg, 22303 …" />
        </label>
        <label>
          Immobilientyp
          <select name="type">
            <option value="">Alle Typen</option>
            <option value="house">Haus</option>
            <option value="apartment">Wohnung</option>
          </select>
        </label>
        <label>
          Preis ab
          <input type="number" min="0" name="min_price" placeholder="€" />
        </label>
        <label>
          Preis bis
          <input type="number" min="0" name="max_price" placeholder="€" />
        </label>
        <label>
          Wohnfläche ab m²
          <input type="number" min="0" name="min_area" />
        </label>
        <label>
          Zimmer ab
          <input type="number" min="0" step="0.5" name="rooms" />
        </label>
        <label>
          Sortierung
          <select name="sort">
            <option value="newest">Neueste zuerst</option>
            <option value="price_asc">Preis aufsteigend</option>
            <option value="price_desc">Preis absteigend</option>
          </select>
        </label>
        <button className="button" disabled={loading}>
          {loading ? "Suche läuft …" : "Immobilien suchen"}
          <ArrowUpRight size={16} />
        </button>
      </form>
      {err && (
        <div className="notice error" role="alert">
          {err}
        </div>
      )}
      {result &&
        (result.items.length ? (
          <>
            <div className="property-grid">
              {result.items.map((p: Any) => (
                <PropertyCard p={p} key={p.id} />
              ))}
            </div>
            <div className="pagination">
              <button
                disabled={result.page <= 1}
                onClick={() => load(query, result.page - 1)}
                aria-label="Vorherige Seite"
              >
                <ChevronLeft />
              </button>
              <span>
                Seite {result.page} von {result.pages}
              </span>
              <button
                disabled={result.page >= result.pages}
                onClick={() => load(query, result.page + 1)}
                aria-label="Nächste Seite"
              >
                <ChevronRight />
              </button>
            </div>
          </>
        ) : (
          <Empty c={c} />
        ))}
    </section>
  );
}
function PropertyPage({
  c,
  slug,
  preview,
}: {
  c: Any;
  slug: string;
  preview: boolean;
}) {
  const [p, setP] = useState<Any>(null),
    [err, setErr] = useState(""),
    [selected, setSelected] = useState(0),
    [apply, setApply] = useState(false);
  useEffect(() => {
    const id = new URLSearchParams(location.search).get("id");
    (preview && id
      ? api("/admin/preview/properties").then((rows) =>
          rows.find((r: Any) => r.id === Number(id)),
        )
      : api("/public/properties/" + slug)
    )
      .then((v) => {
        if (!v) throw new Error("Immobilie nicht gefunden");
        setP(v);
        if (!preview) track(c, "property_view", "/immobilien/" + slug);
      })
      .catch((e) => setErr(e.message));
  }, [slug]);
  if (err)
    return (
      <section className="content-page">
        <h1>Immobilie nicht verfügbar.</h1>
        <p>{err}</p>
        <SiteLink href="/immobilien" className="text-link">
          Zur Immobilienübersicht <ArrowRight size={16} />
        </SiteLink>
      </section>
    );
  if (!p) return <div className="content-page">Exposé wird geladen …</div>;
  const filePath = preview ? "/api/admin/files/" : "/api/public/files/";
  return (
    <section className="content-page detail-page">
      <SiteLink className="back-link" href="/immobilien">
        <ChevronLeft size={15} />
        Alle Immobilien
      </SiteLink>
      <Eyebrow>
        {p.offer === "rent" ? "Zur Miete" : "Zum Kauf"} · {p.postcode} {p.city}
      </Eyebrow>
      <h1>{p.title}</h1>
      <p className="muted">
        <MapPin size={14} />
        {p.show_address ? `${p.street} ${p.house_number}, ` : ""}
        {p.postcode} {p.city} {p.district}
      </p>
      {p.images.length > 0 && (
        <>
          <img
            className="detail-hero"
            src={filePath + p.images[selected].id}
            alt={p.images[selected].alt || p.title}
          />
          <div className="gallery-thumbs">
            {p.images.map((image: Any, i: number) => (
              <button
                key={image.id}
                onClick={() => setSelected(i)}
                aria-label={"Bild " + (i + 1)}
                className={i === selected ? "selected" : ""}
              >
                <img
                  src={filePath + image.id}
                  alt={image.alt || "Immobilienbild"}
                />
              </button>
            ))}
          </div>
        </>
      )}
      <div className="detail-columns">
        <article>
          <div className="facts">
            <div>
              <strong>{p.area} m²</strong>
              <small>Wohnfläche</small>
            </div>
            <div>
              <strong>{p.rooms}</strong>
              <small>Zimmer</small>
            </div>
            <div>
              <strong>{p.year || "—"}</strong>
              <small>Baujahr</small>
            </div>
            <div>
              <strong>{p.type === "house" ? "Haus" : "Wohnung"}</strong>
              <small>Objekttyp</small>
            </div>
          </div>
          {[
            ["Beschreibung", p.description],
            ["Ausstattung", p.equipment],
            ["Lage", p.location],
            ["Weitere Informationen", p.notes],
          ].map(
            ([heading, text]) =>
              text && (
                <div className="description-block" key={heading}>
                  <h2>{heading}</h2>
                  <p className="preserve">{text}</p>
                </div>
              ),
          )}
          <div className="feature-tags">
            {p.features.map((f: string) => (
              <span key={f}>
                <Check size={14} />
                {f}
              </span>
            ))}
          </div>
          <h2>Energie & Eigenschaften</h2>
          <dl className="info-list">
            {Object.entries({
              Heizung: p.heating,
              Energieträger: p.energy_source,
              Energieausweis: {
                unknown: "Nicht angegeben",
                exempt: "Ausnahme",
                demand: "Bedarfsausweis",
                consumption: "Verbrauchsausweis",
              }[p.certificate as string],
              Kennwert:
                p.energy_value != null
                  ? `${p.energy_value} kWh/(m²·a)`
                  : "Nicht angegeben",
              Effizienzklasse: p.energy_class,
              "Gültig bis": p.energy_until,
              Ausnahmegrund: p.exemption_reason,
              Zustand: p.condition,
              Verfügbar: p.available,
              Barrierefreiheit: p.accessibility,
              Haustiere: p.pets,
            }).map(
              ([k, v]) =>
                v && (
                  <div key={k}>
                    <dt>{k}</dt>
                    <dd>{v}</dd>
                  </div>
                ),
            )}
          </dl>
        </article>
        <aside className="inquiry-box">
          <Eyebrow>Ihre nächste Perspektive</Eyebrow>
          <h2>{money(p.price)}</h2>
          <p>{p.offer === "rent" ? "Kaltmiete / Monat" : "Kaufpreis"}</p>
          {p.offer === "rent" ? (
            <dl className="info-list">
              {[
                ["Nebenkosten", money(p.service_charge)],
                [
                  "Heizkosten",
                  p.heating_included
                    ? "In Nebenkosten enthalten"
                    : money(p.heating_cost),
                ],
                ["Warmmiete", money(p.total_rent)],
                ["Kaution", money(p.deposit)],
                ["Stellplatz (zusätzlich)", money(p.parking_cost)],
                ["Möblierung (zusätzlich)", money(p.furniture_cost)],
              ].map(([k, v]) => (
                <div key={k}>
                  <dt>{k}</dt>
                  <dd>{v}</dd>
                </div>
              ))}
            </dl>
          ) : (
            <p>
              {p.commission && `Provision: ${p.commission}`}
              {p.maintenance > 0 && ` · Hausgeld: ${money(p.maintenance)}`}
            </p>
          )}
          {c.modules.applications && (
            <button
              className="button"
              onClick={() => {
                setApply(true);
                track(c, "inquiry_click", "/immobilien/" + slug);
                setTimeout(
                  () =>
                    document
                      .getElementById("application")
                      ?.scrollIntoView({ behavior: "smooth" }),
                  100,
                );
              }}
            >
              Interesse an dieser Immobilie
              <ArrowUpRight size={17} />
            </button>
          )}
          {p.contact && <p>Ihr Ansprechpartner: {p.contact}</p>}
          {c.phone && (
            <a href={"tel:" + c.phone} className="text-link">
              <Phone size={14} />
              {c.phone}
            </a>
          )}
        </aside>
      </div>
      {apply && (
        <div id="application" className="application-form">
          <Eyebrow>Interesse bekunden</Eyebrow>
          <h2>
            Vielleicht Ihr <span>neues Zuhause.</span>
          </h2>
          <ContactForm c={c} propertyId={p.id} />
        </div>
      )}
    </section>
  );
}
function Contact({ c }: { c: Any }) {
  return (
    <section className="contact-page content-page">
      <div className="contact-intro">
        <Eyebrow>Ein guter Anfang</Eyebrow>
        <h1>
          Ihre Pläne.
          <br />
          <span>Unser Gespräch.</span>
        </h1>
        <p>
          Ob erste Idee oder konkretes Vorhaben –<br />
          wir freuen uns, Sie kennenzulernen.
        </p>
        <div className="contact-details">
          {c.email && (
            <a href={"mailto:" + c.email}>
              <Mail size={20} />
              <span>
                <small>Schreiben Sie uns</small>
                {c.email}
              </span>
              <ArrowUpRight size={16} />
            </a>
          )}
          {c.phone && (
            <a href={"tel:" + c.phone}>
              <Phone size={20} />
              <span>
                <small>Rufen Sie uns an</small>
                {c.phone}
              </span>
              <ArrowUpRight size={16} />
            </a>
          )}
          {c.address && (
            <div>
              <MapPin size={20} />
              <span>
                <small>Besuchen Sie uns</small>
                {c.address}
              </span>
            </div>
          )}
        </div>
        <p className="contact-note">Persönlich. Vertraulich. Unverbindlich.</p>
      </div>
      <div className="form-panel">
        <Eyebrow>Persönlich für Sie da</Eyebrow>
        <h2>Was haben Sie vor?</h2>
        <p>
          Erzählen Sie uns von Ihren Plänen.
          <br />
          Wir melden uns persönlich bei Ihnen.
        </p>
        <ContactForm c={c} />
      </div>
    </section>
  );
}
export function ContactForm({
  c,
  propertyId,
  page = "",
  subject = "Kontakt",
}: {
  c: Any;
  propertyId?: number;
  page?: string;
  subject?: string;
}) {
  const preview = useContext(PreviewContext);
  const targets =
    c.forms[page || ""] || c.forms[propertyId ? "application" : "contact"];
  const [busy, setBusy] = useState(false),
    [err, setErr] = useState(""),
    [success, setSuccess] = useState<Any>(null),
    [key, setKey] = useState("");
  useEffect(() => setKey(crypto.randomUUID()), []);
  async function submit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    if (busy || preview) return;
    setBusy(true);
    setErr("");
    const d = Object.fromEntries(new FormData(e.currentTarget));
    try {
      const result = await api("/public/inquiries", {
        method: "POST",
        headers: { "Idempotency-Key": key },
        body: JSON.stringify({
          ...d,
          consent: d.consent === "on",
          property_id: propertyId || null,
          page,
        }),
      });
      setSuccess(result);
    } catch (error: Any) {
      setErr(error.message);
    } finally {
      setBusy(false);
    }
  }
  if (success)
    return (
      <div className="form-success" role="status">
        <span>
          <Check size={26} />
        </span>
        <h3>Vielen Dank für Ihr Vertrauen.</h3>
        <p>Ihre Anfrage wurde angenommen und wird persönlich bearbeitet.</p>
        <small>
          Ihre Anfragekennung: #{success.reference}
          <br />
          Bitte für eine mögliche Dokumentenrückgabe aufbewahren.
        </small>
        {c.modules.disclosure && c.disclosure_returns && (
          <div className="return-code">
            <small>
              Persönlicher Rückgabecode – zusammen mit der Kennung sicher
              aufbewahren:
            </small>
            <code>{success.document_token}</code>
            <small>
              Er berechtigt nur zum Hochladen, nicht zum Lesen von Dokumenten.
            </small>
          </div>
        )}
        <button
          className="text-link"
          onClick={() => {
            setSuccess(null);
            setKey(crypto.randomUUID());
          }}
        >
          Weitere Anfrage <ArrowUpRight size={14} />
        </button>
      </div>
    );
  return (
    <form className="contact-form" onSubmit={submit}>
      <div className="form-row">
        <label>
          Vorname *
          <input
            name="first_name"
            autoComplete="given-name"
            required
            maxLength={100}
          />
        </label>
        <label>
          Nachname *
          <input
            name="last_name"
            autoComplete="family-name"
            required
            maxLength={100}
          />
        </label>
      </div>
      <label>
        E-Mail *
        <input name="email" type="email" autoComplete="email" required />
      </label>
      <label>
        Telefon {targets.phone_required ? "*" : "(optional)"}
        <input
          name="phone"
          type="tel"
          autoComplete="tel"
          required={targets.phone_required}
        />
      </label>
      <label>
        Ihr Anliegen
        <select
          name="subject"
          defaultValue={propertyId ? "Immobilienbewerbung" : subject}
        >
          <option>Kontakt</option>
          <option>Verkaufen</option>
          <option>Vermieten</option>
          <option>Bewertung</option>
          <option>Beratung</option>
          <option>Suchwunsch</option>
          {![
            "Kontakt",
            "Verkaufen",
            "Vermieten",
            "Bewertung",
            "Beratung",
            "Suchwunsch",
          ].includes(subject) && <option>{subject}</option>}
          {propertyId && <option>Immobilienbewerbung</option>}
        </select>
      </label>
      <label>
        Ihre Nachricht *
        <textarea
          name="message"
          required
          minLength={5}
          maxLength={10000}
          rows={4}
        />
      </label>
      <div className="honeypot" aria-hidden="true">
        <label>
          Website
          <input name="website" tabIndex={-1} autoComplete="off" />
        </label>
      </div>
      <label className="checkbox-label">
        <input type="checkbox" name="consent" required />
        <span>
          Ich habe die{" "}
          <SiteLink href="/datenschutz" target="_blank">
            Datenschutzhinweise
          </SiteLink>{" "}
          gelesen und stimme der Verarbeitung meiner Angaben zur Bearbeitung
          dieser Anfrage zu. *
        </span>
      </label>
      {err && (
        <p className="notice error" role="alert">
          {err}
        </p>
      )}
      <button className="button" disabled={busy || preview}>
        {preview
          ? "Vorschau · kein Versand"
          : busy
            ? "Anfrage wird gesendet …"
            : "Anfrage absenden"}
        <ArrowUpRight size={17} />
      </button>
      <small className="form-footnote">
        * Erforderliche Angaben. Keine Newsletter-Anmeldung.
      </small>
    </form>
  );
}
function Disclosure({ c }: { c: Any }) {
  const preview = useContext(PreviewContext);
  const [message, setMessage] = useState(""),
    [busy, setBusy] = useState(false);
  async function submit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    if (preview) return;
    setBusy(true);
    try {
      const f = new FormData(e.currentTarget);
      f.set("consent", "true");
      const r = await api("/public/disclosure-return", {
        method: "POST",
        body: f,
      });
      setMessage(r.message);
      e.currentTarget?.reset();
    } catch (e: Any) {
      setMessage(e.message);
    } finally {
      setBusy(false);
    }
  }
  return (
    <section className="content-page narrow disclosure-page">
      <Eyebrow>Für Mietinteressenten</Eyebrow>
      <h1>
        Ihre Selbstauskunft.
        <br />
        <span>In Ruhe vorbereitet.</span>
      </h1>
      <p className="lead preserve">{c.disclosure_text}</p>
      <div className="pdf-card">
        <div className="pdf-icon">
          <FileText size={36} />
          <span>PDF</span>
        </div>
        <div>
          <Eyebrow>{c.company}</Eyebrow>
          <h2>Ihre Unterlagen. Gut vorbereitet.</h2>
          <p>Das aktuelle Dokument Ihres Immobilienpartners.</p>
          <a
            className="button"
            href={
              (preview ? "/api/admin/files/" : "/api/public/files/") +
              c.disclosure_pdf
            }
            download
          >
            Selbstauskunft herunterladen <Download size={17} />
          </a>
        </div>
      </div>
      <h2>So nutzen Sie das Dokument</h2>
      <div className="steps">
        {[
          [
            "01",
            "PDF herunterladen",
            "Speichern Sie das bereitgestellte Dokument auf Ihrem Gerät.",
          ],
          [
            "02",
            "In Ruhe ausfüllen",
            "Nutzen Sie ein geeignetes PDF-Programm oder drucken Sie das Dokument aus.",
          ],
          [
            "03",
            "Rückgabe abstimmen",
            "Besprechen Sie die sichere Rückgabe mit Ihrem Ansprechpartner.",
          ],
        ].map(([n, h, t]) => (
          <div key={n}>
            <span>{n}</span>
            <h3>{h}</h3>
            <p>{t}</p>
          </div>
        ))}
      </div>
      <div className="return-info">
        <h2>Ausgefüllt – und dann?</h2>
        <p>
          Beim Herunterladen werden keine ausgefüllten Formulardaten
          übermittelt. Die Selbstauskunft ist keine Voraussetzung für eine erste
          Kontaktaufnahme.
        </p>
        {c.modules.contact && (
          <SiteLink className="text-link" href="/kontakt">
            Rückgabe abstimmen <ArrowUpRight size={15} />
          </SiteLink>
        )}
      </div>
      {c.disclosure_returns && (
        <form onSubmit={submit} className="form-panel">
          <Eyebrow>Geschützte Übermittlung</Eyebrow>
          <h2>Unterlagen sicher zurückgeben</h2>
          <p>
            Verwenden Sie Kennung und persönlichen Rückgabecode Ihrer bereits
            angenommenen Anfrage.
          </p>
          <div className="form-row">
            <label>
              Anfragekennung
              <input required name="reference" type="number" min="1" />
            </label>
            <label>
              E-Mail der Anfrage
              <input required name="email" type="email" />
            </label>
          </div>
          <label>
            Persönlicher Rückgabecode
            <input
              required
              name="return_code"
              autoComplete="off"
              type="password"
              minLength={64}
              maxLength={64}
            />
          </label>
          <label>
            Ausgefülltes PDF (max. 10 MB)
            <input name="file" type="file" accept="application/pdf" required />
          </label>
          <label className="checkbox-label">
            <input type="checkbox" name="consent" required />
            <span>
              Ich stimme der geschützten Verarbeitung gemäß{" "}
              <SiteLink href="/datenschutz">Datenschutzhinweis</SiteLink> zu.
            </span>
          </label>
          <button className="button" disabled={busy || preview}>
            {busy ? "Wird übertragen …" : "Dokument privat übermitteln"}
            <ArrowUpRight size={17} />
          </button>
          {message && <p role="status">{message}</p>}
        </form>
      )}
    </section>
  );
}
