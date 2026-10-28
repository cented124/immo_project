import type { MetadataRoute } from "next";
export const dynamic = "force-dynamic";

export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  const response = await fetch(`${process.env.API_INTERNAL_URL || "http://127.0.0.1:8000"}/api/public/search-index`, { cache: "no-store" });
  if (!response.ok) throw new Error("Sitemap-Daten vorübergehend nicht verfügbar");
  const index = await response.json();
  return index.local ? [] : index.paths.map((path: string) => ({ url: index.origin + (path === "/" ? "" : path) }));
}
