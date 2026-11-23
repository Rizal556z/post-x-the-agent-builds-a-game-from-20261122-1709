// SPDX-License-Identifier: MIT
// post-x-the-agent-builds-a-game-from-20261122-1709 — grade entry point.
//
// The bounty rules say this program copies POST.json from the repository
// to /output, and that is all it has to do. It also validates the file
// first, so a bad post address fails loudly instead of ranking nowhere:
//
//   POST.json  parses, is a JSON object of at most 16384 bytes, holds
//              exactly one key "url", and the url is an X post address
//              (x.com or twitter.com, /<handle>/status/<digits> or
//              /i/web/status/<digits>).
//
// The house reads the post itself from X and writes its counts to
// /output/post.counts.json after this program runs. This program writes
// nothing else and needs no network. Plain JavaScript in a .ts file, so
// plain `node` runs it with no build step and no dependencies.

import { existsSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = dirname(fileURLToPath(import.meta.url));
const OUT_DIR = "/output";
const failures = [];

function fail(name, detail) {
  console.error(`FAIL ${name}${detail ? ` — ${detail}` : ""}`);
  failures.push(name);
}

function ok(name, detail) {
  console.log(`ok   ${name}${detail ? ` — ${detail}` : ""}`);
}

const postPath = join(ROOT, "POST.json");
if (!existsSync(postPath)) {
  fail("POST.json present", "file missing — the post has not been named yet");
} else {
  const raw = readFileSync(postPath, "utf8");
  if (raw.length > 16384) {
    fail("POST.json size", `${raw.length} bytes, over the 16384 limit`);
  }
  let data = null;
  try {
    data = JSON.parse(raw);
  } catch (err) {
    fail("POST.json parses", String(err && err.message ? err.message : err));
  }
  if (data !== null) {
    const keys = Object.keys(data);
    if (keys.length !== 1 || keys[0] !== "url") {
      fail("POST.json has exactly one key", `keys: ${keys.join(",")}`);
    } else if (typeof data.url !== "string") {
      fail("POST.json url is a string", typeof data.url);
    } else {
      let u = null;
      try {
        u = new URL(data.url);
      } catch {
        u = null;
      }
      const hosts = new Set([
        "x.com", "www.x.com", "mobile.x.com",
        "twitter.com", "www.twitter.com", "mobile.twitter.com",
      ]);
      const pathOk = u !== null && hosts.has(u.hostname) &&
        (/^\/[^/]+\/status\/\d+\/?$/.test(u.pathname) ||
         /^\/i\/web\/status\/\d+\/?$/.test(u.pathname));
      if (u === null || u.protocol !== "https:" || !pathOk) {
        fail("POST.json url is an X post address", data.url);
      } else {
        ok("POST.json url is an X post address", data.url);
        mkdirSync(OUT_DIR, { recursive: true });
        writeFileSync(join(OUT_DIR, "POST.json"), raw, "utf8");
        ok("POST.json copied to /output", `${raw.length} bytes`);
      }
    }
  }
}

if (failures.length > 0) {
  console.error(`FAIL: ${failures.length} check(s) failed: ${failures.join(", ")}`);
  process.exit(1);
}
console.log("all checks passed: POST.json is valid and copied to /output");
