/* AI/developer build tool. The importing user only selects the resulting ZIP. */
const fs = require("fs"),
  path = require("path"),
  cp = require("child_process"),
  os = require("os");
const root = path.resolve(__dirname, "..");
const esbuild = require(path.join(root, "frontend/node_modules/esbuild"));
const args = process.argv.slice(2);
function option(key, fallback) {
  const i = args.indexOf("--" + key);
  return i < 0 ? fallback : args[i + 1];
}
const source = path.resolve(option("source", path.join(root, "frontend")));
const target = path.resolve(
  option("output", path.join(root, "downloads/Raumwerk-Frontend.zip")),
);
const manifestPath = option("manifest", "");
const theme = manifestPath
  ? JSON.parse(fs.readFileSync(manifestPath, "utf8"))
  : JSON.parse(
      fs.readFileSync(path.join(root, "templates/atelier.json"), "utf8"),
    );
const identity = option("id", "frontend-" + Date.now().toString(36));
const name = option("name", "Mein eigenes Frontend");
const build = fs.mkdtempSync(path.join(os.tmpdir(), "raumwerk-browser-"));
(async () => {
  try {
    const imports = [
      "@fontsource/manrope/400.css",
      "@fontsource/manrope/500.css",
      "@fontsource/manrope/600.css",
      "@fontsource/barlow-condensed/400.css",
      "@fontsource/barlow-condensed/500.css",
      path.join(source, "app/globals.css"),
    ];
    const extra = option("css", path.join(source, "app/perspective.css"));
    if (fs.existsSync(extra)) imports.push(extra);
    const entry =
      imports.map((p) => "import " + JSON.stringify(p) + ";").join("\n") +
      `
      import React from 'react'; import { createRoot } from 'react-dom/client';
      import Website from ${JSON.stringify(path.join(source, "components/Website.tsx"))};
      window.Raumwerk.ready().then(context => createRoot(document.getElementById('root')).render(
        <Website path={context.path} initialConfig={context.config} embedded={true} />
      )).catch(error => { document.getElementById('root').textContent = error.message; });
    `;
    await esbuild.build({
      stdin: { contents: entry, loader: "tsx", resolveDir: source },
      absWorkingDir: source,
      outdir: build,
      entryNames: "app",
      assetNames: "assets/[name]-[hash]",
      bundle: true,
      minify: true,
      format: "iife",
      platform: "browser",
      target: ["es2022"],
      jsx: "automatic",
      define: { "process.env.NODE_ENV": '"production"' },
      nodePaths: [path.join(root, "frontend/node_modules")],
      alias: { "next/link": path.join(root, "frontend/portable/Link.tsx") },
      plugins: [
        {
          name: "local-public-assets",
          setup(build) {
            build.onResolve({ filter: /^\// }, (args) =>
              args.kind === "url-token"
                ? { path: "./public/" + args.path.slice(1), external: true }
                : undefined,
            );
          },
        },
      ],
      loader: {
        ".woff2": "file",
        ".woff": "file",
        ".png": "file",
        ".jpg": "file",
        ".svg": "dataurl",
      },
    });
    function copyPublic(folder, relative = "") {
      for (const item of fs.readdirSync(folder, { withFileTypes: true })) {
        if (item.isSymbolicLink() || item.name.startsWith("."))
          throw new Error("Ungeeignete öffentliche Datei: " + item.name);
        const rel = path.join(relative, item.name),
          from = path.join(folder, item.name),
          to = path.join(build, "public", rel);
        if (item.isDirectory()) copyPublic(from, rel);
        else {
          fs.mkdirSync(path.dirname(to), { recursive: true });
          fs.copyFileSync(from, to);
        }
      }
    }
    if (fs.existsSync(path.join(source, "public")))
      copyPublic(path.join(source, "public"));
    const picture = path.join(source, "public/architecture.png");
    fs.writeFileSync(
      path.join(build, "LICENSE-fonts.txt"),
      ["manrope", "barlow-condensed"]
        .map((font) =>
          fs.readFileSync(
            path.join(
              root,
              "frontend/node_modules/@fontsource",
              font,
              "LICENSE",
            ),
            "utf8",
          ),
        )
        .join("\n\n"),
    );
    const manifest = {
      ...theme,
      id: identity,
      name,
      version: 3,
      entry: "index.html",
      assets: fs.existsSync(picture)
        ? {
            hero_image: "public/architecture.png",
            approach_image: "public/architecture.png",
            ...(theme.assets || {}),
          }
        : { ...(theme.assets || {}) },
    };
    fs.writeFileSync(
      path.join(build, "manifest.json"),
      JSON.stringify(manifest, null, 2),
    );
    fs.writeFileSync(
      path.join(build, "index.html"),
      '<!doctype html><html lang="de"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><link rel="stylesheet" href="./app.css"></head><body><div id="root"></div><script defer src="./app.js"></script></body></html>',
    );
    fs.writeFileSync(
      path.join(build, "README.md"),
      "# Dein Frontend\n\nDieses ZIP unverändert im Frontend-Studio auswählen. Prüfen, als Entwurf übernehmen, Vorschau prüfen und veröffentlichen. Keine Firmendaten oder Zugänge werden importiert.\n",
    );
    fs.mkdirSync(path.dirname(target), { recursive: true });
    const python = option(
      "python",
      [
        path.join(root, ".venv/bin/python"),
        path.join(root, ".runtime/python/python.exe"),
      ].find((p) => fs.existsSync(p)) ||
        (process.platform === "win32" ? "python" : "python3"),
    );
    const result = cp.spawnSync(
      python,
      [
        "-X",
        "utf8",
        "-c",
        'import sys,zipfile,pathlib; source=pathlib.Path(sys.argv[1]); z=zipfile.ZipFile(sys.argv[2],"w",zipfile.ZIP_DEFLATED); [z.write(p,p.relative_to(source).as_posix()) for p in sorted(source.rglob("*")) if p.is_file()]; z.close()',
        build,
        target,
      ],
      { stdio: "inherit" },
    );
    if (result.status !== 0) throw new Error("ZIP konnte nicht gebaut werden.");
    if (fs.statSync(target).size > 10 * 1024 * 1024)
      throw new Error(
        "ZIP überschreitet die Importgrenze von 10 MB. Bilder verkleinern.",
      );
    console.log("Importfertiges Paket: " + target);
  } finally {
    fs.rmSync(build, { recursive: true, force: true });
  }
})().catch((error) => {
  console.error(error.message);
  process.exit(1);
});
