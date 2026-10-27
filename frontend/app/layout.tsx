import type { Metadata } from "next";
import "@fontsource/manrope/400.css";
import "@fontsource/manrope/500.css";
import "@fontsource/manrope/600.css";
import "@fontsource/barlow-condensed/400.css";
import "@fontsource/barlow-condensed/500.css";
import "./globals.css";
import "./builder.css";
export const metadata: Metadata = {
  title: "Raumwerk · Immobilien mit Perspektive",
  description: "Persönliche Immobilienberatung und ausgewählte Immobilien.",
};
export default function Layout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="de" data-scroll-behavior="smooth">
      <body>{children}</body>
    </html>
  );
}
