"use client";
import { useEffect, useState, FormEvent } from "react";
import { api } from "./api";
type Any = any;
function Message({ text }: { text: string }) {
  return text ? (
    <p className="notice" role="status">
      {text}
    </p>
  ) : null;
}
export function AccountPanel() {
  const [message, setMessage] = useState("");
  async function submit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const data = Object.fromEntries(new FormData(e.currentTarget));
    if (data.password !== data.repeat) {
      setMessage("Die neuen Passwörter stimmen nicht überein.");
      return;
    }
    try {
      const r = await api("/admin/account/password", {
        method: "POST",
        body: JSON.stringify(data),
      });
      setMessage(r.message);
      location.assign("/admin");
    } catch (e: Any) {
      setMessage(e.message);
    }
  }
  return (
    <section className="admin-card">
      <div className="card-header">
        <h2>Mein Passwort ändern</h2>
        <p>Nach einer Änderung werden alle Sitzungen dieses Kontos beendet.</p>
      </div>
      <form onSubmit={submit}>
        <div className="field-grid">
          <label>
            Aktuelles Passwort
            <input
              name="current_password"
              type="password"
              autoComplete="current-password"
              required
            />
          </label>
          <label>
            Neues Passwort
            <input
              name="password"
              type="password"
              autoComplete="new-password"
              minLength={12}
              required
            />
          </label>
          <label>
            Neues Passwort wiederholen
            <input
              name="repeat"
              type="password"
              autoComplete="new-password"
              minLength={12}
              required
            />
          </label>
        </div>
        <button className="button">Passwort ändern</button>
      </form>
      <Message text={message} />
    </section>
  );
}
export function TeamControls({
  users,
  refresh,
}: {
  users: Any[];
  refresh: () => void;
}) {
  const [message, setMessage] = useState("");
  async function update(e: FormEvent<HTMLFormElement>, id: number) {
    e.preventDefault();
    const f = new FormData(e.currentTarget);
    const data: Any = { role: f.get("role"), active: f.get("active") === "on" };
    if (f.get("password")) data.password = f.get("password");
    try {
      await api("/admin/users/" + id, {
        method: "PATCH",
        body: JSON.stringify(data),
      });
      setMessage("Konto aktualisiert. Bestehende Sitzungen wurden beendet.");
      await api("/admin/me")
        .then(() => refresh())
        .catch(() => location.assign("/admin"));
    } catch (e: Any) {
      setMessage(e.message);
    }
  }
  return (
    <>
      <h3 className="team-controls-title">Konten bearbeiten oder sperren</h3>
      {users.map((u) => (
        <details className="page-editor" key={u.id}>
          <summary>
            {u.email} · {u.active ? "Aktiv" : "Gesperrt"}
          </summary>
          <form
            key={u.role + String(u.active)}
            onSubmit={(e) => update(e, u.id)}
          >
            <div className="field-grid">
              <label>
                Rolle
                <select name="role" defaultValue={u.role}>
                  <option value="staff">Mitarbeiter</option>
                  <option value="admin">Administrator</option>
                </select>
              </label>
              <label>
                Neues Passwort (optional)
                <input
                  name="password"
                  type="password"
                  minLength={12}
                  autoComplete="new-password"
                />
              </label>
            </div>
            <label className="checkbox-label">
              <input name="active" type="checkbox" defaultChecked={u.active} />
              Konto aktiv
            </label>
            <div className="button-row">
              <button className="small-button">Konto speichern</button>
              <button
                className="small-button danger"
                type="button"
                onClick={async () => {
                  if (!confirm("Dieses Konto dauerhaft löschen?")) return;
                  try {
                    await api("/admin/users/" + u.id, { method: "DELETE" });
                    refresh();
                    setMessage("Konto gelöscht.");
                  } catch (e: Any) {
                    setMessage(e.message);
                  }
                }}
              >
                Konto löschen
              </button>
            </div>
          </form>
        </details>
      ))}
      <Message text={message} />
    </>
  );
}
export function TemplateLibrary({
  config: c,
  setConfig: set,
}: {
  config: Any;
  setConfig: (v: Any) => void;
}) {
  const [templates, setTemplates] = useState<Any[]>([]),
    [text, setText] = useState(""),
    [message, setMessage] = useState(""),
    [busy, setBusy] = useState(false);
  const load = () =>
    api("/admin/templates")
      .then(setTemplates)
      .catch((e) => setMessage(e.message));
  useEffect(() => {
    load();
  }, []);
  function choose(m: Any) {
    const { primary, accent, font, ...layout } = m.theme || {};
    set({
      ...c,
      template: m.id,
      template_adapter: m.adapter,
      ...(m.theme ? { primary, accent, font, frontend_theme: layout } : {}),
    });
  }
  async function importManifest() {
    setBusy(true);
    try {
      const data = JSON.parse(text);
      const r = await api("/admin/templates/import", {
        method: "POST",
        body: JSON.stringify(data),
      });
      setMessage(r.message);
      await load();
      choose(r.manifest);
    } catch (e: Any) {
      setMessage(e.message);
    } finally {
      setBusy(false);
    }
  }
  return (
    <section className="admin-card">
      <div className="card-header">
        <h2>Template-Bibliothek & Import</h2>
        <p>
          Ein JSON-Manifest verbindet ein Design mit einem registrierten
          Funktionsadapter. Es lädt keinen fremden Programmcode.
        </p>
      </div>
      <label>
        Gespeichertes Template auswählen
        <select
          value={c.template}
          onChange={(e) => {
            const m = templates.find((t) => t.id === e.target.value);
            if (m) choose(m);
          }}
        >
          {templates.map((m) => (
            <option key={m.id} value={m.id}>
              {m.name} · Adapter {m.adapter}
            </option>
          ))}
        </select>
      </label>
      <label>
        Manifest-Datei (.json, maximal 64 KB)
        <input
          type="file"
          accept="application/json,.json"
          onChange={async (e) => {
            const f = e.target.files?.[0];
            if (f) {
              if (f.size > 65536) {
                setMessage("Maximal 64 KB.");
                return;
              }
              setText(await f.text());
            }
          }}
        />
      </label>
      <label>
        Manifest-Inhalt
        <textarea
          rows={7}
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder='{"id":"mein-design","name":"Mein Design","version":1,"adapter":"editorial",…}'
        />
      </label>
      <button
        className="small-button"
        disabled={busy || !text}
        onClick={importManifest}
      >
        {busy ? "Wird geprüft …" : "Prüfen und importieren"}
      </button>
      <Message text={message} />
    </section>
  );
}
export function FormRouting({
  config: c,
  setConfig: set,
}: {
  config: Any;
  setConfig: (v: Any) => void;
}) {
  const forms = [
    ...c.pages
      .filter((p: Any) => p.form)
      .map((p: Any) => ({ id: p.slug, title: p.title })),
    { id: "disclosure", title: "PDF-Rückgabe" },
  ];
  function change(id: string, key: string, value: boolean) {
    set({
      ...c,
      forms: {
        ...c.forms,
        [id]: { ...(c.forms[id] || c.forms.contact), [key]: value },
      },
    });
  }
  return (
    <section className="admin-card">
      <div className="card-header">
        <h2>Ziele je Seitenformular</h2>
        <p>
          Verkauf, Vermietung, Bewertung und weitere Seiten können eigene Ziele
          und eine eigene Telefonpflicht erhalten.
        </p>
      </div>
      {forms.map((f: Any) => (
        <details className="page-editor" key={f.id}>
          <summary>
            {f.title} · {c.forms[f.id] ? "Eigene Ziele" : "Standardziele"}
          </summary>
          <label className="checkbox-label">
            <input
              type="checkbox"
              checked={!!c.forms[f.id]}
              onChange={(e) => {
                const next = { ...c.forms };
                if (e.target.checked)
                  next[f.id] = { ...c.forms.contact, store: true };
                else delete next[f.id];
                set({ ...c, forms: next });
              }}
            />
            Eigene Einstellungen verwenden
          </label>
          {c.forms[f.id] &&
            [
              ["store", "Im Adminbereich speichern"],
              ["email", "Per E-Mail zustellen"],
              ["telegram", "Per Telegram zustellen"],
              ...(f.id !== "disclosure"
                ? [["phone_required", "Telefon ist Pflicht"]]
                : []),
            ].map(([key, label]) => (
              <label className="toggle-row" key={key}>
                <div>
                  <strong>{label}</strong>
                </div>
                <input
                  type="checkbox"
                  role="switch"
                  checked={c.forms[f.id][key]}
                  onChange={(e) => change(f.id, key, e.target.checked)}
                />
              </label>
            ))}
        </details>
      ))}
    </section>
  );
}
