const fs = require("fs");
const path = require("path");
const { spawn } = require("child_process");

const root = __dirname;
const standalone = path.join(root, ".next", "standalone");

fs.mkdirSync(path.join(standalone, ".next"), { recursive: true });
fs.cpSync(path.join(root, ".next", "static"), path.join(standalone, ".next", "static"), {
  recursive: true,
  force: true,
});
fs.cpSync(path.join(root, "public"), path.join(standalone, "public"), {
  recursive: true,
  force: true,
});

const server = spawn(process.execPath, [path.join(standalone, "server.js")], {
  cwd: standalone,
  env: { ...process.env, HOSTNAME: process.env.HOSTNAME || "0.0.0.0" },
  stdio: "inherit",
});

function stop(signal) {
  if (!server.killed) server.kill(signal);
}

process.on("SIGINT", () => stop("SIGINT"));
process.on("SIGTERM", () => stop("SIGTERM"));
server.on("exit", (code, signal) => {
  process.exit(code ?? (signal ? 1 : 0));
});
