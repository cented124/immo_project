// Production-only Next server; the desktop gateway owns the public loopback port.
const fs = require("fs");
const http = require("http");
const path = require("path");
const [dir, portFile] = process.argv.slice(2);
if (!dir || !portFile) process.exit(2);
process.chdir(dir);
const next = require(path.join(dir, "node_modules", "next"));
const app = next({ dev: false, dir, hostname: "127.0.0.1" });
let server;
let stopping = false;
async function stop() {
  if (stopping) return;
  stopping = true;
  if (server) server.close();
  await app.close();
  process.exit(0);
}
process.stdin.setEncoding("utf8");
process.stdin.on("data", (value) => {
  if (value.includes("stop\n")) stop();
});
process.stdin.on("end", stop);
process.on("SIGTERM", stop);
process.on("SIGINT", stop);
app
  .prepare()
  .then(() => {
    const handle = app.getRequestHandler();
    server = http.createServer((req, res) => handle(req, res));
    server.listen(0, "127.0.0.1", () => {
      const temporary = portFile + ".tmp";
      fs.writeFileSync(
        temporary,
        JSON.stringify({ port: server.address().port }),
      );
      fs.renameSync(temporary, portFile);
    });
  })
  .catch(() => {
    console.error(
      "Frontend konnte nicht starten. Bitte REPARIEREN.cmd verwenden.",
    );
    process.exit(1);
  });
