// site/src/data/reports.json.js
// Runs at build time. Scans site/src/*.md for frontmatter, outputs sorted JSON.
import { readdirSync, readFileSync } from "node:fs";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const srcDir = join(dirname(fileURLToPath(import.meta.url)), "..");

const files = readdirSync(srcDir).filter(
  (f) => f.endsWith(".md") && f !== "index.md"
);

const reports = files
  .map((file) => {
    const content = readFileSync(join(srcDir, file), "utf8");
    const match = content.match(/^---\n([\s\S]*?)\n---/);
    if (!match) return null;
    const fm = Object.fromEntries(
      match[1]
        .split("\n")
        .map((line) => line.match(/^(\w+):\s*(.+)/))
        .filter(Boolean)
        .map(([, k, v]) => {
          const val = v.trim();
          // Parse YAML arrays like: [auction, interactive]
          if (val.startsWith("[") && val.endsWith("]")) {
            return [k, val.slice(1, -1).split(",").map((s) => s.trim())];
          }
          return [k, val];
        })
    );
    return { ...fm, path: "/" + file.replace(".md", "") };
  })
  .filter(Boolean)
  .sort((a, b) => new Date(b.date) - new Date(a.date));

process.stdout.write(JSON.stringify(reports));
