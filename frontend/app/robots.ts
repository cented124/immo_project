import type { MetadataRoute } from "next";
export const dynamic = "force-dynamic";

export default async function robots(): Promise<MetadataRoute.Robots> {
  try {
    const response = await fetch(`${process.env.API_INTERNAL_URL || "http://127.0.0.1:8000"}/api/public/search-index`, { cache: "no-store" });
    if (!response.ok) throw new Error("Backend nicht verfügbar");
    const index = await response.json();
    if (index.local) return { rules: { userAgent: "*", disallow: "/" } };
    return { rules: { userAgent: "*", allow: "/", disallow: ["/admin", "/api/", "/*?*preview=1*"] }, sitemap: index.origin + "/sitemap.xml" };
  } catch {
    return { rules: { userAgent: "*", disallow: "/" } };
  }
}
