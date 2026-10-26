import Website from "@/components/Website";
import Admin from "@/components/Admin";
import type { Metadata } from "next";
import { notFound } from "next/navigation";
export const dynamic = "force-dynamic";
type Props = {
  params: Promise<{ path?: string[] }>;
  searchParams: Promise<{ preview?: string }>;
};
export async function generateMetadata({ params,searchParams }: Props): Promise<Metadata> {
  const { path = [] } = await params;
  try {
    const c = await fetch(
      `${process.env.API_INTERNAL_URL || "http://127.0.0.1:8000"}/api/public/config`,
      { cache: "no-store" },
    ).then((r) => r.json());
    const page = c.pages.find((p: { slug: string }) => p.slug === path[0]);
    return {
      title: `${page?.title || c.seo_title} | ${c.company}`,
      description: page?.seo_description || c.seo_description,
      icons: c.favicon ? { icon: c.favicon } : undefined,
      robots: path[0] === "admin" || (await searchParams).preview==='1' ? { index: false, follow: false } : undefined,
    };
  } catch {
    return { title: "Raumwerk" };
  }
}
export default async function Page({ params, searchParams }: Props) {
  const { path = [] } = await params;
  if (path[0] === "admin") return <Admin tab={path[1] || "dashboard"} />;
  const preview = (await searchParams).preview === "1";
  let c;
  try {
    c = await fetch(
      `${process.env.API_INTERNAL_URL || "http://127.0.0.1:8000"}/api/public/config`,
      { cache: "no-store" },
    ).then((r) => (r.ok ? r.json() : null));
  } catch {}
  if (c && !preview && path.length) {
    const slug = path[0];
    const allowed =
      slug === "impressum" ||
      slug === "datenschutz" ||
      (slug === "immobilien" && c.modules.properties) ||
      (slug === "kontakt" && c.modules.contact) ||
      (slug === "selbstauskunft" && c.modules.disclosure) ||
      c.pages.some(
        (p: { slug: string; enabled: boolean }) => p.slug === slug && p.enabled,
      );
    if (
      !allowed ||
      path.length > 2 ||
      (path.length === 2 && slug !== "immobilien")
    )
      notFound();
    if (slug === "immobilien" && path[1]) {
      const response = await fetch(
        `${process.env.API_INTERNAL_URL || "http://127.0.0.1:8000"}/api/public/properties/${encodeURIComponent(path[1])}`,
        { cache: "no-store" },
      );
      if (response.status === 404) notFound();
    }
  }
  return <Website path={path} initialConfig={preview ? undefined : c} />;
}
