#!/usr/bin/env node

/**
 * Static export build script.
 *
 * Next.js output:"export" requires generateStaticParams() to return non-empty
 * arrays for dynamic routes. Since our [id] routes are SPA-only (behind Coming
 * Soon), we temporarily exclude them during static export by renaming page.tsx
 * files, then restore them after the build.
 */

const fs = require("fs");
const path = require("path");
const { execSync } = require("child_process");

const DYNAMIC_PAGES = [
  "src/app/campaigns/[id]/ad-serving/page.tsx",
  "src/app/campaigns/[id]/analytics/page.tsx",
  "src/app/campaigns/[id]/predictions/page.tsx",
  "src/app/campaigns/[id]/publish/page.tsx",
  "src/app/campaigns/[id]/variants/page.tsx",
  "src/app/repurpose/[id]/page.tsx",
];

const BACKUP_SUFFIX = "._export_bak";

function hidePages() {
  for (const p of DYNAMIC_PAGES) {
    const full = path.resolve(__dirname, "..", p);
    if (fs.existsSync(full)) {
      fs.renameSync(full, full + BACKUP_SUFFIX);
    }
  }
}

function restorePages() {
  for (const p of DYNAMIC_PAGES) {
    const full = path.resolve(__dirname, "..", p);
    const bak = full + BACKUP_SUFFIX;
    if (fs.existsSync(bak)) {
      fs.renameSync(bak, full);
    }
  }
}

if (process.env.BUILD_STANDALONE === "true") {
  console.log("Standalone build — skipping page exclusion");
  execSync("next build", { stdio: "inherit" });
  process.exit(0);
}

console.log("Static export — hiding dynamic route pages...");
hidePages();

try {
  execSync("next build", { stdio: "inherit" });
} finally {
  restorePages();
  console.log("Dynamic route pages restored.");
}
