export async function api(path: string, options: RequestInit = {}) {
  const isForm = options.body instanceof FormData;
  const response = await fetch("/api" + path, {
    ...options,
    headers: {
      ...(!isForm ? { "Content-Type": "application/json" } : {}),
      "X-Requested-With": "Raumwerk",
      ...options.headers,
    },
  });
  if (!response.ok) {
    let message = "Die Anfrage konnte nicht verarbeitet werden.";
    try {
      const e = await response.json();
      message =
        typeof e.detail === "string"
          ? e.detail
          : Array.isArray(e.detail)
            ? e.detail
                .map(
                  (v: { loc: string[]; msg: string }) =>
                    `${v.loc.slice(1).join(".")}: ${v.msg}`,
                )
                .join(" · ")
            : message;
    } catch {
      if (response.status === 403)
        message =
          "Zugriff verweigert. Bitte Sitzung und Website-Adresse prüfen.";
    }
    throw new Error(message);
  }
  if (response.status === 204) return null;
  return response.json();
}
export const money = (n: number) =>
  new Intl.NumberFormat("de-DE", {
    style: "currency",
    currency: "EUR",
    maximumFractionDigits: 0,
  }).format(n || 0);
export const labels: Record<string, string> = {
  draft: "Entwurf",
  published: "Veröffentlicht",
  reserved: "Reserviert",
  sold: "Verkauft / vermietet",
  archived: "Archiviert",
  new: "Neu",
  processing: "In Bearbeitung",
  answered: "Beantwortet",
  closed: "Abgeschlossen",
  contact: "Kontakt",
  application: "Immobilienbewerbung",
  sent: "Versendet",
  pending: "Ausstehend",
  retry: "Wiederholung",
  failed: "Fehlgeschlagen",
  email: "E-Mail",
  telegram: "Telegram",
  confirmation: "Bestätigung",
};
