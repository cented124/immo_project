/* Raumwerk browser bundle SDK. The host exposes public functions, never sessions. */
(() => {
  if (window.Raumwerk) return;
  // Opaque sandbox origins do not expose every secure-context convenience API.
  // getRandomValues remains available; keep the existing form idempotency keys.
  if (!crypto.randomUUID)
    crypto.randomUUID = () => {
      const bytes = crypto.getRandomValues(new Uint8Array(16));
      bytes[6] = (bytes[6] & 15) | 64;
      bytes[8] = (bytes[8] & 63) | 128;
      const hex = [...bytes]
        .map((b) => b.toString(16).padStart(2, "0"))
        .join("");
      return `${hex.slice(0, 8)}-${hex.slice(8, 12)}-${hex.slice(12, 16)}-${hex.slice(16, 20)}-${hex.slice(20)}`;
    };
  const pending = new Map();
  let context, resolveReady;
  const ready = new Promise((resolve) => {
    resolveReady = resolve;
  });
  let counter = 0;
  function send(kind, data = {}) {
    const id = "rw-" + ++counter;
    return new Promise((resolve, reject) => {
      const timer = setTimeout(() => {
        pending.delete(id);
        reject(
          new Error("Die Website antwortet nicht. Bitte erneut versuchen."),
        );
      }, 45000);
      pending.set(id, { resolve, reject, timer });
      parent.postMessage(
        { channel: "raumwerk-frontend-v3", id, kind, ...data },
        "*",
      );
    });
  }
  window.addEventListener("message", (event) => {
    if (event.source !== parent || event.data?.channel !== "raumwerk-host-v3")
      return;
    const item = pending.get(event.data.id);
    if (!item) return;
    clearTimeout(item.timer);
    pending.delete(event.data.id);
    event.data.error
      ? item.reject(new Error(event.data.error))
      : item.resolve(event.data.result);
  });
  async function request(url, options = {}) {
    await ready;
    let body = options.body ?? null;
    if (body instanceof FormData) body = { multipart: [...body.entries()] };
    const headers = Object.fromEntries(
      new Headers(options.headers || {}).entries(),
    );
    const result = await send("request", {
      url: String(url),
      method: options.method || "GET",
      headers,
      body,
    });
    return new Response(result.body, {
      status: result.status,
      headers: result.headers,
    });
  }
  const originalFetch = window.fetch.bind(window);
  window.fetch = (input, options) => {
    const url = typeof input === "string" ? input : input.url || String(input);
    return url.startsWith("/api/")
      ? request(url, options)
      : originalFetch(input, options);
  };
  function media(url) {
    if (!url || !context || /^(data:|blob:)/.test(url)) return url;
    if (
      context.preview &&
      /^\/api\/(public|admin)\/files\/[a-f0-9]{32}$/.test(url)
    )
      return context.base + "__media/" + url.split("/").pop();
    const prefix = "/api/public/frontend/" + context.config.template + "/";
    const privatePrefix =
      "/api/admin/frontend/" + context.config.template + "/";
    if (context.preview && url.startsWith(privatePrefix))
      return context.base + url.slice(privatePrefix.length);
    if (context.preview && url.startsWith(prefix))
      return context.base + url.slice(prefix.length);
    if (
      url.startsWith("/") &&
      !url.startsWith("/api/") &&
      !url.startsWith("/_next/")
    )
      return context.base + "public/" + url.slice(1);
    return url;
  }
  function rewriteImages() {
    document.querySelectorAll("img[src],source[src]").forEach((node) => {
      const before = node.getAttribute("src"),
        after = media(before);
      if (after !== before) node.setAttribute("src", after);
    });
  }
  document.addEventListener("click", (event) => {
    const link = event.target.closest?.("a[href]");
    if (!link) return;
    const href = link.getAttribute("href");
    if (!href || href.startsWith("#") || href.startsWith("blob:")) return;
    event.preventDefault();
    const kind = /^\/api\/(public|admin)\/files\//.test(href)
      ? "download"
      : "navigate";
    send(kind, { url: href }).catch((error) => {
      window.dispatchEvent(
        new CustomEvent("raumwerk:error", { detail: error.message }),
      );
    });
  });
  window.Raumwerk = {
    ready: () => ready,
    request,
    navigate: (url) => send("navigate", { url }),
    media,
  };
  window.addEventListener("error", (event) =>
    send("runtime-error", {
      message: event.message || "Fehler im importierten Frontend.",
    }).catch(() => {}),
  );
  window.addEventListener("unhandledrejection", (event) =>
    send("runtime-error", {
      message: event.reason?.message || "Fehler im importierten Frontend.",
    }).catch(() => {}),
  );
  send("ready")
    .then((result) => {
      context = result;
      // Original public React components also use location.search for preview/id.
      // The document's own URL keeps the same query parameters as the outer route.
      resolveReady(context);
      const observer = new MutationObserver(rewriteImages);
      observer.observe(document.documentElement, {
        childList: true,
        subtree: true,
        attributes: true,
        attributeFilter: ["src"],
      });
      rewriteImages();
    })
    .catch((error) => {
      document.body.textContent = error.message;
    });
})();
