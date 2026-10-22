// A portable npm entrypoint for preview supervisors that append Vite-style flags.
import { spawn } from "node:child_process";
import { fileURLToPath } from "node:url";
import path from "node:path";
import fs from "node:fs";
const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const args = process.argv.slice(2);
const option = (name, fallback) => {
  const i = args.indexOf(name);
  return i >= 0 ? args[i + 1] : fallback;
};
const venv = path.join(
  root,
  ".venv",
  process.platform === "win32" ? "Scripts/python.exe" : "bin/python",
);
// The optional project-local uv runtime also works in copy-based preview environments
// where a virtualenv's absolute interpreter symlink points to the original checkout.
const runtime = path.join(
  root,
  ".runtime",
  "cpython-3.13.16-linux-x86_64-gnu",
  "bin",
  "python3.13",
);
const python = fs.existsSync(venv) ? venv : runtime;
const env = { ...process.env };
if (python === runtime)
  env.PYTHONPATH = path.join(
    root,
    ".venv",
    "lib",
    "python3.13",
    "site-packages",
  );
if (python === runtime) env.JYOTI_EVAL_DIR = "/tmp/jyoti-accuracy-lab-evals";
const child = spawn(
  python,
  [
    "-m",
    "uvicorn",
    "app.main:app",
    "--host",
    option("--host", "127.0.0.1"),
    "--port",
    option("--port", "8000"),
  ],
  { cwd: root, stdio: "inherit", env },
);
child.on("error", (error) => {
  console.error(
    "Unable to start the lab. Run uv sync --dev first. " + error.message,
  );
  process.exitCode = 1;
});
child.on("exit", (code) => {
  process.exitCode = code ?? 1;
});
for (const signal of ["SIGTERM", "SIGINT"])
  process.on(signal, () => child.kill(signal));
