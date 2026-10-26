import Link from "next/link";
export default function NotFound() {
  return (
    <main className="system-message">
      <span className="eyebrow">Neue Perspektiven</span>
      <h1>Hier geht es gerade nicht weiter.</h1>
      <p>Diese Seite oder Immobilie ist nicht verfügbar.</p>
      <Link className="button" href="/">
        Zur Startseite ↗
      </Link>
    </main>
  );
}
