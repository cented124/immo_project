"use client";
import { useEffect, useRef, useState } from "react";
import Link from "next/link";

const channel = "raumwerk-frontend-v3";
export default function CustomFrontend({
  config: c,
  path,
  preview,
}: {
  config: any;
  path: string[];
  preview: boolean;
}) {
  const frame = useRef<HTMLIFrameElement>(null);
  const [error, setError] = useState("");
  const [ready, setReady] = useState(false);
  const [source, setSource] = useState("");
  useEffect(() => {
    const query = new URLSearchParams(location.search);
    setError("");
    setReady(false);
    setSource(c.frontend_package.entry + "?" + query.toString());
  }, [c.frontend_package.entry]);
  useEffect(() => {
    let live = true,
      active = 0;
    const timeout = window.setTimeout(() => {
      if (live)
        setError(
          "Das Frontend meldet sich nicht. Bitte das Paket mit Raumwerk-Anbindung erstellen lassen.",
        );
    }, 30000);
    const base = c.frontend_package.base;
    async function receive(event: MessageEvent) {
      const data = event.data;
      if (
        event.source !== frame.current?.contentWindow ||
        data?.channel !== channel ||
        typeof data.id !== "string"
      )
        return;
      if (active >= 12) return;
      active++;
      try {
        let result: any;
        if (data.kind === "ready") {
          clearTimeout(timeout);
          setReady(true);
          setError("");
          result = { config: c, path, preview, base, origin: location.origin };
        } else if (data.kind === "runtime-error") {
          setError(
            String(data.message || "Fehler im importierten Frontend.").slice(
              0,
              300,
            ),
          );
          result = true;
        } else if (data.kind === "navigate") {
          const configuredExternal = [...(c.social_links || []), c.email ? "mailto:" + c.email : "", c.phone ? "tel:" + c.phone : ""].filter(Boolean);
          if (configuredExternal.includes(String(data.url))) {
            location.assign(String(data.url));
            result = true;
          } else {
          const url = new URL(String(data.url), location.origin);
          if (
            url.origin !== location.origin ||
            !url.pathname.startsWith("/") ||
            url.pathname.startsWith("/api/") ||
            (url.pathname.startsWith("/admin") &&
              !["/admin", "/admin/design"].includes(url.pathname))
          )
            throw new Error("Dieses Navigationsziel ist nicht freigegeben.");
          if (preview && !url.pathname.startsWith("/admin"))
            url.searchParams.set("preview", "1");
          location.assign(url.pathname + url.search + url.hash);
          result = true;
          }
        } else if (data.kind === "request" || data.kind === "download") {
          let url = String(data.url),
            method = String(data.method || "GET").toUpperCase();
          if (
            url.length > 2048 ||
            !url.startsWith("/api/") ||
            url.includes("\\") ||
            url.includes("#")
          )
            throw new Error("Ungültige öffentliche Schnittstelle.");
          const parsed = new URL(url, location.origin);
          const pathname = parsed.pathname;
          if (preview && method !== "GET")
            throw new Error(
              "Die Vorschau sendet keine Anfragen oder Analysen.",
            );
          if (
            preview &&
            ["/api/admin/config", "/api/public/config"].includes(pathname)
          ) {
            const value = pathname.startsWith("/api/admin") ? { draft: c } : c;
            result = {
              body: new TextEncoder().encode(JSON.stringify(value)).buffer,
              status: 200,
              headers: { "Content-Type": "application/json" },
            };
          } else {
            const publicGet =
              /^\/api\/public\/(config|properties(?:\/[^/]+)?|files\/[a-f0-9]{32})$/.test(
                pathname,
              );
            const publicPost = [
              "/api/public/inquiries",
              "/api/public/events",
              "/api/public/disclosure-return",
            ].includes(pathname);
            const previewGet =
              preview &&
              pathname === "/api/admin/preview/properties" &&
              c.modules.properties;
            const previewFile =
              preview && /^\/api\/admin\/files\/[a-f0-9]{32}$/.test(pathname);
            if (
              !(
                (method === "GET" &&
                  (publicGet || previewGet || previewFile)) ||
                (method === "POST" && publicPost && !preview)
              )
            )
              throw new Error(
                "Das Frontend darf nur öffentliche Website-Funktionen verwenden.",
              );
            if (previewFile)
              url = base + "__media/" + pathname.split("/").pop();
            const headers: Record<string, string> = {};
            if (typeof data.headers?.["idempotency-key"] === "string")
              headers["Idempotency-Key"] = data.headers[
                "idempotency-key"
              ].slice(0, 128);
            let body: BodyInit | undefined;
            if (data.body?.multipart) {
              if (
                !Array.isArray(data.body.multipart) ||
                data.body.multipart.length > 12
              )
                throw new Error("Ungültiges Formular.");
              const form = new FormData();
              let size = 0;
              for (const [key, value] of data.body.multipart) {
                if (
                  typeof key !== "string" ||
                  !(typeof value === "string" || value instanceof File)
                )
                  throw new Error("Ungültiges Formularfeld.");
                size += typeof value === "string" ? value.length : value.size;
                if (size > 11 * 1024 * 1024) throw new Error("Datei zu groß.");
                form.append(key, value);
              }
              body = form;
            } else if (data.body != null) {
              if (
                typeof data.body !== "string" ||
                data.body.length > 128 * 1024
              )
                throw new Error("Formular zu groß.");
              body = data.body;
              headers["Content-Type"] = "application/json";
            }
            if (previewGet) headers["X-Requested-With"] = "Raumwerk";
            const response = await fetch(url, {
              method,
              headers,
              body: method === "GET" ? undefined : body,
              credentials: previewGet ? "same-origin" : "omit",
              signal: AbortSignal.timeout(30000),
            });
            const buffer = await response.arrayBuffer();
            if (data.kind === "download") {
              if (!response.ok) throw new Error("Datei nicht verfügbar.");
              const object = URL.createObjectURL(
                new Blob([buffer], {
                  type:
                    response.headers.get("Content-Type") || "application/pdf",
                }),
              );
              const link = document.createElement("a");
              link.href = object;
              link.download = "Raumwerk-Dokument.pdf";
              link.click();
              setTimeout(() => URL.revokeObjectURL(object), 1000);
              result = true;
            } else
              result = {
                body: buffer,
                status: response.status,
                headers: {
                  "Content-Type":
                    response.headers.get("Content-Type") || "application/json",
                },
              };
          }
        } else throw new Error("Unbekannte Frontend-Funktion.");
        if (live)
          event.source?.postMessage(
            { channel: "raumwerk-host-v3", id: data.id, result },
            { targetOrigin: "*" },
          );
      } catch (e: any) {
        if (live)
          event.source?.postMessage(
            {
              channel: "raumwerk-host-v3",
              id: data.id,
              error: e.message || "Anfrage fehlgeschlagen.",
            },
            { targetOrigin: "*" },
          );
      } finally {
        active--;
      }
    }
    window.addEventListener("message", receive);
    return () => {
      live = false;
      clearTimeout(timeout);
      window.removeEventListener("message", receive);
    };
  }, [c, path, preview]);
  return (
    <div className="custom-frontend-host">
      {preview && (
        <div className="custom-preview-bar">
          Unveröffentlichte Vorschau · Anfragen gesperrt{" "}
          <Link href="/admin/design">Zurück zum Baukasten ↗</Link>
        </div>
      )}
      {!ready && !error && (
        <p className="custom-loading" role="status">
          Dein Frontend wird geladen …
        </p>
      )}
      {error && (
        <div className="custom-error" role="alert">
          <h1>Frontend konnte nicht geladen werden.</h1>
          <p>{error}</p>
          <Link href="/admin/design">Zum Frontend-Studio</Link>
        </div>
      )}
      {source && (
        <iframe
          ref={frame}
          src={source}
          title={c.frontend_package.name}
          sandbox="allow-scripts allow-forms allow-downloads"
          referrerPolicy="no-referrer"
          className={
            preview ? "custom-site-frame with-preview" : "custom-site-frame"
          }
        />
      )}
    </div>
  );
}
