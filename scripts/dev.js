// Runs the backend (Flask, :5000) and frontend (static, :8080) together.
//   npm run setup   create backend/.venv and install requirements (one time)
//   npm run dev     start both, Ctrl+C stops both
//   npm start       same, and opens the app in Chrome once it is up
//   npm run db:up   start PostgreSQL + pgvector in Docker
//   npm run db:init apply the schema;  npm run db:seed  reset + load the knowledge base
const { spawn, spawnSync } = require("child_process");
const fs = require("fs");
const path = require("path");

const root = path.resolve(__dirname, "..");
const backendDir = path.join(root, "backend");
const frontendDir = path.join(root, "frontend");
const isWin = process.platform === "win32";
const venvPython = path.join(backendDir, ".venv", isWin ? "Scripts" : "bin", isWin ? "python.exe" : "python");

const FRONTEND_PORT = process.env.FRONTEND_PORT || "8080";

function run(cmd, args, cwd) {
  const r = spawnSync(cmd, args, { stdio: "inherit", cwd });
  if (r.status !== 0) process.exit(r.status || 1);
}

function setup() {
  if (!fs.existsSync(venvPython)) {
    const py = isWin ? ["py", ["-3.12", "-m", "venv", path.join(backendDir, ".venv")]] : ["python3", ["-m", "venv", path.join(backendDir, ".venv")]];
    run(py[0], py[1]);
  }
  run(venvPython, ["-m", "pip", "install", "-r", path.join(backendDir, "requirements.txt")]);
}

const services = {
  backend: { color: "\x1b[34m", cwd: backendDir, cmd: () => [venvPython, ["main.py"]] },
  frontend: { color: "\x1b[32m", cwd: frontendDir, cmd: () => [venvPython, ["-m", "http.server", FRONTEND_PORT]] },
};

const children = [];

function start(name) {
  const svc = services[name];
  const [cmd, args] = svc.cmd();
  const child = spawn(cmd, args, { cwd: svc.cwd, env: { ...process.env, PYTHONUNBUFFERED: "1" } });
  const tag = `${svc.color}[${name}]\x1b[0m `;
  const pipe = (stream, out) => {
    let buf = "";
    stream.on("data", (d) => {
      buf += d;
      const lines = buf.split(/\r?\n/);
      buf = lines.pop();
      lines.forEach((l) => out.write(tag + l + "\n"));
    });
  };
  pipe(child.stdout, process.stdout);
  pipe(child.stderr, process.stderr);
  child.on("exit", (code) => {
    console.log(`${tag}exited (${code})`);
    shutdown(code || 0);
  });
  children.push(child);
}

let closing = false;
function shutdown(code) {
  if (closing) return;
  closing = true;
  for (const c of children) {
    if (c.exitCode !== null) continue;
    if (isWin) spawnSync("taskkill", ["/pid", String(c.pid), "/T", "/F"], { stdio: "ignore" });
    else c.kill("SIGTERM");
  }
  process.exit(code);
}
process.on("SIGINT", () => shutdown(0));
process.on("SIGTERM", () => shutdown(0));

function openChrome(url) {
  console.log(`Opening ${url} in Chrome...`);
  const detach = { stdio: "ignore", detached: true };
  if (isWin) {
    const roots = [process.env.PROGRAMFILES, process.env["PROGRAMFILES(X86)"], process.env.LOCALAPPDATA].filter(Boolean);
    const chrome = roots.map((r) => path.join(r, "Google", "Chrome", "Application", "chrome.exe")).find((p) => fs.existsSync(p));
    if (chrome) spawn(chrome, [url], detach).on("error", (e) => console.error("Could not start Chrome:", e.message)).unref();
    else spawn("cmd", ["/c", "start", '""', url], { ...detach, windowsVerbatimArguments: true }).unref(); // default browser
  } else if (process.platform === "darwin") {
    spawn("open", ["-a", "Google Chrome", url], detach).unref();
  } else {
    spawn("google-chrome", [url], detach).on("error", () => spawn("xdg-open", [url], detach).unref()).unref();
  }
}

// Wait for both servers to answer before opening the browser.
function openWhenReady(url) {
  const http = require("http");
  const up = (u) => new Promise((res) => http.get(u, (r) => { r.resume(); res(true); }).on("error", () => res(false)));
  let tries = 0;
  const timer = setInterval(async () => {
    if ((await up(url)) && (await up("http://127.0.0.1:5000/healthz"))) { clearInterval(timer); openChrome(url); }
    else if (++tries > 60) clearInterval(timer);
  }, 1000);
}

const args = process.argv.slice(2);
const openBrowser = args.includes("--open");
const target = args.find((a) => !a.startsWith("--"));
if (target === "setup") {
  setup();
} else if (target === "db-init") {
  run(venvPython, ["-m", "scripts.init_db"], backendDir);
} else if (target === "db-seed") {
  run(venvPython, ["-m", "scripts.reset_and_setup_fintech"], backendDir);
  run(venvPython, ["-m", "scripts.ingest_fintech"], backendDir);
} else {
  if (!fs.existsSync(venvPython)) {
    console.error("backend/.venv not found. Run `npm run setup` first.");
    process.exit(1);
  }
  const names = target ? [target] : ["backend", "frontend"];
  names.forEach((n) => {
    if (!services[n]) { console.error(`Unknown target "${n}". Use backend or frontend.`); process.exit(1); }
    start(n);
  });
  if (!target) {
    console.log(`\n  Frontend: http://localhost:${FRONTEND_PORT}   Admin: http://localhost:${FRONTEND_PORT}/admin/login.html`);
    console.log("  Backend:  http://localhost:5000\n");
  }
  if (openBrowser) openWhenReady(`http://localhost:${FRONTEND_PORT}`);
}
